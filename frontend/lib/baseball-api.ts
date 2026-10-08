import "server-only";
import { notFound } from "next/navigation";
import type { Team, TeamList } from "@/types/team";
import type { TeamRoster } from "@/types/roster";
import type {
  Player,
  PlayerStats,
  Standings,
  TeamSchedule,
  TeamStats,
} from "@/types/baseball";

function apiBase(): string {
  const value = process.env.API_INTERNAL_URL?.trim();
  if (!value) throw new Error("Internal API URL is missing");
  return value.replace(/\/$/, "");
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(15000),
  });
  if (response.status === 404) notFound();
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return (await response.json()) as T;
}

export function getTeams(): Promise<TeamList> {
  return getJson<TeamList>("/api/teams");
}

export function getTeam(id: number): Promise<Team> {
  return getJson<Team>(`/api/teams/${id}`);
}

export function getRoster(id: number): Promise<TeamRoster> {
  return getJson<TeamRoster>(`/api/teams/${id}/roster`);
}

export const getTeamHittingStats = (id: number) =>
  getJson<TeamStats>(`/api/teams/${id}/stats/hitting`);
export const getTeamPitchingStats = (id: number) =>
  getJson<TeamStats>(`/api/teams/${id}/stats/pitching`);
export const getTeamFieldingStats = (id: number) =>
  getJson<TeamStats>(`/api/teams/${id}/stats/fielding`);
export function getTeamSchedule(
  id: number,
  startDate?: string,
  endDate?: string,
): Promise<TeamSchedule> {
  const query = new URLSearchParams();
  if (startDate) query.set("start_date", startDate);
  if (endDate) query.set("end_date", endDate);
  return getJson<TeamSchedule>(
    `/api/teams/${id}/schedule${query.size ? `?${query}` : ""}`,
  );
}
export const getStandings = () => getJson<Standings>("/api/standings");
export const getPlayer = (id: number) => getJson<Player>(`/api/players/${id}`);
export const getPlayerHittingStats = (id: number) =>
  getJson<PlayerStats>(`/api/players/${id}/stats/hitting`);
export const getPlayerPitchingStats = (id: number) =>
  getJson<PlayerStats>(`/api/players/${id}/stats/pitching`);
