import type { ReactNode } from "react";

export type NavigationIconName =
  | "overview"
  | "people"
  | "qualification"
  | "operations"
  | "planner"
  | "training"
  | "risk"
  | "audit"
  | "settings"
  | "mcp";

const glyphs: Record<NavigationIconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="4" rx="1.5" />
      <rect x="14" y="11" width="7" height="10" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  people: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 19c.6-3.2 2.4-5 5.5-5s4.9 1.8 5.5 5" />
      <path d="M15.5 5.5a3 3 0 0 1 0 5.5M16 14c2.6.2 4 1.9 4.5 4.5" />
    </>
  ),
  qualification: (
    <>
      <path d="M6 3.5h9l3 3V14" />
      <path d="M15 3.5V7h3M6 3.5v17h7" />
      <circle cx="17" cy="17" r="3.5" />
      <path d="m15.5 20-.5 2 2-1 2 1-.5-2" />
      <path d="M9 9h5M9 12h3" />
    </>
  ),
  operations: (
    <>
      <path d="M4 10h16v9H4zM8 10V7h8v3" />
      <path d="M3 13.5h7v2h4v-2h7M12 13.5v2" />
    </>
  ),
  planner: (
    <>
      <rect x="3" y="4.5" width="18" height="16" rx="2" />
      <path d="M7 2.5v4M17 2.5v4M3 9h18" />
      <path d="m8 15 2.2 2 5-5" />
    </>
  ),
  training: (
    <>
      <path d="M4 5.5c3-.8 5.7-.2 8 1.5v13c-2.3-1.7-5-2.3-8-1.5z" />
      <path d="M20 5.5c-3-.8-5.7-.2-8 1.5v13c2.3-1.7 5-2.3 8-1.5z" />
      <path d="M12 7v13" />
    </>
  ),
  risk: (
    <>
      <path d="M12 3 20 6v5.5c0 4.8-3.2 8-8 9.5-4.8-1.5-8-4.7-8-9.5V6z" />
      <path d="M12 8v5M12 17h.01" />
    </>
  ),
  audit: (
    <>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4V2.5h6V4M8.5 9h7M8.5 13h3" />
      <path d="m13.5 16 1.5 1.5 3-3" />
    </>
  ),
  settings: (
    <>
      <path d="M4 6h7M15 6h5M4 12h3M11 12h9M4 18h10M18 18h2" />
      <circle cx="13" cy="6" r="2" />
      <circle cx="9" cy="12" r="2" />
      <circle cx="16" cy="18" r="2" />
    </>
  ),
  mcp: (
    <>
      <circle cx="5" cy="7" r="2" />
      <circle cx="19" cy="7" r="2" />
      <circle cx="12" cy="20" r="2" />
      <path d="M7 7h2M15 7h2M12 14v4" />
      <path d="M9 5v5a3 3 0 0 0 6 0V5M12 13v1" />
    </>
  ),
};

export function NavigationIcon({ name }: { name: NavigationIconName }) {
  return (
    <svg
      aria-hidden="true"
      className="nav-icon"
      fill="none"
      focusable="false"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.9"
      viewBox="0 0 24 24"
    >
      {glyphs[name]}
    </svg>
  );
}
