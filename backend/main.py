import os
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai  # Keep for now for stability, but let's fix the logic
from fuzzywuzzy import process
from googletrans import Translator

# 1. Setup & Config
load_dotenv()
app = FastAPI() 
translator = Translator()

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
    try:
        translated = translator.translate(text, dest=target_lang)
        return translated.text
    except Exception:
        return text

def match_medicine(detected_name):
    db = load_medicine_db()
    if not db: return None
    brand_list = [m['brand_name'] for m in db]
    best_match, score = process.extractOne(detected_name, brand_list)
    if score > 70:
        return next(item for item in db if item['brand_name'] == best_match)
    return None

# 3. API Routes
@app.get("/")
def root():
    db = load_medicine_db()
    return {"status": "online", "database_size": len(db)}

@app.post("/analyze")
async def analyze_prescription(file: UploadFile = File(...), lang: str = Query("en")):
    try:
        image_bytes = await file.read()
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
                    "purpose": translate_content(match_info["purpose"], lang),
                    "alternatives": match_info["alternatives"]
                }
                final_results.append({"detected_as": med, "status": "found", "data": processed_data})
            else:
                final_results.append({"detected_as": med, "status": "not_in_db"})

        return {"success": True, "language": lang, "results": final_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Corrected Execution for Windows
if __name__ == "__main__":
    import uvicorn
    # Do not use reload=True here if you are calling it from the terminal with --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)