import type { AgentAdapterInfo } from "../../../shared/types";

export function AgentsPanel({ agents }: { agents: AgentAdapterInfo[] }) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Agents</h2>
      </div>
      <p className="muted">
        Phase 1 registers FakeAgentAdapter only. Real CLI adapters arrive in Phase 2+.
      </p>
      <ul className="status-list">
        {agents.map((agent) => (
          <li key={agent.id}>
            <strong>{agent.displayName}</strong>{" "}
            <code>
              {agent.id} · {agent.status}
            </code>
          </li>
        ))}
      </ul>
    </section>
  );
}
