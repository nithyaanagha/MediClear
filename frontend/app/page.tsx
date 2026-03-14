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