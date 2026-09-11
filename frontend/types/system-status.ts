export interface SystemStatus {
  service: "Frontend" | "Backend" | "Database";
  label: "Online" | "Connected";
  state: "healthy";
}
