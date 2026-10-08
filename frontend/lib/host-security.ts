export function isAllowedHost(
  hostHeader: string | null,
  configuredHosts: string | undefined,
): boolean {
  if (!hostHeader || !configuredHosts) return false;
  const hostname = hostHeader.trim().toLowerCase().split(":", 1)[0];
  const allowed = configuredHosts
    .split(",")
    .map((host) => host.trim().toLowerCase())
    .filter(Boolean);
  return Boolean(hostname) && allowed.includes(hostname);
}
