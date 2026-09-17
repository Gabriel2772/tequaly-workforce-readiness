"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getCurrentSession, logoutSession, type UserSession } from "@/lib/api";

const roleLabels: Record<UserSession["role"], string> = {
  viewer: "Leitura",
  planner: "Planejador",
  admin: "Administrador",
};

export function SessionPanel() {
  const [session, setSession] = useState<UserSession | null | undefined>(undefined);

  useEffect(() => {
    const refresh = () => void getCurrentSession().then(setSession).catch(() => setSession(null));
    refresh();
    window.addEventListener("twr-session-changed", refresh);
    return () => window.removeEventListener("twr-session-changed", refresh);
  }, []);

  async function signOut() {
    await logoutSession();
    setSession(null);
  }

  if (session === undefined) return <div className="session-placeholder" aria-label="Verificando sessão" />;
  if (session === null) return <Link className="login-link" href="/entrar">Entrar</Link>;

  const initials = session.display_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  return (
    <div className="session-controls">
      <div className="user-chip" aria-label={`Usuário atual: ${session.display_name}`}>
        <span aria-hidden="true">{initials}</span>
        <div><strong>{session.display_name}</strong><small>{roleLabels[session.role]}</small></div>
      </div>
      <button className="text-button" onClick={() => void signOut()} type="button">Sair</button>
    </div>
  );
}
