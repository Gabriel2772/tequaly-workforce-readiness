import { LoginForm } from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="page-shell login-page">
      <section className="login-card">
        <div className="eyebrow">Acesso controlado</div>
        <h1>Entrar no Workforce Readiness</h1>
        <p>Use um perfil de demonstração. As permissões são verificadas no servidor em cada ação.</p>
        <LoginForm />
        <div className="demo-credentials" aria-label="Credenciais de demonstração">
          <strong>Perfis disponíveis</strong>
          <code>viewer.demo</code><code>planner.demo</code><code>admin.demo</code>
          <small>Senha para todos: TequalyDemo!2026</small>
        </div>
      </section>
    </main>
  );
}
