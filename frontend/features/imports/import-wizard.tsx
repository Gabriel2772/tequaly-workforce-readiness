"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import { commitImport, previewImport } from "@/lib/api";
import type { ImportContractName, ImportPreviewView } from "@/lib/api";

const contractLabels: Record<ImportContractName, string> = {
  employees: "Colaboradores",
  employee_qualifications: "Qualificações por colaborador",
  operations: "Operações e demandas",
  training_catalog: "Catálogo de treinamentos",
};

async function fileBase64(file: File): Promise<string> {
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let index = 0; index < bytes.length; index += 8_192) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 8_192));
  }
  return btoa(binary);
}

function downloadErrors(preview: ImportPreviewView) {
  const escape = (value: string | number | null) =>
    `"${String(value ?? "").replaceAll('"', '""')}"`;
  const csv = [
    ["linha", "codigo", "campo", "mensagem"],
    ...preview.errors.map((error) => [error.row, error.code, error.field, error.message]),
  ]
    .map((row) => row.map(escape).join(","))
    .join("\n");
  const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `erros-${preview.filename}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ImportWizard() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewView | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function submitPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const file = selectedFile;
    if (!file?.size) return;
    setPending(true);
    setMessage("");
    setPreview(null);
    setConfirmed(false);
    try {
      const result = await previewImport({
        contract: String(data.get("contract")) as ImportContractName,
        filename: file.name,
        content_base64: await fileBase64(file),
      });
      setPreview(result);
      setMessage(
        result.invalid_rows
          ? "Preview concluído com inconsistências. Corrija o arquivo antes de confirmar."
          : "Preview validado. Revise o mapeamento e confirme a transação.",
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível validar o arquivo.");
    } finally {
      setPending(false);
    }
  }

  async function confirmImport() {
    if (!preview || !confirmed || preview.invalid_rows) return;
    setPending(true);
    setMessage("");
    try {
      const result = await commitImport(preview.token, true);
      setMessage(
        `Importação concluída: ${result.created} criado(s) e ${result.updated} atualizado(s).`,
      );
      setConfirmed(false);
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível confirmar a importação.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="planner-panel import-panel" aria-labelledby="import-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Entrada controlada</p>
          <h2 id="import-title">Importar dados canônicos</h2>
          <p className="panel-summary">
            CSV ou XLSX, até 5 MB e 5.000 linhas. O preview não altera dados.
          </p>
        </div>
      </header>
      <form className="import-controls" onSubmit={submitPreview}>
        <label>
          Tipo de dado
          <select defaultValue="employees" name="contract">
            {Object.entries(contractLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          Arquivo
          <input accept=".csv,.xlsx" name="file" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} required type="file" />
        </label>
        <button className="secondary-action button-action" disabled={pending} type="submit">
          {pending ? "Validando…" : "Gerar preview"}
        </button>
      </form>

      {preview ? (
        <div className="import-preview">
          <div className="quality-summary" aria-label="Resumo do preview">
            <div><span>Linhas</span><strong>{preview.total_rows}</strong></div>
            <div><span>Válidas</span><strong>{preview.valid_rows}</strong></div>
            <div><span>Inválidas</span><strong>{preview.invalid_rows}</strong></div>
            <div><span>Contrato</span><strong>v{preview.contract_version}</strong></div>
          </div>
          <div className="mapping-list" aria-label="Mapeamento de colunas">
            {Object.entries(preview.mapping).map(([source, target]) => (
              <span key={source}>{source} <b aria-hidden="true">→</b> {target}</span>
            ))}
          </div>
          {preview.errors.length ? (
            <>
              <DataTable ariaLabel="Inconsistências da importação">
                <thead><tr><th>Linha</th><th>Código</th><th>Campo</th><th>Mensagem</th></tr></thead>
                <tbody>{preview.errors.slice(0, 50).map((error) => (
                  <tr key={`${error.row}-${error.code}-${error.field}`}>
                    <td>{error.row}</td><td><StatusBadge tone="danger">{error.code}</StatusBadge></td>
                    <td>{error.field ?? "—"}</td><td>{error.message}</td>
                  </tr>
                ))}</tbody>
              </DataTable>
              <button className="secondary-action button-action" onClick={() => downloadErrors(preview)} type="button">
                Baixar relatório de erros
              </button>
            </>
          ) : (
            <div className="import-confirmation">
              <label className="confirmation-check">
                <input checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} type="checkbox" />
                Confirmo o mapeamento e a gravação transacional destas {preview.valid_rows} linhas.
              </label>
              <button className="primary-action button-action" disabled={!confirmed || pending} onClick={confirmImport} type="button">
                {pending ? "Importando…" : "Confirmar importação"}
              </button>
            </div>
          )}
        </div>
      ) : null}
      <p aria-live="polite" className="form-feedback" role="status">{message}</p>
    </section>
  );
}
