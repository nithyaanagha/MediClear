"use client";
import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, IndianRupee, Volume2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";

export default function MedicineCard({ medicine, index }: { medicine: any; index: number }) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  const speakInstructions = () => {
    const text = `
      ${medicine.brand_name}. 
      ${medicine.purpose_simple}. 
      How to take: ${medicine.how_to_take?.join(". ")}. 
      Warning: ${medicine.warnings}
    `;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  };
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
          <div className="flex items-center gap-2">
            {medicine.brand_price && (
              <div className="text-right shrink-0">
                <div className="flex items-center gap-0.5 text-gray-400 text-xs">
                  <IndianRupee className="w-3 h-3" />
                  <span>{medicine.brand_price}</span>
                </div>
                <span className="text-xs text-gray-300">brand</span>
              </div>
            )}
            <button
              onClick={speakInstructions}
              className="text-gray-300 hover:text-sky-500 transition-colors"
              title="Read aloud"
            >
              <Volume2 className="w-5 h-5" />
            </button>
          </div>
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
