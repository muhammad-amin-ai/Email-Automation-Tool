import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

function useCountUp(target, durationMs = 700) {
  const [value, setValue] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const end = Number(target) || 0;
    const start = performance.now();
    const from = 0;

    function tick(now) {
      const progress = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setValue(Math.round(from + (end - from) * eased));
      if (progress < 1) {
        raf.current = requestAnimationFrame(tick);
      }
    }

    raf.current = requestAnimationFrame(tick);
    return () => raf.current && cancelAnimationFrame(raf.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);

  return value;
}

const icons = {
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  userCheck: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="m16 11 2 2 4-4" />
    </svg>
  ),
  userX: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="m17 8 4 4M21 8l-4 4" />
    </svg>
  ),
  alertTriangle: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4M12 17h.01" />
    </svg>
  ),
  megaphone: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m3 11 18-5v12L3 14v-3z" />
      <path d="M11.6 16.8a3 3 0 1 1-5.8-1.6" />
    </svg>
  ),
  play: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="5 3 19 12 5 21 5 3" />
    </svg>
  ),
  edit: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  ),
  fileText: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
    </svg>
  ),
  send: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </svg>
  ),
  clock: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  ),
  loader: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="icon-spin">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  ),
  x: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  ),
  checkCircle: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="m9 11 3 3L22 4" />
    </svg>
  ),
  pause: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="6" y="4" width="4" height="16" rx="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" />
    </svg>
  ),
  bounce: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 12h4l3 8 4-16 3 8h4" />
    </svg>
  ),
  target: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  ),
};

function StatCard({ label, value, icon, color, delay }) {
  const animated = useCountUp(value ?? 0);
  return (
    <div
      className="stat-card"
      style={{ "--card-color": color, animationDelay: `${delay}ms` }}
    >
      <div className="stat-card-top">
        <div className="stat-card-icon">{icon}</div>
      </div>
      <div className="value">{animated}</div>
      <div className="label">{label}</div>
    </div>
  );
}

function EmailStatusBars({ summary }) {
  const rows = [
    { label: "Sent", value: summary.total_sent, color: "var(--success)", icon: icons.send },
    { label: "Queued", value: summary.total_queued, color: "var(--accent)", icon: icons.clock },
    { label: "Processing", value: summary.total_processing, color: "var(--accent-2)", icon: icons.loader },
    { label: "Failed", value: summary.total_failed, color: "var(--danger)", icon: icons.x },
    { label: "Bounced", value: summary.total_bounced, color: "var(--danger)", icon: icons.bounce },
  ];
  const max = Math.max(1, ...rows.map((r) => r.value || 0));
  const total = rows.reduce((sum, r) => sum + (r.value || 0), 0);
  const sentPct = total > 0 ? Math.round(((summary.total_sent || 0) / total) * 100) : 0;

  return (
    <div className="dash-bar-panel">
      <div className="dash-bar-panel-head">
        <h3>Email jobs breakdown</h3>
        {total > 0 && <span className="dash-success-pct">{sentPct}% delivered</span>}
      </div>
      {rows.map((r) => (
        <div className="dash-bar-row" key={r.label}>
          <span className="dash-bar-label">{r.label}</span>
          <div className="dash-bar-track">
            <div
              className="dash-bar-fill"
              style={{
                background: r.color,
                width: `${((r.value || 0) / max) * 100}%`,
              }}
            />
          </div>
          <span className="dash-bar-count">{r.value ?? 0}</span>
        </div>
      ))}
    </div>
  );
}

function SuccessRateCard({ summary }) {
  const attempted =
    (summary.total_sent || 0) +
    (summary.total_failed || 0) +
    (summary.total_bounced || 0);
  const pct =
    attempted > 0 ? Math.round(((summary.total_sent || 0) / attempted) * 100) : null;

  const size = 96;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = pct !== null ? (pct / 100) * circumference : 0;

  return (
    <div className="dash-bar-panel dash-rate-card">
      <div className="dash-bar-panel-head">
        <h3>Delivery success rate</h3>
      </div>
      {pct === null ? (
        <p className="muted" style={{ margin: 0 }}>
          No emails sent yet — this fills in once campaigns start sending.
        </p>
      ) : (
        <div className="dash-rate-body">
          <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="var(--border, #e5e7eb)"
              strokeWidth={stroke}
            />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="var(--success)"
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circumference - dash}`}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
            <text
              x="50%"
              y="50%"
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="20"
              fontWeight="700"
              fill="currentColor"
            >
              {pct}%
            </text>
          </svg>
          <div className="dash-rate-details">
            <div>
              <span className="dash-rate-dot" style={{ background: "var(--success)" }} />
              {summary.total_sent ?? 0} delivered
            </div>
            <div>
              <span className="dash-rate-dot" style={{ background: "var(--danger)" }} />
              {(summary.total_failed || 0) + (summary.total_bounced || 0)} failed / bounced
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .analyticsSummary()
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!summary)
    return (
      <div className="muted btn-busy-content">
        {icons.loader}
        Loading...
      </div>
    );

  const contactStats = [
    { label: "Total contacts", value: summary.total_contacts, icon: icons.users, color: "var(--accent)" },
    { label: "Active contacts", value: summary.active_contacts, icon: icons.userCheck, color: "var(--success)" },
    { label: "Unsubscribed", value: summary.unsubscribed_contacts, icon: icons.userX, color: "var(--muted)" },
    { label: "Bounced contacts", value: summary.bounced_contacts, icon: icons.alertTriangle, color: "var(--danger)" },
  ];

  const campaignStats = [
    { label: "Total campaigns", value: summary.total_campaigns, icon: icons.megaphone, color: "var(--accent)" },
    { label: "Active campaigns", value: summary.active_campaigns, icon: icons.play, color: "var(--success)" },
    { label: "Draft campaigns", value: summary.draft_campaigns, icon: icons.edit, color: "var(--accent-2)" },
    { label: "Paused campaigns", value: summary.paused_campaigns, icon: icons.pause, color: "var(--muted)" },
    { label: "Completed campaigns", value: summary.completed_campaigns, icon: icons.checkCircle, color: "var(--success)" },
    { label: "Templates", value: summary.total_templates, icon: icons.fileText, color: "var(--accent)" },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>Dashboard</h2>
      </div>

      <div className="dash-section-title">Contacts</div>
      <div className="grid-stats">
        {contactStats.map((s, i) => (
          <StatCard key={s.label} {...s} delay={i * 60} />
        ))}
      </div>

      <div className="dash-section-title">Campaigns &amp; templates</div>
      <div className="grid-stats">
        {campaignStats.map((s, i) => (
          <StatCard key={s.label} {...s} delay={i * 60} />
        ))}
      </div>

      <div className="dash-section-title">Email delivery</div>
      {summary.total_failed > 0 && (
        <Link to="/campaigns" className="dash-alert-banner">
          {icons.alertTriangle}
          <span>
            {summary.total_failed} email{summary.total_failed > 1 ? "s" : ""} failed to
            send — view campaigns to see details
          </span>
        </Link>
      )}
      <div className="dash-delivery-grid">
        <EmailStatusBars summary={summary} />
        <SuccessRateCard summary={summary} />
      </div>
    </div>
  );
}