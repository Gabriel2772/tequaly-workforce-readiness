import Link from "next/link";

import { EmployeeTable } from "@/features/employees/employee-table";
import { listEmployees } from "@/lib/api";


export const dynamic = "force-dynamic";

type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function EmployeesPage({ searchParams }: PageProps) {
  const input = await searchParams;
  const parameters = new URLSearchParams();
  parameters.set("page", typeof input.page === "string" ? input.page : "1");
  parameters.set("page_size", "25");
  if (typeof input.query === "string" && input.query.trim()) {
    parameters.set("query", input.query.trim());
  }
  const data = await listEmployees(parameters);

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Força de trabalho</p>
          <h1>Colaboradores</h1>
          <p className="page-summary">
            {data.total.toLocaleString("pt-BR")} perfis disponíveis para qualificação e alocação.
          </p>
        </div>
        <form className="search-form">
          <label htmlFor="employee-query">Buscar por nome ou matrícula</label>
          <div>
            <input defaultValue={typeof input.query === "string" ? input.query : ""} id="employee-query" name="query" />
            <button type="submit">Buscar</button>
          </div>
        </form>
        <Link className="primary-action" href="/colaboradores/novo">
          Novo colaborador
        </Link>
      </header>
      <EmployeeTable employees={data.items} />
    </main>
  );
}
