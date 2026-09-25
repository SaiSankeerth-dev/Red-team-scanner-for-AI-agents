import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Redline — agent red-team scanner",
  description: "Scan AI agents for prompt injection, jailbreaks, and tool misuse.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <a href="/" className="brand">
            <span className="brand-mark">◤</span> REDLINE
          </a>
          <span className="tagline">agent red-team scanner</span>
          <nav style={{ marginLeft: "auto", display: "flex", gap: 18, fontSize: 14 }}>
            <a href="/" style={{ color: "#e8edf2" }}>campaigns</a>
            <a href="/leaderboard" style={{ color: "#e8edf2" }}>leaderboard</a>
          </nav>
        </header>
        <main className="container">{children}</main>
        <footer className="footer">
          Redline runs only against targets you own, that permit testing, or public
          demos. All secrets shown are synthetic canaries.
        </footer>
      </body>
    </html>
  );
}
