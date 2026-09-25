import Link from "next/link";
import { api, gradeClass } from "@/lib/api";

export const dynamic = "force-dynamic";

function statusClass(status: string) {
  return `status ${status.replace(" ", "-")}`;
}

export default async function CampaignDetail({
  params,
}: {
  params: { id: string };
}) {
  let data: Awaited<ReturnType<typeof api.summary>> | null = null;
  let loadError = "";
  try {
    data = await api.summary(params.id);
  } catch (e) {
    loadError = e instanceof Error ? e.message : "could not load campaign";
  }

  if (!data) {
    return (
      <>
        <Link href="/">← campaigns</Link>
        <div className="empty">{loadError || "Campaign not found."}</div>
      </>
    );
  }

  const c = data.campaign;
  return (
    <>
      <Link href="/">← campaigns</Link>
      <h1 style={{ marginTop: 12 }}>
        #{c.id} — {c.name}
      </h1>
      <p className="sub">
        target <b>{c.target}</b> · pack {c.pack} · run {c.created_at} · report
        generated {data.generated_at}
      </p>

      <div className="scorecard">
        <div className={`${gradeClass(data.grade)} grade-big`}>{data.grade}</div>
        <div>
          <div className="score-num">
            {data.score}
            <small>/100</small>
          </div>
          <div className="counts">
            <span>
              <b className="bad">{data.counts.fail}</b> failed
            </span>
            <span>
              <b>{data.counts.partial}</b> unclear
            </span>
            <span>
              <b>{data.counts.pass}</b> blocked
            </span>
            <span>
              <b>{data.counts.total}</b> total
            </span>
          </div>
        </div>
      </div>

      <div className="actions">
        <a href={api.reportUrl(c.id)} target="_blank" rel="noreferrer">
          <button className="btn-ghost" type="button">Full HTML report ↗</button>
        </a>
        <a href={api.pdfUrl(c.id)} target="_blank" rel="noreferrer">
          <button className="btn-ghost" type="button">Download PDF ↓</button>
        </a>
      </div>

      <h2>Probe breakdown</h2>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Probe</th>
              <th>Severity</th>
              <th>What it tests</th>
              <th className="num">Attempts</th>
              <th className="num">Failed</th>
              <th className="num">Blocked</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.probes.map((p) => (
              <tr key={p.name}>
                <td>
                  <b>{p.name}</b>
                </td>
                <td>
                  <span className={`sev sev-${p.severity}`}>{p.severity}</span>
                </td>
                <td style={{ color: "#9aa6b2" }}>{p.description}</td>
                <td className="num">{p.total}</td>
                <td className="num" style={{ color: "#ff3b47", fontWeight: 700 }}>
                  {p.fail}
                </td>
                <td className="num">{p.pass}</td>
                <td>
                  <span className={statusClass(p.status)}>{p.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2>Findings ({data.findings.length})</h2>
      {data.findings.length === 0 ? (
        <div className="empty">No failed attempts. Nothing to fix.</div>
      ) : (
        data.findings.map((f, i) => (
          <section className="finding" key={i}>
            <h3>
              #{i + 1} — {f.probe_name}
              <span className={`sev sev-${f.severity}`}>{f.severity}</span>
            </h3>
            {f.messages.map((m, j) => (
              <div className="turn" key={j}>
                <span className="role">{m.role}</span>
                <pre>{m.content}</pre>
              </div>
            ))}
            <div className="turn">
              <span className="role">agent response</span>
              <pre>{f.response}</pre>
            </div>
            {f.notes && (
              <p className="notes">
                <strong>Detector notes:</strong> {f.notes}
              </p>
            )}
            <p className="fix">
              <strong>How to fix:</strong> {f.remediation}
            </p>
          </section>
        ))
      )}
    </>
  );
}
