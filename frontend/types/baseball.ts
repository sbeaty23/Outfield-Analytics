export interface TeamStats {
  team_id: number;
  season: number;
  group: string;
  stats: HittingStats | PitchingStats | FieldingStats | null;
}
export interface Player {
  id: number;
  full_name: string;
  first_name: string | null;
  last_name: string | null;
  jersey_number: string | null;
  primary_position: string | null;
  bat_side: string | null;
  throw_side: string | null;
  height: string | null;
  weight: number | null;
  active: boolean;
  current_team_id: number | null;
}
export interface PlayerStats {
  player_id: number;
  season: number;
  group: string;
  stats: HittingStats | PitchingStats | null;
}
export interface TeamSchedule {
  team_id: number;
  season: number;
  games: Array<{
    game_id: number;
    game_date: string;
    game_type: string;
    away_team_id: number;
    away_team_name: string;
    home_team_id: number;
    home_team_name: string;
    away_score: number | null;
    home_score: number | null;
    status: string;
    venue_name: string | null;
    probable_home_pitcher: string | null;
    probable_away_pitcher: string | null;
  }>;
}
export interface Standings {
  season: number;
  divisions: Array<{
    division_id: number;
    division_name: string;
    teams: Array<{
      team_id: number;
      team_name: string;
      wins: number;
      losses: number;
      winning_percentage: number;
      games_back: string;
      division_rank: number | null;
      league_rank: number | null;
      last_ten_wins: number | null;
      last_ten_losses: number | null;
      streak: string | null;
    }>;
  }>;
}

export interface HittingStats {
  games: number | null;
  plate_appearances: number | null;
  at_bats: number | null;
  runs: number | null;
  hits: number | null;
  doubles: number | null;
  triples: number | null;
  home_runs: number | null;
  rbi: number | null;
  walks: number | null;
  strikeouts: number | null;
  average: number | null;
  obp: number | null;
  slg: number | null;
  ops: number | null;
}

export interface PitchingStats {
  games: number | null;
  wins: number | null;
  losses: number | null;
  innings_pitched: string | null;
  hits: number | null;
  runs: number | null;
  earned_runs: number | null;
  home_runs: number | null;
  walks: number | null;
  strikeouts: number | null;
  era: number | null;
  whip: number | null;
}

export interface FieldingStats {
  games: number | null;
  games_started: number | null;
  innings: string | null;
  putouts: number | null;
  assists: number | null;
  errors: number | null;
  fielding_percentage: number | null;
}
