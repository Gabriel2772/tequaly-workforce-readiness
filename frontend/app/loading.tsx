export default function Loading() {
  return <main className="workspace-page dashboard-page" aria-busy="true" aria-label="Carregando visão executiva"><div className="dashboard-skeleton dashboard-skeleton-hero" /><div className="dashboard-kpis">{Array.from({ length: 6 }, (_, index) => <div className="dashboard-skeleton dashboard-skeleton-card" key={index} />)}</div><div className="dashboard-skeleton dashboard-skeleton-panel" /></main>;
}
