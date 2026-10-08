import Link from "next/link";

import { getTeams } from "@/lib/baseball-api";

export const dynamic = "force-dynamic";

export default async function TeamsPage() {
  const { season, teams } = await getTeams();
  const divisions = Map.groupBy(teams, (team) => team.division ?? "Other");
  return (
    <main className="content-shell">
      <p className="eyebrow">Outfield Analytics</p>
      <h1>MLB teams</h1>
      <p className="intro">Current {season} active clubs.</p>
      {[...divisions].map(([division, clubs]) => (
        <section className="team-group" key={division}>
          <h2>{division}</h2>
          <ul className="team-grid">
            {clubs.map((team) => (
              <li key={team.id}>
                <Link href={`/teams/${team.id}`}>{team.name}</Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
