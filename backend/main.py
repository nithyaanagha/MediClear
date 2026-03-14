import logging
logging.basicConfig(level=logging.DEBUG)
import os
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
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

_MEDICINE_DB = None

def get_medicine_db():
    global _MEDICINE_DB
    if _MEDICINE_DB is None:
        _MEDICINE_DB = load_medicine_db()
    return _MEDICINE_DB

def translate_content(text, target_lang):
    if not target_lang or target_lang == "en":
        return text
    return GoogleTranslator(source='auto', target=target_lang).translate(text)

def match_medicine(detected_name):
    db = get_medicine_db()
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
    db = get_medicine_db()
    return {"status": "online", "database_size": len(db)}

VISION_PROMPT = """
You are an expert Indian pharmacist and medical OCR system specialising in reading handwritten Indian prescriptions.

Your task: Extract ONLY medicine/drug names (with their strength if visible) from this prescription image.

Rules:
1. Look for lines that start with "Tab", "Cap", "Syr", "Inj", "Tab.", "Cap." — these mark a drug entry.
2. Include the strength/dosage number as part of the name (e.g. "Dolo 650", "Augmentin 625", "Pan 40", "Azithral 500").
3. Ignore everything that is NOT a medicine: patient name, doctor name, date, diagnosis, clinic name, dosage frequency (OD/BD/TDS), duration (x3 days), quantity, and instructions.
4. If the same medicine appears more than once, include it only once.
5. Handle common handwriting variations and OCR errors — include your best interpretation.
6. Common Indian brand names: Dolo, Augmentin, Pan, Combiflam, Azithral, Ciplox, Calpol, Zedex, Omnacortil, Cetirizine, Montair, Allegra, Pantop, Rantac, etc.

Output ONLY a valid JSON array of strings with absolutely no extra text, no markdown fences, no explanation:
["Brand Name 1", "Brand Name 2"]

If the image is illegible or no medicines are found, return exactly: []
"""

def build_image_part(image_bytes: bytes, content_type: str):
    mime_type = content_type if content_type and content_type.startswith("image/") else "image/jpeg"
    return {"mime_type": mime_type, "data": image_bytes}

def extract_medicines_from_detected(detected_medicines, lang):
    final_results = []
    for med in detected_medicines:
        match_info = match_medicine(med)
        if match_info:
            processed_data = {
                "brand_name": match_info["brand_name"],
                "brand_price": match_info.get("brand_price"),
                "generic_name": match_info["generic_name"],
                "purpose": translate_content(expand_abbreviations(match_info["purpose"]), lang),
                "alternatives": match_info["alternatives"]
            }
            final_results.append({"detected_as": med, "status": "found", "data": processed_data})
        else:
            final_results.append({"detected_as": med, "status": "not_in_db"})
    return final_results

@app.post("/analyze")
async def analyze_prescription(file: UploadFile = File(...), lang: str = Query("en")):
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content([
            VISION_PROMPT,
            build_image_part(image_bytes, mime_type)
        ])
        
        cleaned_text = re.sub(r'```json|```', '', response.text).strip()
        detected_medicines = json.loads(cleaned_text)
        final_results = extract_medicines_from_detected(detected_medicines, lang)

        return {"success": True, "language": lang, "results": final_results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class TextBody(BaseModel):
    text: str

@app.post("/analyze-text")
async def analyze_text_prescription(body: TextBody, lang: str = Query("en")):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
You are an expert Indian pharmacist extracting medicine names from prescription text.

Prescription text:
{body.text}

Extract ONLY medicine/drug brand names with their strength (e.g. "Dolo 650", "Augmentin 625").
Ignore dosage frequency, duration, patient details, and instructions.

Output ONLY a valid JSON array of strings with no extra text:
["Brand Name 1", "Brand Name 2"]

If no medicines are found, return exactly: []
"""
        response = model.generate_content(prompt)
        cleaned_text = re.sub(r'```json|```', '', response.text).strip()
        detected_medicines = json.loads(cleaned_text)
        final_results = extract_medicines_from_detected(detected_medicines, lang)

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
        dosage_note = expand_abbreviations(med.get('raw_text', 'as prescribed'))
        prompt = f"""
You are MediClear, a compassionate patient-education assistant helping Indian patients understand their prescriptions.

The patient has been prescribed the following medicine. Write simple, clear instructions that even a non-medical person can understand.

Medicine (Brand): {med['brand_name']}
Generic Name: {med['generic_name']}
Medical Purpose: {med['purpose']}
Prescription note: {dosage_note}

Generate ONLY a valid JSON object (no markdown, no extra text, no code fences) with these exact keys:
{{
  "purpose_simple": "One clear sentence explaining what this medicine does and why the doctor prescribed it",
  "how_to_take": ["When and how to take it (e.g. morning and night)", "Whether to take with food or on empty stomach", "How long to continue (if known from prescription note)"],
  "warnings": "One specific safety warning relevant to this medicine (e.g. avoid alcohol, don't crush tablet, watch for drowsiness)",
  "duration": "Duration extracted from the prescription note, or 'As prescribed by your doctor'"
}}

Write in simple English. Avoid medical jargon. Be specific to this medicine's actual use.
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