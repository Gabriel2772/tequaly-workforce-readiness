import Link from "next/link";

import { listOperations } from "@/lib/api";


export const dynamic = "force-dynamic";

export default async function OperationsPage() {
  const operations = await listOperations();

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Planejamento operacional</p>
          <h1>Operações</h1>
          <p className="page-summary">
            {operations.total.toLocaleString("pt-BR")} operações com demanda e requisitos estruturados.
          </p>
        </div>
        <Link className="primary-action" href="/operacoes/novo">
          Nova operação
        </Link>
      </header>
      <div className="table-frame">
        <table aria-label="Operações" className="data-table">
          <thead>
            <tr>
              <th scope="col">Operação</th>
              <th scope="col">Cliente</th>
              <th scope="col">Base</th>
              <th scope="col">Período</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {operations.items.map((operation) => (
              <tr key={operation.id}>
                <td>
                  <Link href={`/operacoes/${operation.id}`}>{operation.name}</Link>
                  <span className="cell-detail">{operation.code}</span>
                </td>
                <td>{operation.client_name}</td>
                <td>{operation.base_location}</td>
                <td>
                  {new Date(operation.starts_at).toLocaleDateString("pt-BR")} –{" "}
                  {new Date(operation.ends_at).toLocaleDateString("pt-BR")}
                </td>
                <td><span className="status">{operation.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
