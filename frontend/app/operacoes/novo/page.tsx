import { createOperationAction } from "@/app/workforce-actions";
import { OperationForm } from "@/features/operations/operation-form";
import { listRoles } from "@/lib/api";


export const dynamic = "force-dynamic";

export default async function NewOperationPage() {
  const roles = await listRoles();

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Planejamento operacional</p>
          <h1>Nova operação</h1>
          <p className="page-summary">Defina o período e a primeira demanda de cargo.</p>
        </div>
      </header>
      <OperationForm
        action={createOperationAction}
        roles={roles.items.filter((role) => role.active)}
      />
    </main>
  );
}
