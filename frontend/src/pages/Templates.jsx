import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { icons } from "../components/icons.jsx";
import { useConfirm } from "../context/ConfirmContext.jsx";

const emptyForm = { name: "", subject: "", html_body: "" };

export default function Templates() {
  const confirmAction = useConfirm();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectMode, setSelectMode] = useState(false);

  const [aiPurpose, setAiPurpose] = useState("");
  const [aiTone, setAiTone] = useState("professional");
  const [aiBusy, setAiBusy] = useState(false);

  const load = async () => {
    try {
      const data = await api.listTemplates();
      setItems(data.items);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      if (editingId) {
        await api.updateTemplate(editingId, form);
        setMessage("Template updated.");
      } else {
        await api.createTemplate(form);
        setMessage("Template created.");
      }
      setForm(emptyForm);
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleEdit = (t) => {
    setEditingId(t.id);
    setForm({ name: t.name, subject: t.subject, html_body: t.html_body });
  };

  const handleDelete = async (id) => {
    if (!(await confirmAction("Delete this template? This can't be undone."))) return;
    try {
      await api.deleteTemplate(id);
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
      prev.length === items.length ? [] : items.map((t) => t.id)
    );
  };

  const enterSelectMode = () => setSelectMode(true);

  const exitSelectMode = () => {
    setSelectMode(false);
    setSelectedIds([]);
  };

  const handleBulkDelete = async () => {
    if (
      !(await confirmAction(
        `Delete ${selectedIds.length} selected template${selectedIds.length > 1 ? "s" : ""}? This can't be undone.`
      ))
    )
      return;
    setError("");
    setMessage("");
    setBulkBusy(true);
    const results = await Promise.allSettled(selectedIds.map((id) => api.deleteTemplate(id)));
    const failed = results.filter((r) => r.status === "rejected").length;
    const succeeded = results.length - failed;
    if (succeeded > 0) {
      setMessage(
        `Delete: ${succeeded} template${succeeded > 1 ? "s" : ""} removed` +
          (failed > 0 ? `, ${failed} failed.` : ".")
      );
    } else if (failed > 0) {
      setError("Delete failed for all selected templates.");
    }
    setSelectedIds([]);
    setBulkBusy(false);
    await load();
  };

  const handleAiGenerate = async () => {
    if (!aiPurpose.trim()) return;
    setAiBusy(true);
    setError("");
    try {
      const result = await api.generateEmail({ purpose: aiPurpose, tone: aiTone });
      setForm((f) => ({ ...f, subject: result.subject, html_body: result.body }));
      setMessage("AI draft inserted below — review before saving.");
    } catch (e) {
      setError(e.message);
    } finally {
      setAiBusy(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Templates</h2>
      </div>

      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Generate a draft with AI (Ollama)</h3>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            placeholder="Purpose, e.g. 'Welcome email for new subscribers'"
            value={aiPurpose}
            onChange={(e) => setAiPurpose(e.target.value)}
            style={{ flex: 2 }}
          />
          <select value={aiTone} onChange={(e) => setAiTone(e.target.value)} style={{ flex: 1 }}>
            <option value="professional">Professional</option>
            <option value="friendly">Friendly</option>
            <option value="casual">Casual</option>
            <option value="persuasive">Persuasive</option>
          </select>
          <button className="btn secondary" onClick={handleAiGenerate} disabled={aiBusy}>
            {aiBusy ? (
              <span className="btn-busy-content">
                {icons.spinner}
                Generating...
              </span>
            ) : (
              "Generate"
            )}
          </button>
        </div>
        <p className="muted" style={{ fontSize: 13 }}>
          Requires a local Ollama server running the model configured in the backend `.env`.
        </p>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{editingId ? "Edit template" : "New template"}</h3>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Name</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </div>
          <div className="field">
            <label>Subject (supports {"{{ first_name }}"}, {"{{ last_name }}"}, {"{{ email }}"})</label>
            <input
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>HTML body</label>
            <textarea
              value={form.html_body}
              onChange={(e) => setForm({ ...form, html_body: e.target.value })}
              required
            />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" type="submit">
              {editingId ? "Save changes" : "Create template"}
            </button>
            {editingId && (
              <button
                type="button"
                className="btn secondary"
                onClick={() => {
                  setEditingId(null);
                  setForm(emptyForm);
                }}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <div className="table-toolbar">
          {!selectMode ? (
            <button className="btn secondary" onClick={enterSelectMode} disabled={items.length === 0}>
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
                {selectedIds.length} template{selectedIds.length > 1 ? "s" : ""} selected
              </span>
              <div className="row-actions">
                <button className="btn secondary" onClick={toggleSelectAll}>
                  {selectedIds.length === items.length ? "Deselect all" : "Select all"}
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
                <th>Subject</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading && items.length === 0 &&
                Array.from({ length: 3 }).map((_, i) => (
                  <tr key={`skeleton-${i}`}>
                    {selectMode && <td><div className="skeleton-cell" style={{ width: "18px" }} /></td>}
                    <td><div className="skeleton-cell" style={{ width: "70%" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "85%" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "70px" }} /></td>
                  </tr>
                ))}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={selectMode ? 4 : 3}>
                    <div className="empty-state">
                      {icons.fileText}
                      <p className="title">No templates yet</p>
                      <p>Create one manually above, or generate a draft with AI.</p>
                    </div>
                  </td>
                </tr>
              )}
              {items.map((t) => (
                <tr key={t.id}>
                  {selectMode && (
                    <td className="checkbox-col">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(t.id)}
                        onChange={() => toggleSelected(t.id)}
                        aria-label={`Select ${t.name}`}
                      />
                    </td>
                  )}
                  <td>{t.name}</td>
                  <td>{t.subject}</td>
                  <td>
                    <div className="row-actions">
                      <button className="btn secondary" onClick={() => handleEdit(t)}>
                        Edit
                      </button>
                      <button className="btn danger" onClick={() => handleDelete(t.id)}>
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