import { StatusBadge } from "@/components/status-badge";
import type { DataQualityOverview } from "@/lib/api";

const tones = { low: "success", medium: "warning", high: "danger" } as const;

export function QualityPanel({ overview }: { overview: DataQualityOverview }) {
  return (
    <section className="planner-panel quality-panel" aria-labelledby="quality-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Confiabilidade da base</p>
          <h2 id="quality-title">Higiene de dados</h2>
          <p className="panel-summary">Pendências que podem distorcer elegibilidade, custo ou cobertura.</p>
        </div>
        <strong className="quality-score">
          {overview.completeness_percent === null ? "—" : `${overview.completeness_percent.toLocaleString("pt-BR")}%`}
          <small>perfis completos</small>
        </strong>
      </header>
      <div className="quality-issues">
        {overview.issues.map((issue) => (
          <article key={issue.code}>
            <div><StatusBadge tone={tones[issue.severity]}>{String(issue.count)}</StatusBadge><strong>{issue.label}</strong></div>
            <p>{issue.action}</p>
          </article>
        ))}
      </div>
      <p className="metric-note">Fonte atual: dados sintéticos de demonstração. Valide a origem antes do uso operacional.</p>
    </section>
  );
}
