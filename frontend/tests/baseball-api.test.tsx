import { afterEach, expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("server-only", () => ({}));
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("NOT_FOUND");
  },
}));

import * as api from "../lib/baseball-api";
import TeamsPage from "../app/teams/page";
import TeamPage from "../app/teams/[teamId]/page";
import TeamsError from "../app/teams/error";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function responses(body: unknown, status = 200) {
  vi.stubEnv("API_INTERNAL_URL", "https://internal.test/");
  vi.stubEnv("NEXT_PUBLIC_API_URL", "https://browser.test");
  const fetchMock = vi.fn(
    async () => new Response(JSON.stringify(body), { status }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

test.each([
  [() => api.getTeams(), "/api/teams"],
  [() => api.getTeam(110), "/api/teams/110"],
  [() => api.getRoster(110), "/api/teams/110/roster"],
  [() => api.getTeamHittingStats(110), "/api/teams/110/stats/hitting"],
  [() => api.getTeamPitchingStats(110), "/api/teams/110/stats/pitching"],
  [() => api.getTeamFieldingStats(110), "/api/teams/110/stats/fielding"],
  [() => api.getStandings(), "/api/standings"],
  [() => api.getPlayer(123), "/api/players/123"],
  [() => api.getPlayerHittingStats(123), "/api/players/123/stats/hitting"],
  [() => api.getPlayerPitchingStats(123), "/api/players/123/stats/pitching"],
] as const)("uses the internal origin: %s", async (call, path) => {
  const mock = responses({ stats: null });
  expect(await call()).toEqual({ stats: null });
  expect(mock).toHaveBeenCalledWith(
    `https://internal.test${path}`,
    expect.objectContaining({
      cache: "no-store",
      signal: expect.any(AbortSignal),
    }),
  );
});

test("encodes schedule dates", async () => {
  const mock = responses({ games: [] });
  await api.getTeamSchedule(110, "2026-06-01", "2026-06-03");
  expect(mock.mock.calls[0]).toEqual(
    expect.arrayContaining([
      "https://internal.test/api/teams/110/schedule?start_date=2026-06-01&end_date=2026-06-03",
    ]),
  );
});

test("requires the internal origin without public fallback", async () => {
  const mock = responses({});
  vi.stubEnv("API_INTERNAL_URL", "");
  await expect(api.getTeams()).rejects.toThrow("Internal API URL is missing");
  expect(mock).not.toHaveBeenCalled();
});

test("maps missing resources to the Next.js not-found boundary", async () => {
  responses({}, 404);
  await expect(api.getTeam(999)).rejects.toThrow("NOT_FOUND");
});

test("rejects provider outages", async () => {
  responses({}, 502);
  await expect(api.getTeams()).rejects.toThrow("API request failed: 502");
});

test("renders normalized teams", async () => {
  responses({
    season: 2026,
    teams: [{ id: 110, name: "Test Club", division: "Test Division" }],
  });
  render(await TeamsPage());
  expect(
    screen.getByRole("link", { name: "Test Club" }).getAttribute("href"),
  ).toBe("/teams/110");
});

test("renders missing optional roster information", async () => {
  responses({});
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async (url: string) =>
        new Response(
          JSON.stringify(
            url.endsWith("/roster")
              ? {
                  players: [
                    {
                      player_id: 1,
                      full_name: "Test Player",
                      position_name: null,
                      position_abbreviation: null,
                    },
                  ],
                }
              : {
                  name: "Test Club",
                  abbreviation: "TST",
                  league: "Test League",
                  division: null,
                },
          ),
        ),
    ),
  );
  render(await TeamPage({ params: Promise.resolve({ teamId: "110" }) }));
  expect(screen.getByText(/Position pending/)).toBeTruthy();
});

test("renders a useful retry action on outages", () => {
  const reset = vi.fn();
  render(<TeamsError reset={reset} />);
  screen.getByRole("button", { name: "Try again" }).click();
  expect(reset).toHaveBeenCalledOnce();
});
