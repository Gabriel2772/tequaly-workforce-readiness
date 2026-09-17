import type { ReactNode } from "react";

export function DataTable({ ariaLabel, children }: { ariaLabel: string; children: ReactNode }) {
  return (
    <div className="table-frame table-frame-contained">
      <table aria-label={ariaLabel} className="data-table">{children}</table>
    </div>
  );
}
