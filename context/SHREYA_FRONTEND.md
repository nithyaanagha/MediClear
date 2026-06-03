# Shreya's Frontend Build Doc — MediClear
> Attach this file to your AI coder (Cursor / Windsurf / Claude). Tell it: "Read this document and execute it step by step."

---

## Your Job

Build the **entire frontend** for MediClear using Next.js 14.

- You are building a **mobile-first web app** (most users will use it on their phones at the pharmacy)
- The backend is already running at `http://localhost:8000` (Nithya's FastAPI)
- Your job: beautiful UI that calls the backend, shows results cleanly
- Stack: **Next.js 14 + Tailwind CSS + shadcn/ui**
- Design vibe: Clean, white, medical but friendly. Sky blue (#0EA5E9) as primary color. Green for savings. No clutter.

---

## Step 0 — Setup

Run these commands in the `frontend/` folder:

```bash
npm install
npx shadcn-ui@latest init
# Choose: Default style, Zinc base color, yes CSS variables
npx shadcn-ui@latest add card button badge textarea separator
npm install react-dropzone framer-motion lucide-react
```

Create a file `frontend/lib/api.ts`:
```typescript
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function analyzePrescription(file: File, lang: string = "en") {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_URL}/analyze?lang=${lang}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
}

export async function simplifyMedicines(medicines: any[], lang: string = "en") {
  const res = await fetch(`${BACKEND_URL}/simplify?lang=${lang}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ medicines }),
  });
  if (!res.ok) throw new Error("Simplification failed");
  return res.json();
}

export async function searchMedicines(query: string) {
  const res = await fetch(`${BACKEND_URL}/medicines/search?q=${query}`);
  return res.json();
}
```

---

## Step 1 — Root Layout (`app/layout.tsx`)

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MediClear — Understand Your Prescription",
  description: "AI-powered prescription scanner and generic medicine finder",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
```

---

## Step 2 — Upload Screen (`app/page.tsx`)

This is the **first thing users see**. It should feel premium and simple.

**What it needs:**
- MediClear logo + tagline at the top
- Drag-and-drop image upload box (large, centered)
- Camera capture button (for mobile)
- "Or type prescription text" toggle below the upload box
- Language selector dropdown (English, Hindi, Tamil, Telugu, Kannada)
- Animated "Analyse Prescription" button
- Loading state with step-by-step progress animation

**Full component (`app/page.tsx`):**

```typescript
"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Camera, FileText, Loader2, Pill } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { analyzePrescription, simplifyMedicines } from "@/lib/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "ta", label: "Tamil" },
  { code: "te", label: "Telugu" },
  { code: "kn", label: "Kannada" },
];

const STEPS = [
  "Uploading image...",
  "Reading prescription...",
  "Matching medicines...",
  "Generating instructions...",
];

export default function HomePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [showTextInput, setShowTextInput] = useState(false);
  const [manualText, setManualText] = useState("");
  const [lang, setLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const f = acceptedFiles[0];
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    multiple: false,
  });

  const handleAnalyze = async () => {
    if (!file && !manualText.trim()) {
      setError("Please upload a prescription image or enter text.");
      return;
    }
    setLoading(true);
    setCurrentStep(0);
    setError(null);

    try {
      // Simulate step progression
      const stepInterval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev < STEPS.length - 1) return prev + 1;
          clearInterval(stepInterval);
          return prev;
        });
      }, 900);

      let analyzeResult;
      if (file) {
        analyzeResult = await analyzePrescription(file, lang);
      } else {
        // Manual text: create a text blob and send
        const textBlob = new Blob([manualText], { type: "text/plain" });
        const textFile = new File([textBlob], "prescription.txt", { type: "text/plain" });
        analyzeResult = await analyzePrescription(textFile, lang);
      }

      clearInterval(stepInterval);
      setCurrentStep(STEPS.length - 1);

      const foundMeds = analyzeResult.results.filter((r: any) => r.status === "found");
      const medicinesForSimplify = foundMeds.map((r: any) => ({
        brand_name: r.data.brand_name,
        brand_price: r.data.brand_price,
        generic_name: r.data.generic_name,
        purpose: r.data.purpose,
        alternatives: r.data.alternatives,
        raw_text: r.detected_as,
      }));

      const simplifyResult = await simplifyMedicines(medicinesForSimplify, lang);

      // Merge results
      const finalData = simplifyResult.instructions.map((inst: any, i: number) => ({
        ...inst,
        brand_price: medicinesForSimplify[i]?.brand_price,
        alternatives: medicinesForSimplify[i]?.alternatives,
      }));

      // Store in sessionStorage and navigate
      sessionStorage.setItem("mediclear_results", JSON.stringify(finalData));
      router.push("/results");
    } catch (err) {
      setError("Something went wrong. Please try again or use text input.");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <div className="flex items-center justify-center gap-2 mb-2">
          <Pill className="w-8 h-8 text-sky-500" />
          <h1 className="text-3xl font-bold text-gray-900">MediClear</h1>
        </div>
        <p className="text-gray-500 text-sm max-w-xs mx-auto">
          Upload your prescription. Get clear instructions and save money with generics.
        </p>
      </motion.div>

      {/* Main Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="w-full max-w-md bg-white rounded-3xl shadow-lg p-6 space-y-4"
      >
        {/* Upload Zone */}
        {!showTextInput && (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200
              ${isDragActive ? "border-sky-400 bg-sky-50" : "border-gray-200 hover:border-sky-300 hover:bg-sky-50/50"}
              ${preview ? "border-sky-400 bg-sky-50" : ""}`}
          >
            <input {...getInputProps()} />
            {preview ? (
              <div>
                <img src={preview} alt="prescription" className="max-h-40 mx-auto rounded-xl object-contain mb-2" />
                <p className="text-xs text-sky-600 font-medium">Image ready ✓ — drop another to replace</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-14 h-14 bg-sky-100 rounded-2xl flex items-center justify-center mx-auto">
                  <Upload className="w-6 h-6 text-sky-500" />
                </div>
                <p className="text-gray-700 font-medium">Drop prescription here</p>
                <p className="text-gray-400 text-sm">or click to choose file</p>
                <div className="flex items-center justify-center gap-2">
                  <Camera className="w-4 h-4 text-gray-400" />
                  <span className="text-xs text-gray-400">Camera supported on mobile</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Toggle text input */}
        <button
          onClick={() => setShowTextInput(!showTextInput)}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-sky-500 transition-colors mx-auto"
        >
          <FileText className="w-4 h-4" />
          {showTextInput ? "Upload image instead" : "Type prescription text instead"}
        </button>

        {/* Manual text input */}
        <AnimatePresence>
          {showTextInput && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <Textarea
                placeholder={"Tab Augmentin 625 BD x5 days\nTab Pantop 40 OD"}
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                className="min-h-[100px] text-sm font-mono rounded-2xl resize-none"
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Language Selector */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-400 shrink-0">Language:</span>
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => setLang(l.code)}
              className={`text-xs px-3 py-1 rounded-full border transition-all
                ${lang === l.code
                  ? "bg-sky-500 text-white border-sky-500"
                  : "border-gray-200 text-gray-500 hover:border-sky-300"}`}
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        {/* Loading Steps */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-2"
            >
              {STEPS.map((step, i) => (
                <motion.div
                  key={step}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: i <= currentStep ? 1 : 0.3, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-2 text-sm"
                >
                  {i < currentStep ? (
                    <span className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-white text-xs">✓</span>
                  ) : i === currentStep ? (
                    <Loader2 className="w-4 h-4 text-sky-500 animate-spin" />
                  ) : (
                    <span className="w-4 h-4 rounded-full border-2 border-gray-200" />
                  )}
                  <span className={i <= currentStep ? "text-gray-700" : "text-gray-300"}>{step}</span>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* CTA Button */}
        <Button
          onClick={handleAnalyze}
          disabled={loading || (!file && !manualText.trim())}
          className="w-full h-12 rounded-2xl bg-sky-500 hover:bg-sky-600 text-white font-semibold text-base transition-all"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Analysing...
            </span>
          ) : (
            "Analyse Prescription →"
          )}
        </Button>
      </motion.div>

      {/* Footer */}
      <p className="text-xs text-gray-300 mt-6 text-center max-w-xs">
        MediClear is for informational purposes only. Always consult your doctor before changing medications.
      </p>
    </div>
  );
}
```

---

## Step 3 — Results Screen (`app/results/page.tsx`)

This is the most important screen. Show one card per medicine, then alternatives below.

**Full component (`app/results/page.tsx`):**

```typescript
"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Pill, TrendingDown, AlertCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import MedicineCard from "@/components/MedicineCard";

export default function ResultsPage() {
  const router = useRouter();
  const [results, setResults] = useState<any[]>([]);

  useEffect(() => {
    const stored = sessionStorage.getItem("mediclear_results");
    if (!stored) {
      router.push("/");
      return;
    }
    setResults(JSON.parse(stored));
  }, [router]);

  if (results.length === 0) return null;

  const totalBrandCost = results.reduce((sum, r) => sum + (r.brand_price || 0), 0);
  const totalGenericCost = results.reduce((sum, r) => {
    const cheapest = r.alternatives?.[0]?.price || r.brand_price || 0;
    return sum + cheapest;
  }, 0);
  const totalSavings = totalBrandCost - totalGenericCost;

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center gap-3">
          <button onClick={() => router.push("/")} className="text-gray-400 hover:text-gray-600">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Pill className="w-5 h-5 text-sky-500" />
            <span className="font-semibold text-gray-900">MediClear</span>
          </div>
          <span className="ml-auto text-xs text-gray-400">{results.length} medicine{results.length > 1 ? "s" : ""} found</span>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 pt-4 space-y-4">
        {/* Savings Banner */}
        {totalSavings > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl p-4 text-white"
          >
            <div className="flex items-center gap-2 mb-1">
              <TrendingDown className="w-5 h-5" />
              <span className="font-semibold">You can save money!</span>
            </div>
            <p className="text-green-100 text-sm">
              Switch to generics and save <span className="text-white font-bold">₹{totalSavings}</span> on this prescription.
            </p>
          </motion.div>
        )}

        {/* Medicine Cards */}
        {results.map((medicine, i) => (
          <MedicineCard key={i} medicine={medicine} index={i} />
        ))}

        {/* Disclaimer */}
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-2xl p-4">
          <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-700">
            Always consult your doctor or pharmacist before switching to a generic alternative. Generics contain the same active ingredients but may differ in appearance.
          </p>
        </div>

        {/* Scan Another */}
        <Button
          onClick={() => router.push("/")}
          variant="outline"
          className="w-full h-12 rounded-2xl border-sky-200 text-sky-500 hover:bg-sky-50"
        >
          Scan Another Prescription
        </Button>
      </div>
    </div>
  );
}
```

---

## Step 4 — MedicineCard Component (`components/MedicineCard.tsx`)

```typescript
"use client";
import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, IndianRupee } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";

export default function MedicineCard({ medicine, index }: { medicine: any; index: number }) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  const cheapestAlt = medicine.alternatives?.[0];
  const savings = cheapestAlt ? (medicine.brand_price || 0) - cheapestAlt.price : 0;
  const savingsPct = medicine.brand_price ? Math.round((savings / medicine.brand_price) * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
    >
      {/* Medicine Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{medicine.brand_name}</h2>
            <p className="text-xs text-gray-400 mt-0.5">{medicine.generic_name}</p>
          </div>
          {medicine.brand_price && (
            <div className="text-right shrink-0">
              <div className="flex items-center gap-0.5 text-gray-400 text-xs">
                <IndianRupee className="w-3 h-3" />
                <span>{medicine.brand_price}</span>
              </div>
              <span className="text-xs text-gray-300">brand</span>
            </div>
          )}
        </div>

        {/* Purpose */}
        <div className="bg-sky-50 rounded-xl px-3 py-2 mb-4">
          <p className="text-sm text-sky-700">{medicine.purpose_simple}</p>
        </div>

        {/* Instructions */}
        {medicine.how_to_take?.length > 0 && (
          <ul className="space-y-1.5 mb-4">
            {medicine.how_to_take.map((step: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 mt-1.5 shrink-0" />
                {step}
              </li>
            ))}
          </ul>
        )}

        {/* Duration + Warning */}
        <div className="flex flex-wrap gap-2">
          {medicine.duration && medicine.duration !== "as prescribed" && (
            <Badge variant="outline" className="text-xs text-gray-500 border-gray-200">
              ⏱ {medicine.duration}
            </Badge>
          )}
          {medicine.warnings && (
            <Badge variant="outline" className="text-xs text-amber-600 border-amber-200 bg-amber-50">
              ⚠️ {medicine.warnings}
            </Badge>
          )}
        </div>
      </div>

      {/* Alternatives Toggle */}
      {medicine.alternatives?.length > 0 && (
        <div className="border-t border-gray-100">
          <button
            onClick={() => setShowAlternatives(!showAlternatives)}
            className="w-full flex items-center justify-between px-5 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span>💰 Cheaper alternatives</span>
              {savings > 0 && (
                <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full font-semibold">
                  Save ₹{savings} ({savingsPct}%)
                </span>
              )}
            </div>
            {showAlternatives ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showAlternatives && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="px-5 pb-4 space-y-2"
            >
              {medicine.alternatives.map((alt: any, i: number) => {
                const altSavings = (medicine.brand_price || 0) - alt.price;
                const altPct = medicine.brand_price ? Math.round((altSavings / medicine.brand_price) * 100) : 0;
                return (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <span className="text-sm text-gray-700">{alt.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-900">₹{alt.price}</span>
                      {altSavings > 0 && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${i === 0 ? "bg-green-100 text-green-700 font-semibold" : "bg-gray-100 text-gray-500"}`}>
                          {altPct}% off
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
              <p className="text-xs text-gray-300 mt-2">Same active ingredient. Ask your pharmacist.</p>
            </motion.div>
          )}
        </div>
      )}
    </motion.div>
  );
}
```

---

## Step 5 — Environment Variable

Create `frontend/.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

When deployed to Vercel, update this to the Railway backend URL.

---

## Step 6 — PWA Manifest (Optional but impressive)

Create `frontend/public/manifest.json`:
```json
{
  "name": "MediClear",
  "short_name": "MediClear",
  "description": "Understand your prescription instantly",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f9fafb",
  "theme_color": "#0ea5e9",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## What "Done" Looks Like

You're done when:
- [ ] `npm run dev` runs without errors
- [ ] You can drag an image onto the upload zone and see the preview
- [ ] Clicking "Analyse Prescription" shows the loading steps animation
- [ ] Results page shows at least one MedicineCard with instructions
- [ ] The alternatives section expands/collapses on click
- [ ] The green savings banner shows when there are cheaper options
- [ ] It looks clean on mobile (use Chrome DevTools → phone size)

---

## If You Get Stuck

1. **CORS error** → Backend already has CORS enabled for all origins. Just make sure backend is running on port 8000.
2. **API not returning data** → Check that `medicine_data.json` has `brand_price` field added. Ask Nithya/Adhithya.
3. **shadcn component not found** → Run `npx shadcn-ui@latest add [component-name]`
4. **framer-motion error** → Run `npm install framer-motion`
5. **Image won't upload** → Make sure `python-multipart` is in backend requirements and installed.

---

## Notes on Design

- **No dark mode** needed. Keep it light, clean, white.
- **Rounded corners everywhere** — `rounded-2xl` is your best friend.
- **Sky blue = trust** — Use `text-sky-500`, `bg-sky-50`, `border-sky-200` consistently.
- **Green = savings** — Only use green for price savings, nowhere else.
- **Amber = warnings** — Only for medicine warnings and disclaimer.
- **Don't over-animate** — Framer Motion `opacity` + `y` entrance is enough. No bouncing.
- **Spacing** — Give things room to breathe. `space-y-4` between cards, `p-5` inside cards.
