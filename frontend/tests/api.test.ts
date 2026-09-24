import { afterEach, expect, test, vi } from "vitest";
import { getSystemStatus } from "../lib/api";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function mockResponse(status: number, body: unknown) {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test/");
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => {
    void _input;
    void _init;
    return new Response(JSON.stringify(body), { status });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

test("healthy API uses the browser URL, disables caching, and reports connected services", async () => {
  const fetchMock = mockResponse(200, { status: "ok", database: "connected" });
  const result = await getSystemStatus();
  expect(result.map(({ label }) => label)).toEqual(["Online", "Connected", "Connected"]);
  expect(fetchMock).toHaveBeenCalledWith(
    "https://api.test/api/health",
    expect.objectContaining({ cache: "no-store", signal: expect.any(AbortSignal) }),
  );
});

test("degraded API reports a connected backend and unavailable database", async () => {
  mockResponse(503, { status: "degraded", database: "unavailable" });
  const result = await getSystemStatus();
  expect(result.map(({ label }) => label)).toEqual(["Online", "Connected", "Unavailable"]);
  expect(result[2].state).toBe("unhealthy");
});

test.each([
  [200, { status: "degraded", database: "unavailable" }],
  [503, { status: "ok", database: "connected" }],
  [500, { status: "ok", database: "connected" }],
  [200, null],
  [200, {}],
])("invalid health response: %s %j", async (status, body) => {
  mockResponse(status, body);
  expect((await getSystemStatus()).map(({ label }) => label)).toEqual(["Online", "Unavailable", "Unknown"]);
});

test("missing configuration never issues a request", async () => {
  const fetchMock = mockResponse(200, {});
  vi.stubEnv("NEXT_PUBLIC_API_URL", "");
  expect((await getSystemStatus())[2].label).toBe("Unknown");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("malformed JSON is handled", async () => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
  vi.stubGlobal("fetch", vi.fn(async () => new Response("not JSON")));
  expect((await getSystemStatus())[1].label).toBe("Unavailable");
});

test.each([new TypeError("Network failure"), new DOMException("Timed out", "TimeoutError")])(
  "request failure is handled: %s",
  async (error) => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.test");
    vi.stubGlobal("fetch", vi.fn(async () => { throw error; }));
    expect((await getSystemStatus()).map(({ label }) => label)).toEqual(["Online", "Unavailable", "Unknown"]);
  },
);

test("request combines caller cancellation with a five-second timeout", async () => {
  const fetchMock = mockResponse(200, { status: "ok", database: "connected" });
  const timeout = vi.spyOn(AbortSignal, "timeout").mockReturnValue(new AbortController().signal);
  const controller = new AbortController();
  await getSystemStatus(controller.signal);
  expect(timeout).toHaveBeenCalledWith(5000);
  controller.abort();
  const signal = fetchMock.mock.calls[0][1]?.signal;
  expect(signal?.aborted).toBe(true);
});
