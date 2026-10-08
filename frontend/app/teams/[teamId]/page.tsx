import Link from "next/link";
import { notFound } from "next/navigation";

import { getRoster, getTeam } from "@/lib/baseball-api";

export default async function TeamPage({
  params,
}: {
  params: Promise<{ teamId: string }>;
}) {
  const teamId = Number((await params).teamId);
  if (!Number.isInteger(teamId) || teamId <= 0) notFound();
  const [team, roster] = await Promise.all([
    getTeam(teamId),
    getRoster(teamId),
  ]);
  return (
    <main className="content-shell">
      <Link className="back-link" href="/teams">
        ← All teams
      </Link>
      <p className="eyebrow">{team.abbreviation}</p>
      <h1>{team.name}</h1>
      <dl className="team-facts">
        <div>
          <dt>League</dt>
          <dd>{team.league}</dd>
        </div>
        <div>
          <dt>Division</dt>
          <dd>{team.division ?? "—"}</dd>
        </div>
        <div>
          <dt>Active roster</dt>
          <dd>{roster.players.length} players</dd>
        </div>
      </dl>
      <section className="team-group">
        <h2>Active roster</h2>
        <ul className="team-grid">
          {roster.players.map((player) => (
            <li key={player.player_id}>
              {player.full_name} ·{" "}
              {player.position_abbreviation ??
                player.position_name ??
                "Position pending"}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
