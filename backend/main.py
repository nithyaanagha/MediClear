import logging
logging.basicConfig(level=logging.DEBUG)
import os
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai  # Keep for now for stability, but let's fix the logic
from fuzzywuzzy import process
from deep_translator import GoogleTranslator

# 1. Setup & Config
load_dotenv()
app = FastAPI() 

# Enable CORS for Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GENAI_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=GENAI_KEY)

# 2. Helper Functions

def load_medicine_db():
    try:
        # 1. Get the absolute path to the backend folder (where main.py is)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Get the project root (MediClear) by going up one level
        project_root = os.path.dirname(backend_dir)
        
        # 3. Path to the shared folder and json file
        path = os.path.join(project_root, "shared", "medicine_data.json")
        
        # This will show you exactly where the code is looking in your terminal
        print(f"🔍 DEBUG: Attempting to load from: {path}")
        
        if not os.path.exists(path):
            print(f"❌ ERROR: File not found at: {path}")
            return []

        with open(path, "r") as f:
            print (f)
            content = f.read()
            #Parsing content
            data = json.loads(content)
            # This confirms the "Medicine Database" phase of your workflow
            print(f"✅ SUCCESS: Loaded {len(data)} medicines.")
            return data
            
    except Exception as e:
        print(f"❌ ERROR: Could not load JSON: {e}")
        return []

def translate_content(text, target_lang):
    if not target_lang or target_lang == "en":
        return text
    return GoogleTranslator(source='auto', target=target_lang).translate(text)

def match_medicine(detected_name):
    db = load_medicine_db()
    if not db: return None
    brand_list = [m['brand_name'] for m in db]
    best_match, score = process.extractOne(detected_name, brand_list)
    if score > 70:
        return next(item for item in db if item['brand_name'] == best_match)
    return None

ABBREV_MAP = {
    "OD": "once daily", "BD": "twice daily", "TDS": "three times a day",
    "QID": "four times a day", "HS": "at bedtime", "SOS": "when needed",
    "STAT": "immediately", "AC": "before meals", "PC": "after meals",
    "Tab": "Tablet", "Cap": "Capsule", "Syr": "Syrup", "Inj": "Injection"
}

def expand_abbreviations(text: str) -> str:
    for abbr, full in ABBREV_MAP.items():
        text = re.sub(rf'\b{abbr}\b', full, text, flags=re.IGNORECASE)
    return text

# 3. API Routes
@app.get("/")
def root():
    db = load_medicine_db()
    return {"status": "online", "database_size": len(db)}

@app.post("/analyze")
async def analyze_prescription(file: UploadFile = File(...), lang: str = Query("en")):
    try:
        image_bytes = await file.read()
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Extract medicine brand names and strengths (e.g., 'Dolo 650') from this image.
        Format as a JSON array of strings: ["Name 1", "Name 2"].
        If illegible, return []. 
        """
        
        response = model.generate_content([
            prompt, 
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        cleaned_text = re.sub(r'```json|```', '', response.text).strip()
        detected_medicines = json.loads(cleaned_text)
        
        final_results = []
        for med in detected_medicines:
            match_info = match_medicine(med)
            if match_info:
                processed_data = {
                    "brand_name": match_info["brand_name"],
                    "generic_name": match_info["generic_name"],
                    "purpose": translate_content(expand_abbreviations(match_info["purpose"]), lang),
                    "alternatives": match_info["alternatives"]
                }
                final_results.append({"detected_as": med, "status": "found", "data": processed_data})
            else:
                final_results.append({"detected_as": med, "status": "not_in_db"})

        return {"success": True, "language": lang, "results": final_results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/simplify")
async def simplify_medicines(body: dict, lang: str = Query("en")):
    medicines = body.get("medicines", [])
    results = []
    for med in medicines:
        prompt = f"""
You are a patient-friendly medical assistant.
Given this medicine info, generate simple patient instructions.

Medicine: {med['brand_name']}
Generic: {med['generic_name']}
Purpose: {med['purpose']}
Dosage info from prescription: {expand_abbreviations(med.get('raw_text', ''))}

Output ONLY a JSON object with these keys:
- purpose_simple: one sentence in plain language
- how_to_take: list of 2-3 bullet points
- warnings: one important note
- duration: if mentioned, else "as prescribed"
"""
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        cleaned = re.sub(r'```json|```', '', response.text).strip()
        instructions = json.loads(cleaned)
        instructions['brand_name'] = med['brand_name']
        instructions['translated'] = translate_content(
            instructions['purpose_simple'], lang
        )
        results.append(instructions)
    return {"success": True, "instructions": results}

# 4. Corrected Execution for Windows
if __name__ == "__main__":
    import uvicorn
    # Do not use reload=True here if you are calling it from the terminal with --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)