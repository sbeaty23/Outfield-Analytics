export interface SystemStatus {
  service: "Frontend" | "Backend" | "Database";
  label: "Online" | "Checking" | "Connected" | "Unavailable" | "Unknown";
  state: "healthy" | "loading" | "unhealthy" | "unknown";
}
