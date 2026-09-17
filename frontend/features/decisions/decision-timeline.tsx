import type { DecisionRunTimelineView } from "@/lib/api";

const eventLabels: Record<string, string> = {
  "decision.run_completed": "Cenário calculado",
  "decision.selection_superseded": "Seleção anterior substituída",
  "decision.scenario_selected": "Cenário selecionado",
};

export function DecisionTimeline({ detail }: { detail: DecisionRunTimelineView | null }) {
  return (
    <section className="planner-panel" aria-labelledby="timeline-title">
      <header className="panel-header"><div><p className="eyebrow">Rastreabilidade</p><h2 id="timeline-title">Linha do tempo da decisão</h2></div></header>
      {!detail ? <p className="empty-state">Nenhum cenário calculado para auditar.</p> : (
        <ol className="decision-timeline">
          {detail.timeline.map((event, index) => (
            <li key={`${event.event_type}-${event.occurred_at}-${index}`}>
              <span aria-hidden="true" />
              <div><strong>{eventLabels[event.event_type] ?? event.event_type}</strong><time dateTime={event.occurred_at}>{new Date(event.occurred_at).toLocaleString("pt-BR")}</time><p>{event.actor_id ?? "sistema"}</p>{event.event_type === "decision.scenario_selected" && typeof event.payload.note === "string" ? <blockquote>{event.payload.note}</blockquote> : null}</div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
