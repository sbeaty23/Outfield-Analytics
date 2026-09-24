import type { SystemStatus } from "@/types/system-status";

export const initialStatuses = [
  { service: "Frontend", label: "Online", state: "healthy" },
  { service: "Backend", label: "Checking", state: "loading" },
  { service: "Database", label: "Checking", state: "loading" },
] as const satisfies readonly SystemStatus[];

export async function getSystemStatus(signal?: AbortSignal): Promise<readonly SystemStatus[]> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
    if (!apiUrl) throw new Error("API URL is missing");

    const timeout = AbortSignal.timeout(5000);
    const response = await fetch(`${apiUrl.replace(/\/$/, "")}/api/health`, {
      cache: "no-store",
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
    const body: unknown = await response.json();
    if (!body || typeof body !== "object" || !("status" in body) || !("database" in body)) {
      throw new Error("Invalid health response");
    }
    const connected = response.status === 200 && body.status === "ok" && body.database === "connected";
    const unavailable = response.status === 503 && body.status === "degraded" && body.database === "unavailable";
    if (!connected && !unavailable) throw new Error("Unexpected health response");

    return [
      initialStatuses[0],
      { service: "Backend", label: "Connected", state: "healthy" },
      {
        service: "Database",
        label: connected ? "Connected" : "Unavailable",
        state: connected ? "healthy" : "unhealthy",
      },
    ];
  } catch {
    return [
      initialStatuses[0],
      { service: "Backend", label: "Unavailable", state: "unhealthy" },
      { service: "Database", label: "Unknown", state: "unknown" },
    ];
  }
}
