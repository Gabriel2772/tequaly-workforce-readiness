"use client";

import { useState } from "react";

import { downloadExport } from "@/lib/api";

type ExportType = Parameters<typeof downloadExport>[0];

export function ExportButton({ type, label }: { type: ExportType; label: string }) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function download(format: "csv" | "xlsx") {
    setPending(true);
    setMessage("");
    try {
      const result = await downloadExport(type, format);
      const url = URL.createObjectURL(result.blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = result.filename;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage(`${label} exportado em ${format.toUpperCase()}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Falha ao exportar.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="export-card">
      <strong>{label}</strong>
      <div><button disabled={pending} onClick={() => download("csv")} type="button">CSV</button><button disabled={pending} onClick={() => download("xlsx")} type="button">XLSX</button></div>
      <small aria-live="polite">{message}</small>
    </div>
  );
}

