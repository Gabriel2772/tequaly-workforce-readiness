"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { SessionPanel } from "@/features/auth/session-panel";
import {
  NavigationIcon,
  type NavigationIconName,
} from "@/components/navigation-icons";

const navigation: Array<{
  href: string;
  label: string;
  icon: NavigationIconName;
}> = [
  { href: "/", label: "Visão geral", icon: "overview" },
  { href: "/colaboradores", label: "Colaboradores", icon: "people" },
  { href: "/qualificacoes", label: "Qualificações", icon: "qualification" },
  { href: "/operacoes", label: "Operações", icon: "operations" },
  { href: "/planejador", label: "Planejador de equipe", icon: "planner" },
  { href: "/capacitacoes", label: "Capacitações", icon: "training" },
  { href: "/risco-e-cobertura", label: "Risco e cobertura", icon: "risk" },
  { href: "/auditoria", label: "Auditoria de decisão", icon: "audit" },
  { href: "/configuracoes", label: "Configurações", icon: "settings" },
  { href: "/conexoes-mcp", label: "Conexões MCP", icon: "mcp" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileNavigationPathname, setMobileNavigationPathname] = useState<string | null>(null);
  const mobileNavigationOpen = mobileNavigationPathname === pathname;

  useEffect(() => {
    document.body.classList.toggle("mobile-nav-open", mobileNavigationOpen);
    return () => document.body.classList.remove("mobile-nav-open");
  }, [mobileNavigationOpen]);

  function closeMobileNavigation() {
    setMobileNavigationPathname(null);
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Ir para o conteúdo</a>
      <aside
        className={`app-sidebar${mobileNavigationOpen ? " app-sidebar-open" : ""}`}
        id="primary-sidebar"
      >
        <Link
          aria-label="Tequaly Workforce Readiness"
          className="brand"
          href="/"
          onClick={closeMobileNavigation}
        >
          <Image
            alt="Logo da Tequaly"
            className="tequaly-brand-mark"
            height={40}
            src="/brand/tequaly-symbol.svg"
            unoptimized
            width={40}
          />
          <span className="brand-copy"><strong>Tequaly</strong><small>Workforce Readiness</small></span>
        </Link>
        <nav aria-label="Navegação principal">
          {navigation.map((item) => {
            const active = item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                aria-current={active ? "page" : undefined}
                aria-label={item.label}
                href={item.href}
                key={item.href}
                onClick={closeMobileNavigation}
                title={item.label}
              >
                <NavigationIcon name={item.icon} />
                <span className="nav-label">{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="environment-label"><span aria-hidden="true" />Dados simulados</div>
      </aside>
      <div className="app-workspace">
        <header className="app-topbar">
          <button
            aria-controls="primary-sidebar"
            aria-expanded={mobileNavigationOpen}
            aria-label={mobileNavigationOpen ? "Fechar menu principal" : "Abrir menu principal"}
            className="mobile-menu-button"
            onClick={() =>
              setMobileNavigationPathname((openPathname) =>
                openPathname === pathname ? null : pathname,
              )
            }
            type="button"
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span aria-hidden="true" />
          </button>
          <div className="app-topbar-copy"><strong>Planejamento de força de trabalho</strong><span>Ambiente de demonstração</span></div>
          <SessionPanel />
        </header>
        <div id="main-content">{children}</div>
      </div>
      {mobileNavigationOpen ? (
        <button
          aria-label="Fechar menu principal"
          className="sidebar-backdrop"
          onClick={closeMobileNavigation}
          type="button"
        />
      ) : null}
    </div>
  );
}
