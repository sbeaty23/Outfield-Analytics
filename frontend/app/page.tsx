import { SystemStatusPanel } from "@/components/system-status-panel";

export default function Home() {
  return (
    <main className="page-shell">
      <section className="diagnostic-card" aria-labelledby="page-title">
        <header className="brand-block">
          <div className="brand-mark" aria-hidden="true">
            <span />
          </div>
          <div>
            <p className="eyebrow">Baseball intelligence platform</p>
            <h1 id="page-title">Outfield Analytics</h1>
          </div>
        </header>

        <p className="intro">Baseball analytics and predictive modeling.</p>

        <SystemStatusPanel />
      </section>
    </main>
  );
}
