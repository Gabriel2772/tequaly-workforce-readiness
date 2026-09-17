import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LoginForm } from "./login-form";

const push = vi.fn();
const refresh = vi.fn();
const loginSession = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh }) }));
vi.mock("@/lib/api", () => ({ loginSession: (...args: unknown[]) => loginSession(...args) }));

describe("LoginForm", () => {
  afterEach(cleanup);
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("authenticates and returns to the dashboard", async () => {
    loginSession.mockResolvedValue({ role: "planner" });
    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText("Usuário"), {
      target: { value: "planner.demo" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), {
      target: { value: "TequalyDemo!2026" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(loginSession).toHaveBeenCalledWith({
      username: "planner.demo",
      password: "TequalyDemo!2026",
    }));
    expect(push).toHaveBeenCalledWith("/");
  });

  it("keeps a generic backend error visible", async () => {
    loginSession.mockRejectedValue(new Error("Usuário ou senha inválidos."));
    render(<LoginForm />);
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect((await screen.findByRole("alert")).textContent).toBe("Usuário ou senha inválidos.");
  });
});
