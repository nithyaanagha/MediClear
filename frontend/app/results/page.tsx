"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Pill, TrendingDown, AlertCircle} from "lucide-react";
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
