export function TerminalPlaceholder() {
  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Terminal</h2>
      </div>
      <p className="muted">
        Managed interactive terminals via node-pty are deferred to Phase 2. The renderer
        will never spawn shells directly.
      </p>
    </section>
  );
}
