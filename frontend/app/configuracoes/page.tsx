import { ExportButton } from "@/components/export-button";
import { QualityPanel } from "@/features/data-quality/quality-panel";
import { ImportWizard } from "@/features/imports/import-wizard";
import { getDataQualityOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

const exports = [
  ["employees", "Colaboradores"], ["readiness", "Matriz de prontidão"],
  ["gaps", "Gaps"], ["scenarios", "Cenários"], ["training", "Capacitações"],
  ["risk", "Risco"], ["decision_runs", "Decisões auditadas"],
] as const;

export default async function SettingsPage() {
  const quality = await getDataQualityOverview();
  return (
    <main className="workspace-page settings-page">
      <header className="page-header"><div><p className="eyebrow">Administração</p><h1>Dados, integração e governança</h1><p className="page-summary">Valide a qualidade da base, faça cargas controladas e extraia dados sem expor segredos.</p></div></header>
      <QualityPanel overview={quality} />
      <ImportWizard />
      <section className="planner-panel" aria-labelledby="exports-title">
        <header className="panel-header"><div><p className="eyebrow">Saída segura</p><h2 id="exports-title">Exportações</h2><p className="panel-summary">Arquivos incluem ator, horário, filtros, versão e fuso; segredos e custo individual não são exportados.</p></div></header>
        <div className="export-grid">{exports.map(([type, label]) => <ExportButton key={type} label={label} type={type} />)}</div>
      </section>
    </main>
  );
}
