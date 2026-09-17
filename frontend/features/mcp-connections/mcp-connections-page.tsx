"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  ApiError,
  createMcpConnection,
  deleteMcpConnection,
  getMcpToolCatalog,
  listMcpConnections,
  updateMcpConnection,
  validateMcpConnection,
} from "@/lib/api";
import type { McpClientType, McpConnection, McpConnectionInput, McpTool, McpTransport } from "@/lib/api";

type FormValues = {
  name: string;
  client_type: McpClientType;
  endpoint_url: string;
  transport: McpTransport;
  notes: string;
};

const emptyForm: FormValues = {
  name: "",
  client_type: "claude",
  endpoint_url: "",
  transport: "streamable_http",
  notes: "",
};

function formValues(connection: McpConnection): FormValues {
  return {
    name: connection.name,
    client_type: connection.client_type,
    endpoint_url: connection.endpoint_url,
    transport: connection.transport,
    notes: connection.notes ?? "",
  };
}

export function connectionGuide(connection: McpConnection): string {
  return JSON.stringify({
    name: connection.name,
    url: connection.endpoint_url,
    transport: connection.transport === "streamable_http" ? "streamable-http" : "sse",
  }, null, 2);
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

function destinationLabel(destination: McpClientType): string {
  return destination === "claude" ? "Claude" : "ChatGPT";
}

function validationLabel(lastValidatedAt: string | null): string {
  if (!lastValidatedAt) return "Não validada";
  const formattedDate = new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(lastValidatedAt));
  return `Validada em ${formattedDate}`;
}

export function McpConnectionsPage() {
  const [connections, setConnections] = useState<McpConnection[]>([]);
  const [catalog, setCatalog] = useState<McpTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [requiresLogin, setRequiresLogin] = useState(false);
  const [query, setQuery] = useState("");
  const [destinationFilter, setDestinationFilter] = useState<"all" | McpClientType>("all");
  const [stateFilter, setStateFilter] = useState<"all" | "enabled" | "disabled">("all");
  const [editing, setEditing] = useState<McpConnection | null | undefined>(undefined);
  const [deleting, setDeleting] = useState<McpConnection | null>(null);
  const [form, setForm] = useState<FormValues>(emptyForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [saving, setSaving] = useState(false);
  const formDialogRef = useRef<HTMLDialogElement>(null);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
  const formTriggerRef = useRef<HTMLElement | null>(null);
  const deleteTriggerRef = useRef<HTMLElement | null>(null);

  function handleMutationError(error: unknown): boolean {
    if (!(error instanceof ApiError) || error.status !== 401) return false;
    setRequiresLogin(true);
    setLoadError(null);
    setLoading(false);
    setEditing(undefined);
    setDeleting(null);
    setFormError(null);
    setForm(emptyForm);
    setSaving(false);
    setNotice("");
    return true;
  }

  async function load() {
    setLoading(true);
    setLoadError(null);
    setRequiresLogin(false);
    try {
      const [savedConnections, savedCatalog] = await Promise.all([
        listMcpConnections(),
        getMcpToolCatalog(),
      ]);
      setConnections(savedConnections);
      setCatalog(savedCatalog);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setRequiresLogin(true);
      } else {
        setLoadError(errorMessage(error, "Não foi possível carregar as conexões MCP."));
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const initialLoad = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(initialLoad);
  }, []);

  useEffect(() => {
    const dialog = formDialogRef.current;
    if (editing !== undefined && dialog && !dialog.open) dialog.showModal();
  }, [editing]);

  useEffect(() => {
    const dialog = deleteDialogRef.current;
    if (deleting && dialog && !dialog.open) dialog.showModal();
  }, [deleting]);

  const visibleConnections = useMemo(() => connections.filter((connection) => {
    const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");
    const matchesQuery = !normalizedQuery
      || connection.name.toLocaleLowerCase("pt-BR").includes(normalizedQuery)
      || connection.endpoint_url.toLocaleLowerCase("pt-BR").includes(normalizedQuery);
    const matchesDestination = destinationFilter === "all" || connection.client_type === destinationFilter;
    const matchesState = stateFilter === "all"
      || (stateFilter === "enabled" ? connection.enabled : !connection.enabled);
    return matchesQuery && matchesDestination && matchesState;
  }), [connections, destinationFilter, query, stateFilter]);

  function openCreate(event: React.MouseEvent<HTMLButtonElement>) {
    formTriggerRef.current = event.currentTarget;
    setEditing(null);
    setForm(emptyForm);
    setFormError(null);
  }

  function openEdit(event: React.MouseEvent<HTMLButtonElement>, connection: McpConnection) {
    formTriggerRef.current = event.currentTarget;
    setEditing(connection);
    setForm(formValues(connection));
    setFormError(null);
  }

  function finishFormClose() {
    setEditing(undefined);
    setFormError(null);
    formTriggerRef.current?.focus();
  }

  function closeDialog() {
    const dialog = formDialogRef.current;
    if (dialog?.open) dialog.close();
    finishFormClose();
  }

  function finishDeleteClose() {
    setDeleting(null);
    deleteTriggerRef.current?.focus();
  }

  function closeDeleteDialog() {
    const dialog = deleteDialogRef.current;
    if (dialog?.open) dialog.close();
    finishDeleteClose();
  }

  async function saveConnection(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = form.name.trim();
    const endpointUrl = form.endpoint_url.trim();
    if (!name || !endpointUrl) {
      setFormError("Preencha nome e endpoint antes de salvar.");
      return;
    }
    const payload: McpConnectionInput = {
      name,
      client_type: form.client_type,
      endpoint_url: endpointUrl,
      transport: form.transport,
      notes: form.notes.trim() || null,
    };
    setSaving(true);
    setFormError(null);
    try {
      const result = editing
        ? await updateMcpConnection(editing.id, payload)
        : await createMcpConnection(payload);
      setConnections((current) => editing
        ? current.map((connection) => connection.id === result.id ? result : connection)
        : [result, ...current]);
      setNotice(editing ? "Conexão atualizada." : "Conexão cadastrada.");
      closeDialog();
    } catch (error) {
      if (handleMutationError(error)) return;
      setFormError(errorMessage(error, "Não foi possível salvar a conexão."));
    } finally {
      setSaving(false);
    }
  }

  async function validateConnection(connection: McpConnection) {
    try {
      const validation = await validateMcpConnection(connection.id);
      setConnections((current) => current.map((item) => item.id === connection.id
        ? { ...item, endpoint_url: validation.normalized_endpoint_url, last_validated_at: validation.validated_at }
        : item));
      setNotice("Configuração válida");
    } catch (error) {
      if (handleMutationError(error)) return;
      setNotice(errorMessage(error, "A configuração precisa de correção."));
    }
  }

  async function copyConnection(connection: McpConnection) {
    try {
      await navigator.clipboard.writeText(connectionGuide(connection));
      setNotice("Configuração copiada sem segredos.");
    } catch {
      setNotice("Não foi possível copiar a configuração neste navegador.");
    }
  }

  async function toggleConnection(connection: McpConnection) {
    try {
      const result = await updateMcpConnection(connection.id, { enabled: !connection.enabled });
      setConnections((current) => current.map((item) => item.id === result.id ? result : item));
      setNotice(result.enabled ? "Conexão ativada." : "Conexão desativada.");
    } catch (error) {
      if (handleMutationError(error)) return;
      setNotice(errorMessage(error, "Não foi possível alterar o estado da conexão."));
    }
  }

  async function confirmDelete() {
    if (!deleting) return;
    try {
      await deleteMcpConnection(deleting.id);
      const dialog = deleteDialogRef.current;
      if (dialog?.open) dialog.close();
      setConnections((current) => current.filter((connection) => connection.id !== deleting.id));
      setNotice("Conexão excluída.");
      setDeleting(null);
      createButtonRef.current?.focus();
    } catch (error) {
      if (handleMutationError(error)) return;
      setNotice(errorMessage(error, "Não foi possível excluir a conexão."));
    }
  }

  return (
    <main className="workspace-page mcp-connections-page">
      <header className="page-header mcp-page-header">
        <div>
          <p className="eyebrow">Configurações individuais</p>
          <h1>Conexões MCP</h1>
          <p className="page-summary">Organize configurações MCP sem segredos. O TWR não hospeda conversas nem executa modelos de IA.</p>
        </div>
        <button className="primary-action" onClick={openCreate} ref={createButtonRef} type="button">Cadastrar MCP</button>
      </header>

      <p aria-live="polite" className="mcp-notice" role="status">{notice}</p>

      <section aria-label="Disponibilidade por destino" className="mcp-provider-grid">
        <article className="mcp-provider-card">
          <p className="eyebrow">Destino</p>
          <h2>Claude</h2>
          <p>Compatível com conectores MCP remotos, respeitando as regras do plano do usuário e da organização.</p>
          <small>O conector é configurado externamente; o TWR não inicia sessão nem instala integrações.</small>
        </article>
        <article className="mcp-provider-card">
          <p className="eyebrow">Destino</p>
          <h2>ChatGPT</h2>
          <p>A disponibilidade de apps MCP pode depender do plano e das permissões do workspace.</p>
          <small>Confirme com o administrador antes de importar a configuração no cliente externo.</small>
        </article>
      </section>

      <section aria-labelledby="mcp-instructions-title" className="planner-panel mcp-instructions">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Próximos passos</p>
            <h2 id="mcp-instructions-title">Como levar uma conexão ao cliente</h2>
            <p className="panel-summary">O cadastro organiza metadados; a configuração final acontece no cliente escolhido.</p>
          </div>
        </header>
        <ol>
          <li><strong>Cadastre</strong><span>Informe um nome, destino, endpoint HTTPS e transporte compatível.</span></li>
          <li><strong>Valide e copie</strong><span>Use a validação estrutural e copie o guia sem segredos.</span></li>
          <li><strong>Configure no destino</strong><span>Adicione a URL no Claude ou ChatGPT conforme o plano e as permissões da sua organização.</span></li>
        </ol>
        <p className="mcp-local-note">Em desenvolvimento, localhost pode ser aceito pelo TWR; clientes em nuvem normalmente exigem um endpoint HTTPS público.</p>
      </section>

      <section className="planner-panel mcp-connections-panel" aria-labelledby="mcp-list-title">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Cadastro</p>
            <h2 id="mcp-list-title">Suas conexões</h2>
            <p className="panel-summary">A validação é estrutural e não acessa o endpoint remoto.</p>
          </div>
        </header>
        <div className="mcp-filters">
          <label>Buscar conexões
            <input onChange={(event) => setQuery(event.target.value)} value={query} />
          </label>
          <label>Filtrar por destino
            <select onChange={(event) => setDestinationFilter(event.target.value as "all" | McpClientType)} value={destinationFilter}>
              <option value="all">Todos os destinos</option>
              <option value="claude">Claude</option>
              <option value="chatgpt">ChatGPT</option>
            </select>
          </label>
          <label>Filtrar por estado
            <select onChange={(event) => setStateFilter(event.target.value as "all" | "enabled" | "disabled")} value={stateFilter}>
              <option value="all">Todos os estados</option>
              <option value="enabled">Ativas</option>
              <option value="disabled">Inativas</option>
            </select>
          </label>
        </div>

        {loading ? <p className="empty-state">Carregando conexões MCP…</p> : null}
        {requiresLogin ? <p className="mcp-error" role="alert">Entre para gerenciar suas conexões MCP.</p> : null}
        {loadError ? <div className="mcp-error" role="alert"><p>{loadError}</p><button onClick={() => void load()} type="button">Tentar novamente</button></div> : null}
        {!loading && !requiresLogin && !loadError && connections.length === 0 ? <p className="empty-state">Nenhuma conexão cadastrada. Cadastre o primeiro MCP para organizar sua configuração.</p> : null}
        {!loading && !requiresLogin && !loadError && connections.length > 0 && visibleConnections.length === 0 ? <p className="empty-state">Nenhuma conexão corresponde aos filtros atuais.</p> : null}
        {!loading && !requiresLogin && !loadError ? <div className="mcp-connection-list">
          {visibleConnections.map((connection) => <article className="mcp-connection-card" key={connection.id}>
            <header><div><span className={`mcp-state ${connection.enabled ? "mcp-state-enabled" : "mcp-state-disabled"}`}>{connection.enabled ? "Ativa" : "Inativa"}</span><h3>{connection.name}</h3></div><span>{destinationLabel(connection.client_type)}</span></header>
            <dl><div><dt>Endpoint</dt><dd>{connection.endpoint_url}</dd></div><div><dt>Transporte</dt><dd>{connection.transport === "streamable_http" ? "Streamable HTTP" : "SSE"}</dd></div><div><dt>Validação</dt><dd>{validationLabel(connection.last_validated_at)}</dd></div></dl>
            {connection.notes ? <p>{connection.notes}</p> : null}
            <div className="mcp-card-actions">
              <button onClick={() => void validateConnection(connection)} type="button">Validar configuração</button>
              <button onClick={() => void copyConnection(connection)} type="button">Copiar configuração</button>
              <button aria-label={`Editar ${connection.name}`} onClick={(event) => openEdit(event, connection)} type="button">Editar</button>
              <button onClick={() => void toggleConnection(connection)} type="button">{connection.enabled ? "Desativar" : "Ativar"}</button>
              <button className="danger-action" onClick={(event) => { deleteTriggerRef.current = event.currentTarget; setDeleting(connection); }} type="button">Excluir</button>
            </div>
          </article>)}
        </div> : null}
      </section>

      <section className="planner-panel mcp-catalog" aria-labelledby="mcp-catalog-title">
        <header className="panel-header"><div><p className="eyebrow">Catálogo local</p><h2 id="mcp-catalog-title">Ferramentas MCP do TWR</h2></div></header>
        {catalog.length > 0 ? <ul>{catalog.map((tool) => <li key={tool.name}><strong>{tool.name}</strong><span>{tool.description}</span><small>Somente leitura</small></li>)}</ul> : <p className="empty-state">Nenhuma ferramenta local disponível.</p>}
      </section>

      {editing !== undefined ? <dialog aria-labelledby="mcp-form-title" className="mcp-dialog" onCancel={(event) => { event.preventDefault(); closeDialog(); }} onClose={finishFormClose} ref={formDialogRef}>
        <form onSubmit={(event) => void saveConnection(event)}>
          <header><div><p className="eyebrow">{editing ? "Editar" : "Novo cadastro"}</p><h2 id="mcp-form-title">{editing ? "Editar conexão MCP" : "Cadastrar MCP"}</h2></div></header>
          <label>Nome<input maxLength={120} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} value={form.name} /></label>
          <label>Destino<select onChange={(event) => setForm((current) => ({ ...current, client_type: event.target.value as McpClientType }))} value={form.client_type}><option value="claude">Claude</option><option value="chatgpt">ChatGPT</option></select></label>
          <label>Endpoint MCP<input inputMode="url" maxLength={2048} onChange={(event) => setForm((current) => ({ ...current, endpoint_url: event.target.value }))} value={form.endpoint_url} /></label>
          <label>Transporte<select onChange={(event) => setForm((current) => ({ ...current, transport: event.target.value as McpTransport }))} value={form.transport}><option value="streamable_http">Streamable HTTP</option><option value="sse">SSE</option></select></label>
          <label>Observações<textarea maxLength={1000} onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))} value={form.notes} /></label>
          {formError ? <p className="mcp-error" role="alert">{formError}</p> : null}
          <footer><button onClick={closeDialog} type="button">Cancelar</button><button className="primary-action" disabled={saving} type="submit">{saving ? "Salvando…" : "Salvar conexão"}</button></footer>
        </form>
      </dialog> : null}

      {deleting ? <dialog aria-labelledby="mcp-delete-title" className="mcp-dialog" onCancel={(event) => { event.preventDefault(); closeDeleteDialog(); }} onClose={finishDeleteClose} ref={deleteDialogRef}>
        <div><h2 id="mcp-delete-title">Excluir conexão MCP?</h2><p>A exclusão de “{deleting.name}” remove somente este cadastro local.</p><footer><button onClick={closeDeleteDialog} type="button">Cancelar</button><button className="danger-action" onClick={() => void confirmDelete()} type="button">Confirmar exclusão</button></footer></div>
      </dialog> : null}
    </main>
  );
}
