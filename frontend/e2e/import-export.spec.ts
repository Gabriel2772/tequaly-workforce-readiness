import path from "node:path";

import { expect, test } from "@playwright/test";

import { projectRoot } from "../playwright.config";

test("valida, confirma e exporta dados canônicos", async ({ page }) => {
  await page.goto("/configuracoes", { waitUntil: "domcontentloaded" });

  await expect(page.getByRole("heading", { name: "Higiene de dados" })).toBeVisible();
  await page.getByLabel("Arquivo").setInputFiles(path.join(projectRoot, "samples", "employees.csv"));
  await page.getByRole("button", { name: "Gerar preview" }).click();
  await expect(page.getByRole("status")).toContainText("Preview validado");
  await expect(page.getByLabel("Resumo do preview").getByText("2", { exact: true })).toHaveCount(2);

  await page.getByLabel(/Confirmo o mapeamento/).check();
  await page.getByRole("button", { name: "Confirmar importação" }).click();
  await expect(page.getByRole("status")).toContainText("2 criado(s)");

  const employeeExport = page.locator(".export-card").filter({ hasText: "Colaboradores" });
  const downloadPromise = page.waitForEvent("download");
  await employeeExport.getByRole("button", { name: "CSV" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/^twr-employees.*\.csv$/);
});
