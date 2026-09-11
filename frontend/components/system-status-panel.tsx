import type { SystemStatus } from "@/types/system-status";

interface SystemStatusPanelProps {
  statuses: readonly SystemStatus[];
}

export function SystemStatusPanel({ statuses }: SystemStatusPanelProps) {
  return (
    <section className="status-panel" aria-labelledby="system-status-title">
      <h2 id="system-status-title">System Status</h2>
      <ul className="status-list">
        {statuses.map((status) => (
          <li className="status-row" key={status.service}>
            <span className="service-name">{status.service}</span>
            <span className="service-state">
              <span className="status-check" aria-hidden="true">✓</span>
              {status.label}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
