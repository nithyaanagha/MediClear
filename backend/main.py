import os
import json
import traceback
import tempfile
from typing import Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fuzzywuzzy import process
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from groq import Groq
from doctr.models import ocr_predictor
from doctr.io import DocumentFile

# ==================================================
# Setup
# ==================================================

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize docTR OCR
print("Loading docTR OCR model... (first startup may take a minute)")
ocr_model = ocr_predictor(pretrained=True)
print("docTR OCR loaded successfully.")

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

print("Backend initialized with docTR + Groq LLaMA for prescription analysis")


class TranslateRequest(BaseModel):
    text: str
    lang: str


class SimplifyRequest(BaseModel):
    medicines: list[dict[str, Any]]

# ==================================================
# Database Loader
# ==================================================

def load_medicine_db():
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(backend_dir)

        db_path = os.path.join(
            project_root,
            "shared",
            "medicine_data.json"
        )

        print(f"Loading medicine DB from: {db_path}")

        if not os.path.exists(db_path):
            print("medicine_data.json not found")
            return []

        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Loaded {len(data)} medicines")
        return data

    except Exception as e:
        print(f"Database load error: {e}")
        return []


# ==================================================
# Translation
# ==================================================

def translate_content(text, target_lang):
    if not target_lang or target_lang == "en":
        return text


def expand_frequency(value: str | None) -> str | None:
    if not value:
        return value

    normalized = value.strip()
    replacements = {
        "OD": "once daily",
        "BD": "twice daily",
        "BID": "twice daily",
        "TDS": "three times daily",
        "TID": "three times daily",
        "QID": "four times daily",
        "HS": "at bedtime",
        "SOS": "as needed",
        "PRN": "as needed",
        "AC": "before food",
        "PC": "after food",
    }

    upper = normalized.upper().replace(".", "")
    return replacements.get(upper, normalized)


def build_patient_instructions(medicine: dict[str, Any], match_info: dict[str, Any] | None, lang: str) -> dict[str, Any]:
    detected_name = medicine.get("detected_name", "").strip()
    frequency = expand_frequency(medicine.get("frequency"))
    dosage = medicine.get("dosage") or "as prescribed"
    duration = medicine.get("duration") or "as prescribed"
    meals = medicine.get("meals")
    special = medicine.get("special_instructions")

    how_to_take = []
    if dosage or frequency:
        instruction = f"Take {dosage}"
        if frequency:
            instruction += f", {frequency}"
        how_to_take.append(instruction)
    if meals:
        how_to_take.append(f"Take {meals}.")
    if duration and duration != "as prescribed":
        how_to_take.append(f"Continue for {duration}.")
    if special:
        how_to_take.append(special)

    purpose = match_info.get("purpose", "") if match_info else ""
    purpose_simple = translate_content(purpose or "Please verify this medicine with a pharmacist.", lang)

    return {
        "brand_name": match_info.get("brand_name") if match_info else detected_name,
        "generic_name": match_info.get("generic_name") if match_info else None,
        "brand_price": match_info.get("brand_price") if match_info else None,
        "purpose_simple": purpose_simple,
        "how_to_take": how_to_take,
        "duration": duration,
        "warnings": "Verify the medicine name, dose, and duration with your doctor or pharmacist before taking it.",
        "alternatives": match_info.get("alternatives", []) if match_info else [],
        "raw_text": detected_name,
        "confidence": medicine.get("confidence"),
    }

    try:
        return GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(text)

    except Exception:
        return text


# ==================================================
# Medicine Matching
# ==================================================

def match_medicine(detected_name):
    db = load_medicine_db()

    if not db:
        return None

    brand_names = [
        med["brand_name"]
        for med in db
    ]

    result = process.extractOne(
        detected_name,
        brand_names
    )

    if not result:
        return None

    best_match, score = result

    print(f"Matching '{detected_name}' -> '{best_match}' ({score})")

    if score < 70:
        return None

    for med in db:
        if med["brand_name"] == best_match:
            return med

    return None


# ==================================================
# OCR with docTR
# ==================================================

def extract_text_from_image(image_path: str) -> list:
    """Extract text from prescription image using docTR."""
    try:
        # Load image with docTR
        doc = DocumentFile.from_images(image_path)
        
        # Run OCR
        result = ocr_model(doc)
        
        extracted_text = []
        
        # Extract text from all pages and blocks
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        text = word.value
                        confidence = word.confidence
                        
                        if confidence > 0.3:
                            extracted_text.append(text)
        
        return extracted_text
    
    except Exception as e:
        print(f"OCR Error: {e}")
        traceback.print_exc()
        return []


# ==================================================
# Prescription Analysis with Groq LLaMA
# ==================================================

def analyze_prescription_with_groq(ocr_text: list) -> dict:
    """
    Use Groq's LLaMA 3.1 model to analyze extracted prescription text.
    Parses medicine information, dosages, frequencies, and duration.
    """
    try:
        if not groq_client:
            return {
                "status": "error",
                "message": "GROQ_API_KEY is not configured"
            }

        # Join OCR text into readable prescription text
        prescription_text = " ".join(ocr_text)
        
        if not prescription_text.strip():
            return {
                "status": "error",
                "message": "No readable text found in prescription"
            }
        
        # Detailed prompt for LLaMA to analyze prescription
        prompt = f"""Analyze this prescription text and extract medication information in JSON format.

Prescription text: "{prescription_text}"

Extract and return ONLY a valid JSON object with this exact structure (no markdown, no code blocks):
{{
  "medicines": [
    {{
      "detected_name": "the medicine name as written",
      "dosage": "e.g., 500mg, 10ml, 1 tablet",
      "frequency": "e.g., once daily (OD), twice daily (BD), thrice daily (TDS), every 6 hours, etc.",
      "duration": "e.g., 5 days, 1 week, 10 days, as needed",
      "meals": "with/without/before/after food",
      "special_instructions": "any special notes",
      "confidence": "high, medium, or low"
    }}
  ],
  "doctor_name": "if visible, otherwise null",
  "date": "prescription date if visible, otherwise null",
  "patient_name": "if visible, otherwise null"
}}

IMPORTANT:
- Be conservative: only include medicines you're confident about
- Expand abbreviations: OD=once daily, BD=twice daily, TDS=thrice daily, HS=at bedtime, SOS=as needed
- If handwriting is unclear, set confidence to low and preserve the uncertain text in detected_name
- Return valid JSON only, no explanations"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=1024
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response if it contains markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        analysis = json.loads(response_text)
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON Parsing Error: {e}")
        print(f"Response was: {response_text if 'response_text' in locals() else 'N/A'}")
        return {
            "status": "error",
            "message": "Failed to parse prescription analysis"
        }
    except Exception as e:
        print(f"Groq Analysis Error: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }


def analyze_manual_text(text: str) -> list[str]:
    return [token.strip() for token in text.replace("\n", " ").split(" ") if token.strip()]


# ==================================================
# Routes
# ==================================================

@app.get("/")
def root():
    db = load_medicine_db()

    return {
        "status": "online",
        "ocr": "docTR",
        "ai_analysis": "Groq (LLaMA 3.1 8B Instant)",
        "database_size": len(db)
    }


@app.post("/analyze")
async def analyze_prescription(
    file: UploadFile = File(...),
    lang: str = Query("en")
):
    """
    Analyze prescription image:
    1. Extract text using docTR
    2. Parse medical information using Groq LLaMA 3.1 8B Instant
    3. Match medicines to database
    4. Provide alternatives and translations
    """
    temp_path = None
    try:
        # Save uploaded file temporarily
        image_bytes = await file.read()
        content_type = file.content_type or ""
        filename = file.filename or ""

        if content_type.startswith("text/") or filename.lower().endswith(".txt"):
            detected_text = analyze_manual_text(image_bytes.decode("utf-8", errors="ignore"))
        else:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".jpg"
            ) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            # Step 1: OCR with docTR
            print("Extracting text with docTR...")
            detected_text = extract_text_from_image(temp_path)
        
        if not detected_text:
            return {
                "success": False,
                "error": "Could not extract text from image. Please ensure it's a clear prescription."
            }

        print(f"OCR Results: {detected_text}")

        # Step 2: Analyze with Groq
        print("Analyzing prescription with Groq...")
        analysis_result = analyze_prescription_with_groq(detected_text)
        
        if analysis_result["status"] != "success":
            return {
                "success": False,
                "error": analysis_result.get("message", "Failed to analyze prescription")
            }
        
        prescription_data = analysis_result["analysis"]
        
        # Step 3: Match medicines to database and build results
        final_results = []
        db = load_medicine_db()
        
        for medicine in prescription_data.get("medicines", []):
            detected_name = medicine.get("detected_name", "")
            
            # Try to find in database
            match_info = match_medicine(detected_name)
            
            medicine_entry = {
                "detected_as": detected_name,
                "dosage": medicine.get("dosage"),
                "frequency": expand_frequency(medicine.get("frequency")),
                "duration": medicine.get("duration"),
                "meals": medicine.get("meals"),
                "special_instructions": medicine.get("special_instructions"),
                "confidence": medicine.get("confidence")
            }
            
            if match_info:
                medicine_entry["status"] = "found"
                medicine_entry["data"] = {
                    "brand_name": match_info.get("brand_name"),
                    "generic_name": match_info.get("generic_name"),
                    "purpose": translate_content(
                        match_info.get("purpose", ""),
                        lang
                    ),
                    "alternatives": match_info.get("alternatives", [])
                }
            else:
                medicine_entry["status"] = "not_in_db"
                medicine_entry["note"] = "Not found in database - please verify with pharmacist"
            
            final_results.append(medicine_entry)

        patient_results = [
            build_patient_instructions(
                medicine,
                match_medicine(medicine.get("detected_name", "")),
                lang
            )
            for medicine in prescription_data.get("medicines", [])
        ]

        return {
            "success": True,
            "language": lang,
            "ocr_text": " ".join(detected_text),
            "prescription_info": {
                "doctor": prescription_data.get("doctor_name"),
                "date": prescription_data.get("date"),
                "patient": prescription_data.get("patient_name")
            },
            "medicines": final_results,
            "results": patient_results
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
    finally:
        # Clean up temp file
        if temp_path:
            try:
                os.remove(temp_path)
            except:
                pass


@app.post("/translate")
def translate_text(payload: TranslateRequest):
    return {
        "translated": translate_content(payload.text, payload.lang)
    }


@app.post("/simplify")
def simplify_medicines(payload: SimplifyRequest, lang: str = Query("en")):
    instructions = [
        {
            "brand_name": medicine.get("brand_name") or medicine.get("raw_text"),
            "generic_name": medicine.get("generic_name"),
            "brand_price": medicine.get("brand_price"),
            "purpose_simple": translate_content(medicine.get("purpose", ""), lang),
            "how_to_take": medicine.get("how_to_take") or [
                "Follow the dose and timing written on the prescription."
            ],
            "duration": medicine.get("duration") or "as prescribed",
            "warnings": "Verify with your doctor or pharmacist before changing medicines.",
            "alternatives": medicine.get("alternatives", []),
            "raw_text": medicine.get("raw_text"),
        }
        for medicine in payload.medicines
    ]

    return {"instructions": instructions}


# ==================================================
# Run
# ==================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
