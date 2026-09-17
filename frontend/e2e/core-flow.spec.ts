import { expect, test } from "@playwright/test";

test("calcula elegibilidade e compara os três cenários", async ({ page }) => {
  await page.goto("/planejador", { waitUntil: "domcontentloaded" });

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Recalcular elegibilidade" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Elegibilidade recalculada" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Elegibilidade determinística" })).toBeVisible();

  const objectives = [
    { value: "MIN_COST", label: "Menor custo" },
    { value: "FASTEST_READY", label: "Mais rápido" },
    { value: "MAX_INTERNAL", label: "Aproveitamento interno" },
  ];

  for (const objective of objectives) {
    await page.getByLabel("Objetivo").selectOption(objective.value);
    await page.getByRole("button", { name: "Gerar cenário" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Cenário calculado" })).toBeVisible();
    await expect(page.getByRole("tab", { name: objective.label })).toBeVisible();
  }

  await expect(page.getByRole("tablist", { name: "Cenários de otimização" }).getByRole("tab")).toHaveCount(3);
  await expect(page.getByRole("heading", { name: "Equipe proposta" })).toBeVisible();
});
