import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell } from "./app-shell";

let pathname = "/";

vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
}));

vi.mock("next/link", () => ({
  default: ({ onClick, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      {...props}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
      }}
    />
  ),
}));

vi.mock("@/features/auth/session-panel", () => ({
  SessionPanel: () => null,
}));

describe("AppShell", () => {
  afterEach(cleanup);

  beforeEach(() => {
    pathname = "/";
  });

  it("uses labeled SVG navigation, the Tequaly logo, and no copilot launcher", () => {
    render(<AppShell><main>Conteúdo</main></AppShell>);

    expect(screen.getByRole("link", { name: "Conexões MCP" })).not.toBeNull();
    expect(
      screen
        .getByRole("navigation", { name: "Navegação principal" })
        .querySelectorAll("svg"),
    ).toHaveLength(10);
    expect(screen.queryByRole("button", { name: /copiloto/i })).toBeNull();
    expect(
      screen.getByRole("img", { name: "Logo da Tequaly" }).getAttribute("src"),
    ).toContain("/brand/tequaly-symbol.svg");
  });

  it("marks the matching navigation item active on nested routes", () => {
    pathname = "/operacoes/operacao-1";

    render(<AppShell><main>Conteúdo</main></AppShell>);

    expect(
      screen.getByRole("link", { name: "Operações" }).getAttribute("aria-current"),
    ).toBe("page");
    expect(
      screen.getByRole("link", { name: "Visão geral" }).getAttribute("aria-current"),
    ).toBeNull();
  });

  it("does not mark a sibling route that only shares the same prefix", () => {
    pathname = "/operacoes-relatorio";

    render(<AppShell><main>Conteúdo</main></AppShell>);

    expect(
      screen.getByRole("link", { name: "Operações" }).getAttribute("aria-current"),
    ).toBeNull();
  });

  it("opens the mobile navigation and closes it after choosing a destination", () => {
    render(<AppShell><main>Conteúdo</main></AppShell>);

    const menuButton = screen.getByRole("button", { name: "Abrir menu principal" });
    expect(menuButton.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(menuButton);
    expect(menuButton.getAttribute("aria-expanded")).toBe("true");
    expect(document.body.classList.contains("mobile-nav-open")).toBe(true);

    fireEvent.click(screen.getByRole("link", { name: "Conexões MCP" }));
    expect(menuButton.getAttribute("aria-expanded")).toBe("false");
    expect(document.body.classList.contains("mobile-nav-open")).toBe(false);
  });

  it("closes the mobile navigation when the pathname changes externally", () => {
    const view = render(<AppShell><main>Conteúdo</main></AppShell>);
    const menuButton = screen.getByRole("button", { name: "Abrir menu principal" });
    fireEvent.click(menuButton);
    expect(menuButton.getAttribute("aria-expanded")).toBe("true");

    pathname = "/conexoes-mcp";
    view.rerender(<AppShell><main>Novo conteúdo</main></AppShell>);

    expect(menuButton.getAttribute("aria-expanded")).toBe("false");
    expect(document.body.classList.contains("mobile-nav-open")).toBe(false);
  });
});
