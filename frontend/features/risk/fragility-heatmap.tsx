"use client";

import { useState } from "react";

import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import type { FragilityReportView } from "@/lib/api";

import { FragilityDetail } from "./fragility-detail";

type Cell = FragilityReportView["cells"][number];

const severityLabels = { low: "Baixo", medium: "Médio", high: "Alto", critical: "Crítico" } as const;
const severitySpoken = { low: "baixo", medium: "médio", high: "alto", critical: "crítico" } as const;
const severityTones = { low: "success", medium: "warning", high: "danger", critical: "danger" } as const;

function accessibleLabel(cell: Cell): string {
  return `${cell.operation_name}, ${cell.role_name}: risco ${severitySpoken[cell.risk.severity]}, cobertura ${cell.metric.eligible_count} de ${cell.metric.required_count}, redundância ${cell.metric.redundancy}`;
}

export function FragilityHeatmap({ report }: { report: FragilityReportView }) {
  const [selectedDemandId, setSelectedDemandId] = useState(report.cells[0]?.demand_id ?? null);
  const selected = report.cells.find((cell) => cell.demand_id === selectedDemandId) ?? null;
  return (
    <div className="fragility-layout">
      <section className="planner-panel fragility-map" aria-labelledby="fragility-map-title">
        <header className="panel-header"><div><p className="eyebrow">Mapa de cobertura</p><h2 id="fragility-map-title">Fragilidade por operação e cargo</h2></div><span className="runtime-label">{report.cells.length} demandas</span></header>
        {report.cells.length ? (
          <DataTable ariaLabel="Mapa de fragilidade por operação e cargo">
            <thead><tr><th scope="col">Operação</th><th scope="col">Cargo / turno</th><th scope="col">Cobertura</th><th scope="col">Redundância</th><th scope="col">Treináveis</th><th scope="col">Risco</th></tr></thead>
            <tbody>
              {report.cells.map((cell) => (
                <tr key={cell.demand_id}>
                  <td>{cell.operation_name}<span className="cell-detail">mobilização {new Date(cell.mobilization_deadline).toLocaleDateString("pt-BR")}</span></td>
                  <td>{cell.role_name}<span className="cell-detail">{cell.shift_code}</span></td>
                  <td>{cell.metric.eligible_count} / {cell.metric.required_count}</td>
                  <td>{cell.metric.redundancy}</td>
                  <td>{cell.metric.trainable_count}</td>
                  <td>
                    <button aria-label={accessibleLabel(cell)} aria-pressed={selectedDemandId === cell.demand_id} className={`risk-cell risk-cell-${cell.risk.severity}`} onClick={() => setSelectedDemandId(cell.demand_id)} title={cell.risk.explanations.map((item) => item.message).join(" ")} type="button">
                      <StatusBadge tone={severityTones[cell.risk.severity]}>{severityLabels[cell.risk.severity]}</StatusBadge>
                      <span>{cell.risk.reason_codes.length ? `${cell.risk.reason_codes.length} alerta(s)` : "sem alertas"}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
        ) : <p className="empty-state">Nenhuma demanda futura encontrada neste horizonte.</p>}
      </section>
      <FragilityDetail cell={selected} />
    </div>
  );
}
