import { expect, test } from "@playwright/test";

test("fecha o ciclo entre planejamento, risco, resultado e calibração", async ({ page }) => {
  await page.goto("/planejador", { waitUntil: "domcontentloaded" });

  const demonstrableOperationId = await page
    .getByLabel("Operação ativa")
    .locator("option")
    .last()
    .getAttribute("value");
  if (!demonstrableOperationId) throw new Error("Nenhuma operação demonstrável foi encontrada.");
  await page.getByLabel("Operação ativa").selectOption(demonstrableOperationId);
  await page.getByRole("button", { name: "Carregar" }).click();
  await expect(page).toHaveURL(new RegExp(`operation=${demonstrableOperationId}`));

  await page.getByRole("button", { name: "Recalcular elegibilidade" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Elegibilidade recalculada" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Plano de capacitação operacional" }),
  ).toBeVisible();

  await page.getByLabel("Objetivo").selectOption("MIN_COST");
  await page.getByRole("button", { name: "Gerar cenário" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Cenário calculado" })).toBeVisible();

  await page.goto("/risco-e-cobertura", { waitUntil: "domcontentloaded" });
  await expect(
    page.getByRole("heading", { name: "Fragilidade por operação e cargo" }),
  ).toBeVisible();
  await expect(
    page.getByRole("table", { name: "Mapa de fragilidade por operação e cargo" }),
  ).toBeVisible();

  await page.goto("/auditoria", { waitUntil: "domcontentloaded" });
  const newestScenario = page.locator(".selection-card").first();
  await newestScenario.getByLabel("Justificativa da escolha").fill(
    "Cenário selecionado para validar o fluxo operacional demonstrativo.",
  );
  await newestScenario
    .getByLabel("Confirmo que revisei as métricas previstas")
    .check();
  await newestScenario.getByRole("button", { name: "Selecionar cenário" }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Cenário selecionado e auditado" }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Registrar resultado real" })).toBeVisible();

  await page.getByLabel("Custo realizado (R$)").fill("340");
  await page.getByLabel("Prontidão real").fill("2026-09-24T08:00");
  await page.getByLabel("Parâmetro de calibração").selectOption("training_cost_cents");
  await page.getByLabel("Categoria da observação").fill("seguranca");
  await page.getByLabel("Valor observado").fill("340");
  await page.getByRole("button", { name: "Registrar resultado" }).click();
  await expect(page.getByRole("heading", { name: "Previsto versus realizado" })).toBeVisible();

  const calibration = page.locator(".calibration-panel");
  await calibration.getByLabel("Categoria").fill("seguranca");
  await calibration.getByRole("button", { name: "Gerar sugestão" }).click();
  await expect(calibration.getByText("6 observações")).toBeVisible();
  await expect(calibration.getByText("R$ 325,00")).toBeVisible();
  await calibration.getByLabel(/Confirmo a aplicação deste parâmetro/).check();
  await calibration.getByRole("button", { name: "Aplicar parâmetro" }).click();
  await expect(calibration.getByRole("status")).toContainText("Versão v2 aplicada");
});
