import { ReferenceCatalog } from "@/features/workforce/reference-catalog";
import { listQualifications } from "@/lib/api";
import { createQualificationAction } from "@/app/workforce-actions";


export const dynamic = "force-dynamic";

export default async function QualificationsPage() {
  const qualifications = await listQualifications();

  return (
    <main className="workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Referências operacionais</p>
          <h1>Qualificações</h1>
          <p className="page-summary">
            {qualifications.total.toLocaleString("pt-BR")} definições canônicas com validade estruturada.
          </p>
        </div>
      </header>
      <ReferenceCatalog
        createAction={createQualificationAction}
        qualifications={qualifications.items}
      />
    </main>
  );
}
