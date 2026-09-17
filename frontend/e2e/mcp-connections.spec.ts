import { expect, test, type Page } from "@playwright/test";

async function loginAsPlanner(page: Page) {
  await page.goto("/entrar", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Entrar no Workforce Readiness" })).toBeVisible();
  await page.getByLabel("Usuário").fill("planner.demo");
  await page.getByLabel("Senha").fill("TequalyDemo!2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
}

test("user manages a Claude MCP connection", async ({ page }) => {
  await loginAsPlanner(page);
  await page.getByRole("link", { name: "Conexões MCP" }).click();
  await expect(page).toHaveURL(/\/conexoes-mcp$/);
  await expect(page.getByText("Nenhuma conexão cadastrada")).toBeVisible();

  await page.getByRole("button", { name: "Cadastrar MCP" }).click();
  const formDialog = page.getByRole("dialog", { name: "Cadastrar MCP" });
  await formDialog.getByLabel("Nome").fill("MCP Planejamento");
  await formDialog.getByLabel("Destino").selectOption("claude");
  await formDialog.getByLabel("Endpoint MCP").fill("https://mcp.example.com/mcp");
  await formDialog.getByRole("button", { name: "Salvar conexão" }).click();

  await expect(page.getByRole("heading", { name: "MCP Planejamento" })).toBeVisible();
  await page.getByRole("button", { name: "Validar configuração" }).click();
  await expect(page.getByText("Configuração válida")).toBeVisible();
  await page.getByRole("button", { name: "Desativar" }).click();
  await expect(page.getByRole("button", { name: "Ativar" })).toBeVisible();
  await page.getByRole("button", { name: "Ativar" }).click();
  await expect(page.getByRole("button", { name: "Desativar" })).toBeVisible();
  await page.getByRole("button", { name: "Excluir" }).click();
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  await expect(page.getByText("Nenhuma conexão cadastrada")).toBeVisible();
});

test("mobile navigation reaches the MCP registry and closes its drawer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await loginAsPlanner(page);

  const openMenu = page.getByRole("button", { name: "Abrir menu principal" });
  await expect(openMenu).toBeVisible();
  await openMenu.click();
  await expect(page.getByRole("button", { name: "Fechar menu principal" }).first()).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await page.getByRole("link", { name: "Conexões MCP" }).click();

  await expect(page).toHaveURL(/\/conexoes-mcp$/);
  await expect(page.getByRole("heading", { level: 1, name: "Conexões MCP" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Abrir menu principal" })).toHaveAttribute(
    "aria-expanded",
    "false",
  );
});
