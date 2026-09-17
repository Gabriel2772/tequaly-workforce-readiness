import { FragilityHeatmap } from "@/features/risk/fragility-heatmap";
import { getFragility } from "@/lib/api";

export const dynamic = "force-dynamic";

type PageProps = { searchParams: Promise<{ horizonte?: string }> };

export default async function RiskCoveragePage({ searchParams }: PageProps) {
  const parameters = await searchParams;
  const requestedHorizon = Number(parameters.horizonte ?? 180);
  const horizonDays = Number.isInteger(requestedHorizon) && requestedHorizon >= 1 && requestedHorizon <= 3650 ? requestedHorizon : 180;
  const report = await getFragility(horizonDays);
  return (
    <main className="workspace-page risk-page">
      <header className="page-header risk-page-header">
        <div><p className="eyebrow">Risco e cobertura</p><h1>Fragilidade operacional explicável</h1><p className="page-summary">Cobertura, redundância, vencimentos e bloqueios de capacitação para {report.operation_count} operação(ões).</p></div>
        <form className="operation-picker" method="get"><label htmlFor="horizon">Horizonte</label><select defaultValue={horizonDays} id="horizon" name="horizonte"><option value="90">90 dias</option><option value="180">180 dias</option><option value="365">1 ano</option><option value="730">2 anos</option></select><button type="submit">Atualizar</button></form>
      </header>
      <section aria-label="Resumo de riscos" className="risk-summary">
        <div><span>Críticos</span><strong>{report.summary.critical}</strong></div><div><span>Altos</span><strong>{report.summary.high}</strong></div><div><span>Médios</span><strong>{report.summary.medium}</strong></div><div><span>Baixos</span><strong>{report.summary.low}</strong></div>
      </section>
      <FragilityHeatmap report={report} />
    </main>
  );
}
