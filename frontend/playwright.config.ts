import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(frontendRoot, "..");
const backendRoot = path.join(projectRoot, "backend");
const python = path.join(backendRoot, ".venv", "Scripts", "python.exe");
const databasePath = path.join(frontendRoot, ".e2e", "twr-e2e.db").replaceAll("\\", "/");
const databaseUrl = `sqlite:///${databasePath}`;
const backendPort = Number(process.env.TWR_E2E_BACKEND_PORT ?? 8000);
const frontendPort = Number(process.env.TWR_E2E_FRONTEND_PORT ?? 3000);
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}`;

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: frontendUrl,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "Microsoft Edge",
      use: { ...devices["Desktop Chrome"], channel: "msedge" },
    },
  ],
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port ${backendPort}`,
      cwd: backendRoot,
      env: {
        TWR_DATABASE_URL: databaseUrl,
        TWR_FRONTEND_ORIGIN: frontendUrl,
      },
      url: `${backendUrl}/health`,
      reuseExistingServer: false,
      stdout: "pipe",
      timeout: 60_000,
    },
    {
      command: `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port ${frontendPort}`,
      cwd: frontendRoot,
      env: { TWR_API_URL: backendUrl },
      url: `${frontendUrl}/health`,
      reuseExistingServer: false,
      stdout: "pipe",
      timeout: 60_000,
    },
  ],
});

export { backendRoot, databaseUrl, projectRoot, python };
