# 💊 ClearScript: AI Prescription & Generic Finder

ClearScript bridges the gap between doctors and patients by using AI to translate complex, handwritten prescriptions into clear, actionable health instructions while saving patients money through generic medicine mapping.

---

## 🚀 The Problem
- **Handwriting Issues:** 50% of patients struggle to read doctor's handwriting, leading to dosage errors.
- **Medical Jargon:** Terms like "OD", "BD", and "TDS" are confusing for the average person.
- **Cost Barrier:** Patients often buy expensive branded drugs because they aren't aware of cheaper, identical generic alternatives.

## ✨ Features
- **Intelligent OCR:** Deciphers messy handwriting using Gemini Vision / OpenAI Vision.
- **Instruction Simplifier:** Converts medical shorthand into "Patient-First" language.
- **Generic Swap:** Suggests Jan Aushadhi and other generic alternatives with cost-saving percentages.
- **Mobile First:** Designed as a PWA for quick use at the pharmacy counter.

---

## 🛠 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Next.js 14, Tailwind CSS, Shadcn/UI |
| **Backend** | FastAPI (Python 3.11+) |
| **AI Layer** | Google Gemini 1.5 Flash (Vision + Pro) |
| **Data** | Custom JSON Dataset (Top 500 Indian Medicines) |
| **Deployment** | Vercel (Frontend), Railway (Backend) |

---

## 👥 Team: 
- **Nithyaanagha M** 
- **Adhithya Sriram**
- **Manasa M** 
- **Shreya K** 

---

## 🏗 Project Structure
```text
prescription-ai/
├── frontend/    # Next.js Application
├── backend/     # FastAPI Server
├── shared/      # API Types & Medicine Database
└── docs/        # Pitch Deck & Demo Videos
