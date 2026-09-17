import { createEmployeeAction } from "@/app/workforce-actions";
import { EmployeeForm } from "@/features/workforce/employee-form";
import { listRoles } from "@/lib/api";


export const dynamic = "force-dynamic";

export default async function NewEmployeePage() {
  const roles = await listRoles();

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Força de trabalho</p>
          <h1>Novo colaborador</h1>
          <p className="page-summary">
            Cadastre a identidade operacional usando um cargo canônico ativo.
          </p>
        </div>
      </header>
      <EmployeeForm
        action={createEmployeeAction}
        roles={roles.items.filter((role) => role.active)}
      />
    </main>
  );
}
