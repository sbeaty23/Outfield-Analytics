"use client";

import { useEffect, useRef, useState } from "react";
import { getSystemStatus, initialStatuses } from "@/lib/api";
import type { SystemStatus } from "@/types/system-status";

const icons = { healthy: "✓", loading: "…", unhealthy: "!", unknown: "?" };

export function SystemStatusPanel() {
  const [statuses, setStatuses] =
    useState<readonly SystemStatus[]>(initialStatuses);
  const request = useRef<AbortController | null>(null);
  const checking = statuses.some((status) => status.state === "loading");

  useEffect(() => {
    const controller = new AbortController();
    request.current = controller;
    void getSystemStatus(controller.signal).then((result) => {
      if (!controller.signal.aborted) setStatuses(result);
    });
    return () => {
      request.current?.abort();
    };
  }, []);

  async function refresh() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setStatuses(initialStatuses);
    const result = await getSystemStatus(controller.signal);
    if (!controller.signal.aborted) setStatuses(result);
  }

  return (
    <section className="status-panel" aria-labelledby="system-status-title">
      <div className="status-heading">
        <h2 id="system-status-title">System Status</h2>
        <button
          className="status-refresh"
          type="button"
          disabled={checking}
          onClick={refresh}
        >
          Refresh status
        </button>
      </div>
      <ul className="status-list" aria-live="polite" aria-busy={checking}>
        {statuses.map((status) => (
          <li className="status-row" key={status.service}>
            <span className="service-name">{status.service}</span>
            <span className="service-state" data-state={status.state}>
              <span className="status-check" aria-hidden="true">
                {icons[status.state]}
              </span>
              {status.label}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
