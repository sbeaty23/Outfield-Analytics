export interface Team {
  id: number;
  name: string;
  abbreviation: string;
  location: string;
  team_name: string | null;
  league_id: number | null;
  league: string;
  division_id: number | null;
  division: string | null;
  venue: string | null;
  active: boolean;
}

export interface TeamList {
  season: number;
  teams: Team[];
}
