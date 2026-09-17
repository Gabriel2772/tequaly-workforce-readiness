"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { loginSession } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("planner.demo");
  const [password, setPassword] = useState("TequalyDemo!2026");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await loginSession({ username, password });
      window.dispatchEvent(new Event("twr-session-changed"));
      router.push("/");
      router.refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível iniciar a sessão.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="login-form" onSubmit={submit}>
      <label>
        <span>Usuário</span>
        <input autoComplete="username" onChange={(event) => setUsername(event.target.value)} required value={username} />
      </label>
      <label>
        <span>Senha</span>
        <input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
      </label>
      {error ? <p className="form-alert" role="alert">{error}</p> : null}
      <button className="primary-action button-action" disabled={pending} type="submit">
        {pending ? "Entrando…" : "Entrar"}
      </button>
    </form>
  );
}
