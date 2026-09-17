import Link from "next/link";

import { getOperation } from "@/lib/api";


export const dynamic = "force-dynamic";

type PageProps = { params: Promise<{ id: string }> };

export default async function OperationDetailPage({ params }: PageProps) {
  const { id } = await params;
  const operation = await getOperation(id);

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{operation.code}</p>
          <h1>{operation.name}</h1>
          <p className="page-summary">
            {operation.client_name} · {operation.base_location} · {operation.status}
          </p>
        </div>
      </header>
      <nav aria-label="Seções da operação" className="detail-tabs">
        <a href="#resumo">Resumo</a>
        <a href="#demanda">Demanda</a>
        <a href="#requisitos">Requisitos</a>
        <Link href={`/planejador?operation=${operation.id}`}>Candidatos</Link>
        <Link href={`/planejador?operation=${operation.id}`}>Cenários</Link>
        <span aria-disabled="true">Decisão</span>
        <span aria-disabled="true">Resultado</span>
      </nav>
      <section className="detail-panel" id="resumo">
        <h2>Resumo</h2>
        <dl className="profile-facts">
          <div><dt>Início</dt><dd>{new Date(operation.starts_at).toLocaleString("pt-BR")}</dd></div>
          <div><dt>Fim</dt><dd>{new Date(operation.ends_at).toLocaleString("pt-BR")}</dd></div>
          <div><dt>Mobilização</dt><dd>{operation.mobilization_deadline ? new Date(operation.mobilization_deadline).toLocaleString("pt-BR") : "Não informado"}</dd></div>
          <div><dt>Orçamento</dt><dd>{operation.budget_cents?.toLocaleString("pt-BR") ?? "Não informado"}</dd></div>
        </dl>
      </section>
      <section className="detail-panel" id="demanda">
        <h2>Demanda</h2>
        <div className="table-frame">
          <table aria-label="Demanda da operação" className="data-table">
            <thead><tr><th scope="col">Cargo</th><th scope="col">Quantidade</th><th scope="col">Turno</th><th scope="col">Prioridade</th></tr></thead>
            <tbody>{operation.demands.map((demand) => <tr key={demand.id}><td>{demand.role_id}</td><td>{demand.quantity}</td><td>{demand.shift_code}</td><td>{demand.priority}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
      <section className="detail-panel" id="requisitos">
        <h2>Requisitos</h2>
        <div className="table-frame">
          <table aria-label="Requisitos da operação" className="data-table">
            <thead><tr><th scope="col">Código</th><th scope="col">Requisito</th><th scope="col">Tipo</th><th scope="col">Obrigatório</th></tr></thead>
            <tbody>{operation.requirements.map((requirement) => <tr key={requirement.id}><td>{requirement.code}</td><td>{requirement.name}</td><td>{requirement.requirement_type}</td><td>{requirement.mandatory ? "Sim" : "Não"}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
