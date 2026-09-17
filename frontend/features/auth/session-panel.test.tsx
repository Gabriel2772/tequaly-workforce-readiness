import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SessionPanel } from "./session-panel";

const getCurrentSession = vi.fn();
const logoutSession = vi.fn();

vi.mock("@/lib/api", () => ({
  getCurrentSession: () => getCurrentSession(),
  logoutSession: () => logoutSession(),
}));

describe("SessionPanel", () => {
  afterEach(cleanup);
  beforeEach(() => vi.clearAllMocks());

  it("renders an authenticated user's identity and logs out", async () => {
    getCurrentSession.mockResolvedValue({
      id: "1",
      username: "admin.demo",
      display_name: "Administrador de demonstração",
      role: "admin",
      expires_at: "2026-08-25T12:00:00Z",
    });
    logoutSession.mockResolvedValue(undefined);
    render(<SessionPanel />);

    expect(await screen.findByText("Administrador de demonstração")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Sair" }));
    await waitFor(() => expect(logoutSession).toHaveBeenCalled());
    expect(await screen.findByRole("link", { name: "Entrar" })).not.toBeNull();
  });

  it("offers login when there is no signed session", async () => {
    getCurrentSession.mockResolvedValue(null);
    render(<SessionPanel />);

    expect((await screen.findByRole("link", { name: "Entrar" })).getAttribute("href")).toBe("/entrar");
  });
});
