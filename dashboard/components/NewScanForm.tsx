"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export default function NewScanForm() {
  const router = useRouter();
  const [adapter, setAdapter] = useState("local");
  const [target, setTarget] = useState("vulnerable");
  const [model, setModel] = useState("gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [httpUrl, setHttpUrl] = useState("");
  const [responsePath, setResponsePath] = useState("response");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const adapter_config: Record<string, unknown> = {};
      let name: string | undefined;
      if (adapter === "openai") {
        adapter_config.model = model;
        if (apiKey) adapter_config.api_key = apiKey;
        if (baseUrl) adapter_config.base_url = baseUrl;
        name = `openai:${model}`;
      } else if (adapter === "http") {
        adapter_config.url = httpUrl;
        adapter_config.response_path = responsePath;
        name = httpUrl;
      }
      const { id } = await api.createCampaign({
        target,
        pack: "basics",
        name,
        adapter,
        adapter_config,
      });
      router.push(`/campaigns/${id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "scan failed");
      setBusy(false);
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <h2>New scan</h2>
      <div className="grid">
        <div>
          <label>Adapter</label>
          <select value={adapter} onChange={(e) => setAdapter(e.target.value)}>
            <option value="local">local demo</option>
            <option value="openai">OpenAI-compatible</option>
            <option value="http">generic HTTP</option>
          </select>
        </div>
        {adapter === "local" && (
          <div>
            <label>Demo target</label>
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="vulnerable">vulnerable</option>
              <option value="hardened">hardened</option>
            </select>
          </div>
        )}
        {adapter === "openai" && (
          <>
            <div>
              <label>Model</label>
              <input value={model} onChange={(e) => setModel(e.target.value)} />
            </div>
            <div>
              <label>API key (or set OPENAI_API_KEY server-side)</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-…"
              />
            </div>
            <div>
              <label>Base URL (optional)</label>
              <input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
            </div>
          </>
        )}
        {adapter === "http" && (
          <>
            <div>
              <label>Endpoint URL</label>
              <input
                value={httpUrl}
                onChange={(e) => setHttpUrl(e.target.value)}
                placeholder="https://your-agent/hook"
                required
              />
            </div>
            <div>
              <label>Response JSON path</label>
              <input
                value={responsePath}
                onChange={(e) => setResponsePath(e.target.value)}
              />
            </div>
          </>
        )}
      </div>
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={busy}>
        {busy ? "Scanning…" : "Run scan"}
      </button>
    </form>
  );
}
