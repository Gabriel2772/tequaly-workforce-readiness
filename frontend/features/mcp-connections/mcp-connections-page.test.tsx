import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";
import type { McpConnection } from "@/lib/api";

import { McpConnectionsPage } from "./mcp-connections-page";

const api = vi.hoisted(() => ({
  listMcpConnections: vi.fn(),
  createMcpConnection: vi.fn(),
  updateMcpConnection: vi.fn(),
  validateMcpConnection: vi.fn(),
  deleteMcpConnection: vi.fn(),
  getMcpToolCatalog: vi.fn(),
}));

vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  ...api,
}));

const connection: McpConnection = {
  id: "connection-1",
  name: "MCP Planejamento",
  client_type: "claude" as const,
  endpoint_url: "https://mcp.example.com/mcp",
  transport: "streamable_http" as const,
  notes: "Somente leitura",
  enabled: true,
  created_at: "2026-08-25T12:00:00Z",
  updated_at: "2026-08-25T12:00:00Z",
  last_validated_at: null,
};

const catalog = [{
  name: "get_readiness_overview",
  description: "Resumo da prontidão",
  effect: "read" as const,
  input_schema: {},
}];

function configuredApi(connections = [connection]) {
  api.listMcpConnections.mockResolvedValue(connections);
  api.getMcpToolCatalog.mockResolvedValue(catalog);
  api.createMcpConnection.mockResolvedValue(connection);
  api.updateMcpConnection.mockResolvedValue(connection);
  api.validateMcpConnection.mockResolvedValue({
    valid: true,
    normalized_endpoint_url: "https://mcp.example.com/mcp",
    validated_at: "2026-08-25T12:00:00Z",
  });
  api.deleteMcpConnection.mockResolvedValue(undefined);
}

describe("McpConnectionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
      configurable: true,
      value: vi.fn(function showModal(this: HTMLDialogElement) {
        this.open = true;
      }),
      writable: true,
    });
    Object.defineProperty(HTMLDialogElement.prototype, "close", {
      configurable: true,
      value: vi.fn(function close(this: HTMLDialogElement) {
        this.open = false;
        this.dispatchEvent(new Event("close"));
      }),
      writable: true,
    });
    Object.assign(navigator, { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
    configuredApi();
  });

  afterEach(cleanup);

  it("creates, validates, copies, toggles and deletes a connection", async () => {
    configuredApi([]);
    render(<McpConnectionsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Cadastrar MCP" }));
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "MCP Planejamento" } });
    fireEvent.change(screen.getByLabelText("Destino"), { target: { value: "claude" } });
    fireEvent.change(screen.getByLabelText("Endpoint MCP"), { target: { value: "https://mcp.example.com/mcp" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar conexão" }));

    await waitFor(() => expect(api.createMcpConnection).toHaveBeenCalledWith(expect.objectContaining({
      client_type: "claude",
      endpoint_url: "https://mcp.example.com/mcp",
    })));
    await screen.findByRole("button", { name: "Validar configuração" });

    fireEvent.click(screen.getByRole("button", { name: "Validar configuração" }));
    expect(await screen.findByText("Configuração válida")).not.toBeNull();
    expect(screen.getByText(/^Validada em /)).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Copiar configuração" }));
    await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('"url"')));

    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));
    await waitFor(() => expect(api.updateMcpConnection).toHaveBeenCalledWith("connection-1", { enabled: false }));

    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
    await waitFor(() => expect(api.deleteMcpConnection).toHaveBeenCalledWith("connection-1"));
    expect(HTMLDialogElement.prototype.close).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("dialog", { name: "Excluir conexão MCP?" })).toBeNull();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Cadastrar MCP" }));
  }, 15000);

  it("shows the empty state and provider plan guidance without chat controls", async () => {
    configuredApi([]);
    render(<McpConnectionsPage />);

    expect(await screen.findByText(/Nenhuma conexão cadastrada/)).not.toBeNull();
    expect(screen.getByRole("heading", { name: "Como levar uma conexão ao cliente" })).not.toBeNull();
    expect(screen.getByText(/permissões do workspace/i)).not.toBeNull();
    expect(screen.getByText(/regras do plano/i)).not.toBeNull();
    expect(screen.queryByRole("textbox", { name: /mensagem|chat/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /entrar|login/i })).toBeNull();
  });

  it("filters connections and prefills an edit form", async () => {
    configuredApi([
      connection,
      { ...connection, id: "connection-2", name: "MCP Pessoas", client_type: "chatgpt", enabled: false },
    ]);
    render(<McpConnectionsPage />);

    await screen.findByText("MCP Pessoas");
    fireEvent.change(screen.getByLabelText("Buscar conexões"), { target: { value: "Pessoas" } });
    expect(screen.queryByText("MCP Planejamento")).toBeNull();
    fireEvent.change(screen.getByLabelText("Buscar conexões"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Filtrar por destino"), { target: { value: "claude" } });
    expect(screen.queryByText("MCP Pessoas")).toBeNull();
    fireEvent.change(screen.getByLabelText("Filtrar por destino"), { target: { value: "all" } });
    fireEvent.change(screen.getByLabelText("Filtrar por estado"), { target: { value: "enabled" } });
    expect(screen.getByText("MCP Planejamento")).not.toBeNull();
    expect(screen.queryByText("MCP Pessoas")).toBeNull();
    fireEvent.change(screen.getByLabelText("Filtrar por estado"), { target: { value: "disabled" } });
    expect(screen.queryByText("MCP Planejamento")).toBeNull();
    expect(screen.getByText("MCP Pessoas")).not.toBeNull();
    fireEvent.change(screen.getByLabelText("Filtrar por estado"), { target: { value: "all" } });

    fireEvent.click(screen.getByRole("button", { name: "Editar MCP Planejamento" }));
    expect((screen.getByLabelText("Nome") as HTMLInputElement).value).toBe("MCP Planejamento");
    expect((screen.getByLabelText("Destino") as HTMLSelectElement).value).toBe("claude");
  });

  it("distinguishes an empty registry from filters without matches", async () => {
    render(<McpConnectionsPage />);

    await screen.findByText("MCP Planejamento");
    fireEvent.change(screen.getByLabelText("Buscar conexões"), { target: { value: "inexistente" } });

    expect(screen.getByText("Nenhuma conexão corresponde aos filtros atuais.")).not.toBeNull();
    expect(screen.queryByText(/Cadastre o primeiro MCP/)).toBeNull();
  });

  it("shows persisted validation state and trusts an edited API response that clears it", async () => {
    const validatedConnection = { ...connection, last_validated_at: "2026-08-25T12:00:00Z" };
    configuredApi([validatedConnection]);
    api.updateMcpConnection.mockResolvedValue({
      ...validatedConnection,
      endpoint_url: "https://novo.example.com/mcp",
      last_validated_at: null,
    });
    render(<McpConnectionsPage />);

    const connectionCard = (await screen.findByText("MCP Planejamento")).closest("article");
    expect(connectionCard).not.toBeNull();
    expect(within(connectionCard as HTMLElement).getByText(/^Validada em /)).not.toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Editar MCP Planejamento" }));
    fireEvent.change(screen.getByLabelText("Endpoint MCP"), { target: { value: "https://novo.example.com/mcp" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar conexão" }));

    expect(await screen.findByText("https://novo.example.com/mcp")).not.toBeNull();
    expect(screen.getByText("Não validada")).not.toBeNull();
    expect(screen.queryByText(/^Validada em /)).toBeNull();
  });

  it("opens native form and deletion modals, handles cancel and close, and restores focus", async () => {
    render(<McpConnectionsPage />);
    await screen.findByText("MCP Planejamento");

    const createButton = screen.getByRole("button", { name: "Cadastrar MCP" });
    fireEvent.click(createButton);
    const formDialog = screen.getByRole("dialog", { name: "Cadastrar MCP" }) as HTMLDialogElement;
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalledTimes(1);
    expect(formDialog.open).toBe(true);

    fireEvent(formDialog, new Event("cancel", { cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Cadastrar MCP" })).toBeNull());
    expect(document.activeElement).toBe(createButton);

    fireEvent.click(createButton);
    const reopenedFormDialog = screen.getByRole("dialog", { name: "Cadastrar MCP" }) as HTMLDialogElement;
    reopenedFormDialog.close();
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Cadastrar MCP" })).toBeNull());
    expect(document.activeElement).toBe(createButton);

    const deleteButton = screen.getByRole("button", { name: "Excluir" });
    fireEvent.click(deleteButton);
    const deleteDialog = screen.getByRole("dialog", { name: "Excluir conexão MCP?" }) as HTMLDialogElement;
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalledTimes(3);

    fireEvent(deleteDialog, new Event("cancel", { cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Excluir conexão MCP?" })).toBeNull());
    expect(document.activeElement).toBe(deleteButton);
  });

  it("shows a recoverable load error and retries both resources", async () => {
    api.listMcpConnections
      .mockRejectedValueOnce(new Error("Falha temporária ao carregar."))
      .mockResolvedValueOnce([connection]);
    render(<McpConnectionsPage />);

    expect(await screen.findByText("Falha temporária ao carregar.")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    expect(await screen.findByText("MCP Planejamento")).not.toBeNull();
    expect(api.listMcpConnections).toHaveBeenCalledTimes(2);
    expect(api.getMcpToolCatalog).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).toBeNull();
  });

  it("explains login, blocks incomplete forms and shows structural validation errors", async () => {
    api.listMcpConnections.mockRejectedValue(new ApiError(401, "Sessão expirada"));
    render(<McpConnectionsPage />);
    expect(await screen.findByText(/entre para gerenciar/i)).not.toBeNull();

    cleanup();
    configuredApi();
    api.validateMcpConnection.mockRejectedValue(new ApiError(422, "Endpoint precisa de HTTPS"));
    render(<McpConnectionsPage />);
    await screen.findByRole("button", { name: "Cadastrar MCP" });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar MCP" }));
    fireEvent.click(screen.getByRole("button", { name: "Salvar conexão" }));
    expect(await screen.findByText(/preencha nome e endpoint/i)).not.toBeNull();
    expect(api.createMcpConnection).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    fireEvent.click(screen.getByRole("button", { name: "Validar configuração" }));
    expect(await screen.findByText("Endpoint precisa de HTTPS")).not.toBeNull();
  });

  it.each(["create", "edit", "validate", "toggle", "delete"] as const)(
    "transitions to login-required state when %s returns 401",
    async (operation) => {
      configuredApi();
      const unauthorized = new ApiError(401, "Sessão expirada");
      api.createMcpConnection.mockRejectedValue(unauthorized);
      api.updateMcpConnection.mockRejectedValue(unauthorized);
      api.validateMcpConnection.mockRejectedValue(unauthorized);
      api.deleteMcpConnection.mockRejectedValue(unauthorized);
      render(<McpConnectionsPage />);
      await screen.findByText("MCP Planejamento");

      if (operation === "create") {
        fireEvent.click(screen.getByRole("button", { name: "Cadastrar MCP" }));
        fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Novo MCP" } });
        fireEvent.change(screen.getByLabelText("Endpoint MCP"), { target: { value: "https://mcp.example.com/mcp" } });
        fireEvent.click(screen.getByRole("button", { name: "Salvar conexão" }));
      } else if (operation === "edit") {
        fireEvent.click(screen.getByRole("button", { name: "Editar MCP Planejamento" }));
        fireEvent.click(screen.getByRole("button", { name: "Salvar conexão" }));
      } else if (operation === "validate") {
        fireEvent.click(screen.getByRole("button", { name: "Validar configuração" }));
      } else if (operation === "toggle") {
        fireEvent.click(screen.getByRole("button", { name: "Desativar" }));
      } else {
        fireEvent.click(screen.getByRole("button", { name: "Excluir" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
      }

      expect(await screen.findByText("Entre para gerenciar suas conexões MCP.")).not.toBeNull();
      expect(screen.queryByRole("dialog")).toBeNull();
    },
  );
});
