"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="workspace-page dashboard-error"><section className="planner-panel"><p className="eyebrow">Visão temporariamente indisponível</p><h1>Não foi possível carregar os indicadores.</h1><p className="page-summary">Verifique se a API está disponível e tente novamente.</p><button className="primary-action button-action" onClick={reset} type="button">Tentar novamente</button></section></main>;
}
