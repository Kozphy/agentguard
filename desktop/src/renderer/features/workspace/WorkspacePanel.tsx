import type { GitStatusSnapshot, WorkspaceInfo } from "../../../shared/types";

interface WorkspacePanelProps {
  workspace: WorkspaceInfo | null;
  status: GitStatusSnapshot | null;
  busy: boolean;
  onOpen: () => void;
  onRefresh: () => void;
}

export function WorkspacePanel({
  workspace,
  status,
  busy,
  onOpen,
  onRefresh,
}: WorkspacePanelProps) {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Workspace</h2>
        <div className="actions">
          <button type="button" onClick={onOpen} disabled={busy}>
            Open repository
          </button>
          <button type="button" onClick={onRefresh} disabled={busy || !workspace}>
            Refresh status
          </button>
        </div>
      </div>

      {!workspace ? (
        <p className="muted">No repository selected.</p>
      ) : (
        <>
          <p>
            <strong>Path:</strong> <code>{workspace.path}</code>
          </p>
          <p>
            <strong>Branch:</strong>{" "}
            <code>{status?.branch ?? "(unknown)"}</code>
          </p>
          <p>
            <strong>Working tree:</strong>{" "}
            {status ? (status.clean ? "clean" : `${status.entries.length} changed`) : "—"}
          </p>
          {status && !status.clean ? (
            <ul className="status-list">
              {status.entries.map((entry) => (
                <li key={`${entry.code}:${entry.path}`}>
                  <code>{entry.code}</code> {entry.path}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      )}
    </section>
  );
}
