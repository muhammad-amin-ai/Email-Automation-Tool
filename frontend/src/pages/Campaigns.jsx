import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { icons } from "../components/icons.jsx";
import { useConfirm } from "../context/ConfirmContext.jsx";

// Turns "48" hours into "2 days" / "1 day 6 hours" / "3 hours" so the
// step timeline reads naturally instead of showing a raw hour count.
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

export default function Campaigns() {
  const confirmAction = useConfirm();
  const [campaigns, setCampaigns] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState([
    { template_id: "", step_order: 1, delay_hours: 0, scheduled_at: "" },
  ]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectMode, setSelectMode] = useState(false);

  const load = async () => {
    try {
      const [c, t] = await Promise.all([api.listCampaigns(), api.listTemplates()]);
      setCampaigns(c.items);
      setTemplates(t.items);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const addStep = () => {
    setSteps([
      ...steps,
      { template_id: "", step_order: steps.length + 1, delay_hours: 0, scheduled_at: "" },
    ]);
  };

  const updateStep = (idx, field, value) => {
    const next = [...steps];
    next[idx] = { ...next[idx], [field]: value };
    setSteps(next);
  };

  const removeStep = (idx) => {
    setSteps(steps.filter((_, i) => i !== idx));
  };

  // Turns a raw hour count into a short human-readable sentence, e.g.
  // "Sends 2 days after start" instead of a bare "48". Used under the
  // delay field so the sequence reads like a timeline, not a spec sheet.
  const formatDelay = (hours) => {
    const h = Number(hours) || 0;
    if (h === 0) return "Sends immediately when the campaign starts";
    if (h % 24 === 0) {
      const d = h / 24;
      return `Sends ${d} day${d > 1 ? "s" : ""} after start`;
    }
    return `Sends ${h} hour${h > 1 ? "s" : ""} after start`;
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      const payload = {
        name,
        description,
        steps: steps
          .filter((s) => s.template_id)
          .map((s, idx) => ({
            template_id: Number(s.template_id),
            // Fall back to this step's position (1-based) if the "Step
            // order" box was left blank or cleared — an empty box would
            // otherwise be sent as 0, which the backend rejects.
            step_order: Number(s.step_order) || idx + 1,
            delay_hours: Number(s.delay_hours) || 0,
            // If an exact date/time was picked, convert the browser's
            // local wall-clock value to a UTC ISO string so the backend
            // stores/compares it correctly. Leave it out otherwise so the
            // step falls back to the relative delay_hours.
            scheduled_at: s.scheduled_at ? new Date(s.scheduled_at).toISOString() : null,
          })),
      };
      await api.createCampaign(payload);
      setMessage("Campaign created.");
      setName("");
      setDescription("");
      setSteps([{ template_id: "", step_order: 1, delay_hours: 0, scheduled_at: "" }]);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleStart = async (id) => {
    setError("");
    setMessage("");
    try {
      await api.startCampaign(id);
      setMessage("Campaign started — emails will send on the backend's schedule.");
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handlePause = async (id) => {
    try {
      await api.pauseCampaign(id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleDelete = async (id) => {
    if (!(await confirmAction("Delete this campaign? This can't be undone."))) return;
    try {
      await api.deleteCampaign(id);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const toggleSelected = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    setSelectedIds((prev) =>
      prev.length === campaigns.length ? [] : campaigns.map((c) => c.id)
    );
  };

  const runBulkAction = async (actionLabel, actionFn) => {
    setError("");
    setMessage("");
    setBulkBusy(true);
    const results = await Promise.allSettled(selectedIds.map(actionFn));
    const failed = results.filter((r) => r.status === "rejected").length;
    const succeeded = results.length - failed;
    if (succeeded > 0) {
      setMessage(
        `${actionLabel}: ${succeeded} campaign${succeeded > 1 ? "s" : ""} updated` +
          (failed > 0 ? `, ${failed} failed.` : ".")
      );
    } else if (failed > 0) {
      setError(`${actionLabel} failed for all selected campaigns.`);
    }
    setSelectedIds([]);
    setBulkBusy(false);
    await load();
  };

  const handleBulkStart = () => runBulkAction("Start", (id) => api.startCampaign(id));
  const handleBulkPause = () => runBulkAction("Pause", (id) => api.pauseCampaign(id));

  const handleBulkDelete = async () => {
    if (
      !(await confirmAction(
        `Delete ${selectedIds.length} selected campaign${selectedIds.length > 1 ? "s" : ""}? This can't be undone.`
      ))
    )
      return;
    await runBulkAction("Delete", (id) => api.deleteCampaign(id));
  };

  const enterSelectMode = () => setSelectMode(true);

  const exitSelectMode = () => {
    setSelectMode(false);
    setSelectedIds([]);
  };

  return (
    <div>
      <div className="page-header">
        <h2>Campaigns</h2>
      </div>

      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>New campaign</h3>
        {templates.length === 0 && (
          <p className="muted" style={{ fontSize: 13 }}>
            Create at least one template first.
          </p>
        )}
        <form onSubmit={handleCreate}>
          <div className="field">
            <label>Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="field">
            <label>Description</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>

          <label style={{ fontSize: 13, color: "var(--muted)" }}>Steps (sent in order, with optional delay)</label>
          <p className="muted" style={{ fontSize: 12, marginTop: 2, marginBottom: 12 }}>
            Each step picks a template, its position in the sequence, and when it sends — either a
            delay after the campaign starts, or an exact date &amp; time (which overrides the delay).
          </p>
          <div className="steps-list">
            {steps.map((s, idx) => (
              <div className="step-row" key={idx}>
                <div className="step-marker">
                  <span className="step-number">{idx + 1}</span>
                  {idx < steps.length - 1 && <div className="step-connector" />}
                </div>

                <div className="step-card">
                  <div className="step-card-top">
                    <div className="step-card-title">Step {idx + 1}</div>
                    <button type="button" className="btn secondary" onClick={() => removeStep(idx)}>
                      Remove
                    </button>
                  </div>

                  <div className="step-fields">
                    <div className="step-field">
                      <label>Email template</label>
                      <select
                        value={s.template_id}
                        onChange={(e) => updateStep(idx, "template_id", e.target.value)}
                      >
                        <option value="">Select template...</option>
                        {templates.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="step-field">
                      <label>Send order</label>
                      <input
                        type="number"
                        min={1}
                        value={s.step_order}
                        onChange={(e) => updateStep(idx, "step_order", e.target.value)}
                      />
                      <span className="hint">Position in the sequence</span>
                    </div>

                    <div className="step-field">
                      <label>Delay after start</label>
                      <input
                        type="number"
                        min={0}
                        value={s.delay_hours}
                        onChange={(e) => updateStep(idx, "delay_hours", e.target.value)}
                        placeholder="Hours"
                        disabled={!!s.scheduled_at}
                      />
                      <span className="hint">Hours after campaign starts</span>
                    </div>

                    <div className="step-field">
                      <label>Or send at exact date &amp; time</label>
                      <input
                        type="datetime-local"
                        value={s.scheduled_at}
                        onChange={(e) => updateStep(idx, "scheduled_at", e.target.value)}
                      />
                      <span className="hint">
                        {s.scheduled_at ? "Overrides the delay for this step" : "Leave blank to use the delay"}
                      </span>
                    </div>
                  </div>

                  <span className="step-delay-readout">
                    {s.scheduled_at
                      ? `Sends at an exact scheduled time`
                      : formatDelay(s.delay_hours)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button type="button" className="btn secondary" onClick={addStep} style={{ marginBottom: 14 }}>
            + Add step
          </button>
          <div>
            <button className="btn" type="submit">
              Create campaign
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <div className="table-toolbar">
          {!selectMode ? (
            <button className="btn secondary" onClick={enterSelectMode} disabled={campaigns.length === 0}>
              Select
            </button>
          ) : selectedIds.length === 0 ? (
            <div className="row-actions">
              <button className="btn secondary" onClick={toggleSelectAll}>
                Select all
              </button>
              <button className="btn secondary" onClick={exitSelectMode}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="bulk-actions-bar">
              <span>
                {selectedIds.length} campaign{selectedIds.length > 1 ? "s" : ""} selected
              </span>
              <div className="row-actions">
                <button className="btn secondary" onClick={toggleSelectAll}>
                  {selectedIds.length === campaigns.length ? "Deselect all" : "Select all"}
                </button>
                <button className="btn secondary" onClick={handleBulkStart} disabled={bulkBusy}>
                  Start
                </button>
                <button className="btn secondary" onClick={handleBulkPause} disabled={bulkBusy}>
                  Pause
                </button>
                <button className="btn danger" onClick={handleBulkDelete} disabled={bulkBusy}>
                  Delete
                </button>
                <button className="btn secondary" onClick={exitSelectMode} disabled={bulkBusy}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {selectMode && <th className="checkbox-col"></th>}
                <th>Name</th>
                <th>Status</th>
                <th>Steps</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading && campaigns.length === 0 &&
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={`skeleton-${i}`}>
                    {selectMode && <td><div className="skeleton-cell" style={{ width: "18px" }} /></td>}
                    <td><div className="skeleton-cell" style={{ width: "60%" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "50px" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "30px" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "90px" }} /></td>
                  </tr>
                ))}
              {!loading && campaigns.length === 0 && (
                <tr>
                  <td colSpan={selectMode ? 5 : 4}>
                    <div className="empty-state">
                      {icons.megaphone}
                      <p className="title">No campaigns yet</p>
                      <p>Create one above once you have at least one template ready.</p>
                    </div>
                  </td>
                </tr>
              )}
              {campaigns.map((c) => (
                <tr key={c.id}>
                  {selectMode && (
                    <td className="checkbox-col">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(c.id)}
                        onChange={() => toggleSelected(c.id)}
                        aria-label={`Select ${c.name}`}
                      />
                    </td>
                  )}
                  <td>
                    <Link to={`/campaigns/${c.id}`}>{c.name}</Link>
                  </td>
                  <td>
                    <span className={`badge ${c.status}`}>
                      <span className={`status-dot${c.status === "active" ? " pulse" : ""}`} />
                      {c.status}
                    </span>
                  </td>
                  <td>{c.steps.length}</td>
                  <td>
                    <div className="row-actions">
                      {c.status !== "active" ? (
                        <button className="btn secondary" onClick={() => handleStart(c.id)}>
                          Start
                        </button>
                      ) : (
                        <button className="btn secondary" onClick={() => handlePause(c.id)}>
                          Pause
                        </button>
                      )}
                      <button className="btn danger" onClick={() => handleDelete(c.id)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}