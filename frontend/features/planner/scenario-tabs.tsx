"use client";

type ScenarioTab = { id: string; label: string };

export function ScenarioTabs({ tabs, selectedId, onSelect }: { tabs: ScenarioTab[]; selectedId: string; onSelect: (id: string) => void }) {
  return (
    <div className="scenario-tabs" role="tablist" aria-label="Cenários de otimização">
      {tabs.map((tab) => (
        <button
          aria-controls={`scenario-panel-${tab.id}`}
          aria-selected={selectedId === tab.id}
          id={`scenario-tab-${tab.id}`}
          key={tab.id}
          onClick={() => onSelect(tab.id)}
          role="tab"
          tabIndex={selectedId === tab.id ? 0 : -1}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
