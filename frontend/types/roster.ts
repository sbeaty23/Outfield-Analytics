export interface RosterPlayer {
  player_id: number;
  full_name: string;
  jersey_number: string | null;
  position_name: string | null;
  position_abbreviation: string | null;
  position_type: string | null;
  status: string | null;
}

export interface TeamRoster {
  team_id: number;
  season: number;
  roster_type: "active";
  players: RosterPlayer[];
}
