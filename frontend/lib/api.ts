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