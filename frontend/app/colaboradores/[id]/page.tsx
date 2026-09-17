import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, getEmployeeProfile } from "@/lib/api";


export const dynamic = "force-dynamic";

export default async function EmployeeProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let profile;
  try {
    profile = await getEmployeeProfile(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  return (
    <main className="workspace-page profile-page">
      <Link className="text-link" href="/colaboradores">
        ← Voltar para colaboradores
      </Link>
      <header className="profile-header">
        <div>
          <p className="eyebrow">Perfil consolidado</p>
          <h1>{profile.nome}</h1>
          <p className="page-summary">{profile.cargo_funcao_principal}</p>
        </div>
        <dl className="profile-facts">
          <div>
            <dt>Base</dt>
            <dd>{profile.base_localizacao}</dd>
          </div>
          <div>
            <dt>Senioridade</dt>
            <dd>{profile.experiencia_senioridade}</dd>
          </div>
          <div>
            <dt>Prontidão</dt>
            <dd>{String(profile.prontidao.status ?? "não avaliada")}</dd>
          </div>
        </dl>
      </header>
      <section className="profile-section" aria-labelledby="qualifications-title">
        <h2 id="qualifications-title">Qualificações</h2>
        {profile.qualificacoes.length ? (
          <ul className="record-list">
            {profile.qualificacoes.map((qualification) => (
              <li key={qualification.id}>
                <div>
                  <strong>{qualification.nome}</strong>
                  <span>{qualification.categoria}</span>
                </div>
                <span className="status">{qualification.status.replaceAll("_", " ")}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>Nenhuma qualificação cadastrada.</p>
        )}
      </section>
    </main>
  );
}
