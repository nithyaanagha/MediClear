# MediClear: AI Prescription & Generic Finder

MediClear helps patients understand handwritten prescriptions by combining OCR, an LLM prescription parser, and a local Indian medicine database for generic alternatives.

## The Problem

- **Handwriting issues:** Patients often struggle to read doctor's handwriting, which can lead to dosage mistakes.
- **Medical jargon:** Terms like `OD`, `BD`, `TDS`, `HS`, and `SOS` are difficult for non-medical users.
- **Cost barrier:** Patients often buy expensive branded medicines because they do not know equivalent generic alternatives.

## Features

- **Prescription upload:** Upload or capture a prescription image from the browser.
- **Local OCR:** Reads prescription images with docTR OCR instead of Gemini Vision.
- **LLM interpretation:** Uses Groq-hosted LLaMA to extract medicine name, dosage, frequency, duration, meal timing, and notes.
- **Instruction simplifier:** Expands shorthand like `BD` into patient-friendly instructions.
- **Generic swap:** Matches medicines against `shared/medicine_data.json` and shows cheaper alternatives.
- **Manual fallback:** Users can type prescription text if image OCR is unclear.
- **Regional language support:** Uses `deep-translator` for translated purpose/instruction text.
- **Voice readout:** Browser text-to-speech reads instructions from medicine cards.

## Updated Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion |
| Backend | FastAPI, Python |
| OCR | docTR (`python-doctr[torch]`) |
| LLM Parser | Groq API with `llama-3.1-8b-instant` |
| Medicine Matching | `fuzzywuzzy` + `python-Levenshtein` |
| Translation | `deep-translator` |
| Data | Local JSON database at `shared/medicine_data.json` |
| Dev Runner | Root `npm run dev` with `concurrently` |

## Project Structure

```text
MediClear/
|-- backend/
|   |-- main.py
|   |-- requirements.txt
|   |-- test_models.py
|   `-- .env
|-- frontend/
|   |-- app/
|   |-- components/
|   |-- lib/
|   `-- package.json
|-- shared/
|   `-- medicine_data.json
|-- package.json
`-- README.md
```

## Environment

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

OCR runs locally through docTR, so there is no OCR API key.

## Run Locally

From the project root:

```powershell
cd C:\Projects\projectsbio\MediClear\MediClear\MediClear
npm run dev
```

Then open:

- Frontend: http://localhost:3000
- Backend health check: http://localhost:8000

If the backend virtual environment is broken or points to a missing Python install:

```powershell
cd C:\Projects\projectsbio\MediClear\MediClear\MediClear\backend
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
cd ..
npm run dev
```

## API Endpoints

### `GET /`

Health check. Returns OCR engine, LLM provider, and medicine database size.

### `POST /analyze`

Analyzes an uploaded prescription image or text file.

Request:

```text
multipart/form-data
file: image or .txt file
lang: optional query parameter, default "en"
```

Response includes:

- `ocr_text`: raw extracted OCR text
- `prescription_info`: doctor, patient, and date if visible
- `medicines`: raw matched medicine details
- `results`: patient-ready medicine cards for the frontend

### `POST /translate`

Translates text for voice/instruction display.

### `POST /simplify`

Compatibility endpoint for older frontend calls. The current flow gets patient-ready results directly from `/analyze`.

## Safety Note

MediClear is informational only. OCR and handwriting recognition can be uncertain, especially for handwritten medicine names. Users should verify medicine names, dosage, and duration with a doctor or pharmacist before taking or switching medicines.
