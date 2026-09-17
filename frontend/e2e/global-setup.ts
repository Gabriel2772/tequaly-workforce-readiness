import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync } from "node:fs";
import path from "node:path";

import { backendRoot, databaseUrl, python, projectRoot } from "../playwright.config";

export default function globalSetup() {
  const databaseFile = databaseUrl.replace("sqlite:///", "");
  mkdirSync(path.dirname(databaseFile), { recursive: true });
  rmSync(databaseFile, { force: true });

  const env = { ...process.env, TWR_DATABASE_URL: databaseUrl };
  execFileSync(python, ["-m", "alembic", "upgrade", "head"], {
    cwd: backendRoot,
    env,
    stdio: "inherit",
  });
  execFileSync(python, [path.join(projectRoot, "scripts", "seed_demo.py"), "--employees", "300"], {
    cwd: backendRoot,
    env,
    stdio: "inherit",
  });
}
