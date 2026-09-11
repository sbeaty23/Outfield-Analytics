import type { SystemStatus } from "@/types/system-status";

const initialStatuses = [
  { service: "Frontend", label: "Online", state: "healthy" },
  { service: "Backend", label: "Connected", state: "healthy" },
  { service: "Database", label: "Connected", state: "healthy" },
] as const satisfies readonly SystemStatus[];

export async function getSystemStatus(): Promise<readonly SystemStatus[]> {
  return initialStatuses;
}
