import { expect, test } from "@playwright/test";

test("inicia e encerra uma sessão assinada", async ({ page }) => {
  await page.goto("/entrar", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Entrar no Workforce Readiness" })).toBeVisible();
  await page.getByLabel("Usuário").fill("admin.demo");
  await page.getByLabel("Senha").fill("TequalyDemo!2026");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText("Administrador de demonstração")).toBeVisible();
  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page.getByRole("link", { name: "Entrar" })).toBeVisible();
});
