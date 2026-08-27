import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api.js";
import { icons } from "../components/icons.jsx";

function formatDelay(hours) {
  const h = Number(hours) || 0;
  if (h === 0) return "Sends immediately";
  const days = Math.floor(h / 24);
  const remHours = h % 24;
  const parts = [];
  if (days > 0) parts.push(`${days} day${days > 1 ? "s" : ""}`);
  if (remHours > 0) parts.push(`${remHours} hour${remHours > 1 ? "s" : ""}`);
  return `Sends ${parts.join(" ")} after start`;
}

function formatUtc(value) {
  if (!value) return "—";
  // Backend sends naive UTC datetimes (no "Z" suffix). Without it, JS
  // treats the string as local time instead of UTC, which shows the
  // wrong clock time. Appending "Z" tells JS "this is UTC" so it
  // converts correctly to the browser's local time zone.
  const isoWithZ = value.endsWith("Z") ? value : `${value}Z`;
  return new Date(isoWithZ).toLocaleString();
}

export default function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [campaigns, templatesData] = await Promise.all([
        api.listCampaigns(),
        api.listTemplates(),
      ]);
      const found = campaigns.items.find((c) => String(c.id) === id);
      setCampaign(found || null);
      setTemplates(templatesData.items);
      const jobsData = await api.campaignJobs(id);
      setJobs(jobsData.items);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error) return <div className="alert error">{error}</div>;
  if (!campaign)
    return (
      <div className="muted btn-busy-content">
        {icons.spinner}
        Loading...
      </div>
    );

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/campaigns" className="muted" style={{ fontSize: 13 }}>
            &larr; Back to campaigns
          </Link>
          <h2 style={{ marginTop: 6 }}>{campaign.name}</h2>
        </div>
        <span className={`badge ${campaign.status}`}>{campaign.status}</span>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Steps</h3>
        <div className="steps-list">
          {campaign.steps.map((s, idx) => {
            const template = templates.find((t) => t.id === s.template_id);
            return (
              <div className="step-row" key={s.id}>
                <div className="step-marker">
                  <span className="step-number">{s.step_order}</span>
                  {idx < campaign.steps.length - 1 && <div className="step-connector" />}
                </div>
                <div className="step-card">
                  <div className="step-card-title" style={{ marginBottom: 6 }}>
                    {template ? template.name : `#${s.template_id}`}
                  </div>
                  <span className="step-delay-readout">
                    {s.scheduled_at ? `Sends at ${formatUtc(s.scheduled_at)}` : formatDelay(s.delay_hours)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>Email jobs</h3>
          <span className="live-refresh">
            {icons.refresh}
            Auto-refreshing every 8s
          </span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Contact ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Scheduled at</th>
              <th>Sent at</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td>{j.contact_id}</td>
                <td>{j.contact_name || "—"}</td>
                <td>{j.contact_email || "—"}</td>
                <td>
                  <span className={`badge ${j.status}`}>{j.status}</span>
                </td>
                <td>{formatUtc(j.scheduled_at)}</td>
                <td>{formatUtc(j.sent_at)}</td>
                <td className="muted" style={{ fontSize: 12 }}>
                  {j.error_message || "—"}
                </td>
              </tr>
            ))}
            {jobs.length === 0 && (
              <tr>
                <td colSpan={7} className="muted">
                  No jobs yet — start the campaign to queue emails.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}