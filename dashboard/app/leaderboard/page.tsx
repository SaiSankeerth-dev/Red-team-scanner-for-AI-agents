import Link from "next/link";
import { api, gradeClass } from "@/lib/api";

export const dynamic = "force-dynamic";

const TARGET_BLURBS: Record<string, string> = {
  hardened: "Reference build: refuses everything, confirms before acting.",
  "almost-hardened": "Well-built, one edge case: dumps config files verbatim.",
  "eager-assistant": "Good hygiene, asks for confirmation — but repeats secrets from files and URLs.",
  "naive-rag": "RAG bot that trusts retrieved documents completely.",
  vulnerable: "Intentionally vulnerable baseline: obeys the latest instruction, leaks on request.",
};

export default async function Leaderboard() {
  const campaigns = await api.campaigns();
  // Latest campaign per target.
  const latest = new Map<number, (typeof campaigns)[number]>();
  for (const c of campaigns) latest.set(c.id, c);
  const byTarget = new Map<string, (typeof campaigns)[number]>();
  for (const c of [...campaigns].sort((a, b) => b.id - a.id)) {
    if (!byTarget.has(c.target)) byTarget.set(c.target, c);
  }

  const rows = await Promise.all(
    [...byTarget.entries()].map(async ([target, c]) => {
      try {
        const s = await api.summary(c.id);
        return { target, id: c.id, score: s.score, grade: s.grade, counts: s.counts };
      } catch {
        return null;
      }
    })
  );
  const ranked = rows.filter(Boolean).sort((a, b) => b!.score - a!.score);

  return (
    <>
      <Link href="/">← campaigns</Link>
      <h1 style={{ marginTop: 12 }}>Leaderboard</h1>
      <p className="sub">
        Latest Redline score per target. All targets here are synthetic demo
        agents shipped with Redline — the same 27-attack pack, the same
        deterministic detectors, no cherry-picking.
      </p>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th className="num">#</th>
              <th>Target</th>
              <th>Profile</th>
              <th className="num">Score</th>
              <th className="num">Grade</th>
              <th className="num">Failed</th>
              <th className="num">Blocked</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((r, i) => (
              <tr key={r!.target}>
                <td className="num" style={{ fontWeight: 800 }}>{i + 1}</td>
                <td><b>{r!.target}</b></td>
                <td style={{ color: "#9aa6b2", fontSize: 13 }}>
                  {TARGET_BLURBS[r!.target] ?? ""}
                </td>
                <td className="num" style={{ fontWeight: 800, fontSize: 17 }}>{r!.score}</td>
                <td className="num">
                  <span className={gradeClass(r!.grade)} style={{ width: 36, height: 36, fontSize: 16 }}>
                    {r!.grade}
                  </span>
                </td>
                <td className="num" style={{ color: "#ff3b47", fontWeight: 700 }}>{r!.counts.fail}</td>
                <td className="num">{r!.counts.pass}</td>
                <td><Link href={`/campaigns/${r!.id}`}>report →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="sub" style={{ marginTop: 16 }}>
        Scores are triage signals, not certifications. Every finding links to a
        full reproduction transcript. Methodology: <b>README → Methodology</b>.
      </p>
    </>
  );
}
