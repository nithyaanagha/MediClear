# MediClear — Project Context & PRD
> HEAL-A-THON 2026 | Centre for Healthcare Engineering and Learning | 10-Hour State Level Healthcare Hackathon

---

## 1. The Problem

Patients across India face three compounding problems every time they receive a prescription:

1. **Illegible handwriting** — Doctors' handwriting is notoriously difficult to read. 50% of patients struggle to decipher it, leading to dosage errors and wrong medicine purchases.
2. **Medical jargon** — Abbreviations like `OD`, `BD`, `TDS`, `HS`, `SOS` are standard for doctors but completely opaque to patients. A missed `BD` means a patient takes one dose instead of two.
3. **Cost blindness** — Branded medicines cost 3–5x more than identical generic alternatives. Patients pay the premium simply because they don't know cheaper options exist.

Combined, these issues lead to:
- Medication errors and missed doses
- Antibiotic resistance from incomplete courses
- Unnecessary healthcare expenditure (₹500–2000 per prescription)
- Disproportionate impact on elderly, rural, and non-English-speaking populations

---

## 2. The Solution — MediClear

MediClear is an AI-powered prescription scanner and generic medicine finder.

A patient uploads a photo of their prescription. MediClear:
1. Reads it (OCR via Gemini Vision)
2. Parses the medical shorthand into plain language
3. Explains each medicine — what it's for, how and when to take it
4. Shows cheaper generic alternatives with savings in rupees and percentage

No doctor visit. No pharmacist dependence. Works at the pharmacy counter in under 30 seconds.

---

## 3. Target Users

| User | Pain Point | MediClear Value |
|------|-----------|-----------------|
| **Patients** | Can't read/understand prescription | Simple step-by-step instructions |
| **Elderly patients** | Poor eyesight, low literacy | Voice + regional language output |
| **Caregivers** | Managing someone else's meds | Clear instructions per medicine |
| **Low-income patients** | Paying branded prices unknowingly | Instant generic alternatives with savings % |
| **Pharmacists** | Repeated patient queries | Patients arrive already informed |

---

## 4. Product Scope (Hackathon MVP)

### ✅ In Scope (Must Ship)
- Upload prescription image (camera or file)
- Manual text input fallback
- OCR extraction via Gemini Vision API
- Medical abbreviation expansion (OD → once daily, BD → twice daily, etc.)
- Per-medicine cards: name, purpose, how to take, duration
- Generic alternatives table: name, price, savings vs brand
- Language translation (English + Hindi minimum via Google Translate)

### 🔜 Stretch (If Time Permits)
- Voice readout of instructions (browser TTS)
- Drug interaction warnings
- Medication reminder schedule
- Pharmacy stock nearby suggestions

### ❌ Out of Scope
- User accounts / login
- Prescription history storage
- Real-time pharmacy API integration
- Medical diagnosis or dosage recommendations

---

## 5. Team

| Name | Degree | Role |
|------|--------|------|
| **S S Adhithya Sriram** | BTech CSE, Sem 4 | Architecture, backend integration, lead coder |
| **Nithyaanagha M** | BTech Biotech, Sem 4 | Python backend, FastAPI, medicine database |
| **Shreya K** | BTech Biotech, Sem 4 | Frontend (Next.js), UI/UX, component design |
| **Manasa M** | BTech Biotech, Sem 4 | Data, testing, pitch deck, demo script |

---

## 6. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| **Frontend** | Next.js 14, Tailwind CSS, shadcn/ui | Fast setup, mobile-first, component library |
| **Backend** | FastAPI (Python 3.11) | Nithya knows Python; easy Gemini integration |
| **OCR / AI** | Google Gemini 1.5 Flash (Vision) | Free tier, best handwriting accuracy |
| **AI Simplification** | Gemini 1.5 Flash (text prompt) | Same API key, structured JSON output |
| **Medicine Database** | Custom JSON (100 Indian medicines) | No external dependency, fast fuzzy match |
| **Fuzzy Search** | fuzzywuzzy + python-levenshtein | Handles OCR typos, brand name variants |
| **Translation** | deep-translator (Google Translate) | Replaces broken googletrans library |
| **Frontend Deploy** | Vercel | Free, instant deploy from GitHub |
| **Backend Deploy** | Railway | Free tier, FastAPI-friendly |

---

## 7. Repository Structure

```
nithyaanagha-mediclear/
├── backend/
│   ├── main.py                  ← FastAPI app (3 endpoints)
│   ├── requirements.txt         ← Pinned dependencies
│   └── .env.example             ← GEMINI_API_KEY=your_key_here
├── frontend/
│   ├── app/
│   │   ├── page.tsx             ← Upload screen (Step 1)
│   │   ├── results/
│   │   │   └── page.tsx         ← Results screen (Steps 2–4)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── UploadZone.tsx       ← Drag-drop + camera input
│   │   ├── MedicineCard.tsx     ← Per-medicine info card
│   │   ├── AlternativesTable.tsx← Cheaper options table
│   │   └── LoadingSteps.tsx     ← Animated progress steps
│   ├── lib/
│   │   └── api.ts               ← Backend API calls
│   ├── package.json
│   └── next.config.js
├── shared/
│   └── medicine_data.json       ← 100 Indian medicines with prices + alternatives
└── README.md
```

---

## 8. API Endpoints

### `GET /`
Health check. Returns database size.
```json
{ "status": "online", "database_size": 100 }
```

### `POST /analyze`
Accepts a prescription image. Returns detected medicines matched against the database.

**Request:** `multipart/form-data` with `file` (image) + optional `lang` query param (default `"en"`)

**Response:**
```json
{
  "success": true,
  "language": "en",
  "results": [
    {
      "detected_as": "Dolo 650",
      "status": "found",
      "data": {
        "brand_name": "Dolo 650",
        "brand_price": 30,
        "generic_name": "Paracetamol",
        "purpose": "Fever and Pain",
        "alternatives": [
          { "name": "Paracip 650", "price": 15 },
          { "name": "Crocin 650", "price": 18 }
        ]
      }
    }
  ]
}
```

### `POST /simplify`
Takes matched medicine data, returns AI-generated patient-friendly instructions.

**Request Body:**
```json
{
  "medicines": [
    {
      "brand_name": "Dolo 650",
      "generic_name": "Paracetamol",
      "purpose": "Fever and Pain",
      "raw_text": "Tab Dolo 650 BD x3 days"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "instructions": [
    {
      "brand_name": "Dolo 650",
      "purpose_simple": "Reduces fever and relieves body pain",
      "how_to_take": [
        "Take 1 tablet after food",
        "Take morning and night",
        "Continue for 3 days"
      ],
      "warnings": "Do not take more than 2 tablets in 12 hours",
      "duration": "3 days"
    }
  ]
}
```

### `GET /medicines/search?q=dolo`
Simple text search across medicine_data.json. Used for manual input fallback.

---

## 9. Medicine Database Schema

Each entry in `shared/medicine_data.json`:
```json
{
  "brand_name": "Augmentin 625",
  "brand_price": 210,
  "generic_name": "Amoxicillin + Clavulanic Acid",
  "purpose": "Bacterial infections",
  "alternatives": [
    { "name": "Amoxyclav 625", "price": 95 },
    { "name": "Moxikind-CV", "price": 105 }
  ]
}
```

Source: Jan Aushadhi price data + common Indian pharmacy prices. 100 entries covering antibiotics, antacids, painkillers, antihypertensives, antidiabetics, vitamins, and more.

---

## 10. Medical Abbreviations Map

```
OD   → once daily
BD   → twice daily
TDS  → three times a day
QID  → four times a day
HS   → at bedtime
SOS  → when needed / as required
STAT → immediately
AC   → before meals
PC   → after meals
Tab  → Tablet
Cap  → Capsule
Syr  → Syrup
Inj  → Injection
```

---

## 11. User Flow

```
[Upload Screen]
  User uploads prescription image OR types text manually
        ↓
[Processing Steps — Animated]
  Step 1: Uploading image...
  Step 2: Reading prescription...
  Step 3: Finding medicines...
  Step 4: Generating instructions...
        ↓
[Results Screen]
  ┌─────────────────────────────┐
  │ 💊 Dolo 650                 │
  │ Paracetamol                 │
  │ Reduces fever & body pain   │
  │ • Take 1 tablet after food  │
  │ • Morning and night         │
  │ • For 3 days                │
  │ ⚠️ Max 2 tablets / 12 hrs   │
  ├─────────────────────────────┤
  │ 💰 SAVE MONEY               │
  │ Brand price: ₹30            │
  │ Paracip 650     ₹15  50% off│
  │ Crocin 650      ₹18  40% off│
  └─────────────────────────────┘
```

---

## 12. Fallback Strategy (Demo Safety)

| Risk | Fallback |
|------|----------|
| OCR fails / low confidence | User can edit extracted text before processing |
| Medicine not in database | Show Gemini's explanation only, skip alternatives |
| Gemini API rate limit | Display cached demo results for 3 test prescriptions |
| Internet down | Pre-loaded results for Augmentin + Dolo + Pantop demo |

**Always have 3 pre-loaded demo prescriptions ready to show judges.**

---

## 13. Proof Points for Judges

| Judge Question | Proof |
|---------------|-------|
| "What if handwriting is too messy?" | Show manual text input fallback live |
| "Is the medicine data real?" | Show medicine_data.json, cite Jan Aushadhi source |
| "How does generic matching work?" | Walk through fuzzywuzzy brand match → composition → alternatives |
| "Can it handle regional languages?" | Show Hindi output from deep-translator |
| "How does it scale?" | Stateless API + Railway deployment = handles 100 concurrent users |

---

## 14. Pitch Narrative

> "Every day, millions of Indians walk out of clinics clutching a piece of paper they can't read, written in shorthand they don't understand, for medicines they could buy for half the price.
>
> MediClear solves all three problems in 30 seconds — take a photo, get clear instructions, save money.
>
> This isn't just an app. It's a bridge between what the doctor wrote and what the patient actually does."

**Impact numbers:**
- 300M+ Indians receive prescriptions annually
- ₹500–2000 average savings per prescription on generics
- ₹20B annual savings potential at 10M users
- Same model replicable for Southeast Asia, Africa

---

## 15. Environment Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your Gemini API key to .env
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Get free Gemini API key: https://aistudio.google.com
