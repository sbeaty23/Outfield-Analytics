import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { SystemStatusPanel } from "../components/system-status-panel";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function service(name: string) {
  const row = screen.getByText(name).closest("li");
  if (!row) throw new Error(`Missing ${name} row`);
  return within(row);
}

function healthResponse(status: number, database: "connected" | "unavailable") {
  return new Response(
    JSON.stringify({
      status: status === 200 ? "ok" : "degraded",
      database,
    }),
    { status },
  );
}

test("checks the API on mount and renders the connected backend and database", async () => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
  let finishRequest: (response: Response) => void = () => {};
  const fetchMock = vi.fn(() => new Promise<Response>((resolve) => { finishRequest = resolve; }));
  vi.stubGlobal("fetch", fetchMock);

  render(<SystemStatusPanel />);
  expect(service("Backend").getByText("Checking")).toBeTruthy();
  expect(service("Database").getByText("Checking")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Refresh status" }).hasAttribute("disabled")).toBe(true);

  finishRequest(healthResponse(200, "connected"));
  await waitFor(() => expect(service("Backend").getByText("Connected")).toBeTruthy());
  expect(service("Database").getByText("Connected")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith("https://api.test/api/health", expect.any(Object));
});

test("a degraded API leaves backend connected and marks database unavailable", async () => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
  vi.stubGlobal("fetch", vi.fn(async () => healthResponse(503, "unavailable")));

  render(<SystemStatusPanel />);
  await waitFor(() => expect(service("Database").getByText("Unavailable")).toBeTruthy());
  expect(service("Backend").getByText("Connected")).toBeTruthy();
});

test("an API failure marks backend unavailable and database unknown", async () => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
  vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Connection refused"); }));

  render(<SystemStatusPanel />);
  await waitFor(() => expect(service("Backend").getByText("Unavailable")).toBeTruthy());
  expect(service("Database").getByText("Unknown")).toBeTruthy();
  expect(service("Backend").getByText("!")).toBeTruthy();
});

test("refresh checks again and shows recovery", async () => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
  const fetchMock = vi.fn()
    .mockRejectedValueOnce(new TypeError("Connection refused"))
    .mockResolvedValueOnce(healthResponse(200, "connected"));
  vi.stubGlobal("fetch", fetchMock);

  render(<SystemStatusPanel />);
  await waitFor(() => expect(service("Backend").getByText("Unavailable")).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: "Refresh status" }));
  await waitFor(() => expect(service("Database").getByText("Connected")).toBeTruthy());
  expect(service("Backend").getByText("Connected")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
