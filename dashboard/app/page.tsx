import Link from "next/link";
import NewScanForm from "@/components/NewScanForm";
import { api, gradeClass } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  let campaigns: Awaited<ReturnType<typeof api.campaigns>> = [];
  let loadError = "";
  try {
    campaigns = await api.campaigns();
  } catch (e) {
    loadError = e instanceof Error ? e.message : "could not reach the API";
  }

  // Fetch scores for the grade badges (fine at this scale).
  const withScores = await Promise.all(
    campaigns.map(async (c) => {
      try {
        const s = await api.summary(c.id);
        return { ...c, score: s.score, grade: s.grade };
      } catch {
        return { ...c, score: null as number | null, grade: "?" };
      }
    })
  );

  return (
    <>
      <h1>Campaigns</h1>
      <p className="sub">
        Every red-team scan Redline has run. Click through for the full scored
        breakdown and transcripts.
      </p>

      {loadError ? (
        <div className="empty">
          Could not reach the Redline API at{" "}
          <code>{process.env.NEXT_PUBLIC_REDLINE_API ?? "http://localhost:8000"}</code>
          <br />
          <span style={{ fontSize: 13 }}>Start it with: <code>redline serve</code></span>
          <br />
          <span style={{ fontSize: 13, color: "#b91c1c" }}>{loadError}</span>
        </div>
      ) : withScores.length === 0 ? (
        <div className="empty">No campaigns yet — run your first scan below.</div>
      ) : (
        <div className="cards">
          {withScores.map((c) => (
            <Link
              key={c.id}
              href={`/campaigns/${c.id}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div className={gradeClass(c.grade)}>{c.grade}</div>
              <div className="main">
                <div className="name">
                  #{c.id} — {c.name}
                </div>
                <div className="meta">
                  target <b>{c.target}</b> · pack {c.pack} · {c.created_at}
                  {c.score !== null && <> · score {c.score}/100</>}
                </div>
              </div>
              <div className="stats">
                <span className="stat-fail">
                  <b>{c.verdict_counts.fail ?? 0}</b> failed
                </span>
                <span>
                  <b>{c.verdict_counts.pass ?? 0}</b> blocked
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      <NewScanForm />
    </>
  );
}
