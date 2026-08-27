import React, { useEffect, useState } from "react";
import { api } from "../api.js";
import { icons } from "../components/icons.jsx";
import { useConfirm } from "../context/ConfirmContext.jsx";

const emptyForm = { email: "", first_name: "", last_name: "", status: "active" };

export default function Contacts() {
  const confirmAction = useConfirm();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selectMode, setSelectMode] = useState(false);

  const load = async () => {
    try {
      const params = search ? { search } : {};
      const data = await api.listContacts(params);
      setItems(data.items);
      setTotal(data.total);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    await load();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    try {
      if (editingId) {
        await api.updateContact(editingId, form);
        setMessage("Contact updated.");
      } else {
        await api.createContact(form);
        setMessage("Contact created.");
      }
      setForm(emptyForm);
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleEdit = (c) => {
    setEditingId(c.id);
    setForm({
      email: c.email,
      first_name: c.first_name || "",
      last_name: c.last_name || "",
      status: c.status,
    });
  };

  const handleDelete = async (id) => {
    if (!(await confirmAction("Delete this contact? This can't be undone."))) return;
    try {
      await api.deleteContact(id);
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
      prev.length === items.length ? [] : items.map((c) => c.id)
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
        `Delete ${selectedIds.length} selected contact${selectedIds.length > 1 ? "s" : ""}? This can't be undone.`
      ))
    )
      return;
    setError("");
    setMessage("");
    setBulkBusy(true);
    const results = await Promise.allSettled(selectedIds.map((id) => api.deleteContact(id)));
    const failed = results.filter((r) => r.status === "rejected").length;
    const succeeded = results.length - failed;
    if (succeeded > 0) {
      setMessage(
        `Delete: ${succeeded} contact${succeeded > 1 ? "s" : ""} removed` +
          (failed > 0 ? `, ${failed} failed.` : ".")
      );
    } else if (failed > 0) {
      setError("Delete failed for all selected contacts.");
    }
    setSelectedIds([]);
    setBulkBusy(false);
    await load();
  };

  const handleImport = async () => {
    if (!importFile) return;
    setError("");
    setMessage("");
    setImporting(true);
    try {
      const result = await api.importContacts(importFile);
      setMessage(
        `Imported ${result.imported} of ${result.total_rows} rows ` +
          `(${result.duplicates} duplicates, ${result.invalid} invalid).`
      );
      setImportFile(null);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h2>Contacts ({total})</h2>
      </div>

      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}

      <div className="card">
        <h3 style={{ marginTop: 0 }}>{editingId ? "Edit contact" : "Add contact"}</h3>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div className="field" style={{ flex: 1 }}>
              <label>First name</label>
              <input
                value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })}
              />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>Last name</label>
              <input
                value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })}
              />
            </div>
          </div>
          <div className="field">
            <label>Status</label>
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="active">Active</option>
              <option value="unsubscribed">Unsubscribed</option>
              <option value="bounced">Bounced</option>
            </select>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" type="submit">
              {editingId ? "Save changes" : "Add contact"}
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
        <h3 style={{ marginTop: 0 }}>Import from CSV</h3>
        <p className="muted" style={{ fontSize: 13 }}>
          CSV must include an <code>email</code> column. Optional: <code>first_name</code>,{" "}
          <code>last_name</code>.
        </p>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="file" accept=".csv" onChange={(e) => setImportFile(e.target.files[0])} />
          <button className="btn secondary" onClick={handleImport} disabled={!importFile || importing}>
            {importing ? (
              <span className="btn-busy-content">
                {icons.spinner}
                Importing...
              </span>
            ) : (
              "Import"
            )}
          </button>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSearch} style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          <div className="search-field">
            {icons.search}
            <input
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button className="btn secondary" type="submit">
            Search
          </button>
        </form>

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
                {selectedIds.length} contact{selectedIds.length > 1 ? "s" : ""} selected
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
                <th>Email</th>
                <th>Name</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading && items.length === 0 &&
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={`skeleton-${i}`}>
                    {selectMode && <td><div className="skeleton-cell" style={{ width: "18px" }} /></td>}
                    <td><div className="skeleton-cell" style={{ width: "80%" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "60%" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "50px" }} /></td>
                    <td><div className="skeleton-cell" style={{ width: "70px" }} /></td>
                  </tr>
                ))}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={selectMode ? 5 : 4}>
                    <div className="empty-state">
                      {icons.users}
                      <p className="title">No contacts yet</p>
                      <p>Add your first contact using the form above, or import a CSV.</p>
                    </div>
                  </td>
                </tr>
              )}
              {items.map((c) => (
                <tr key={c.id}>
                  {selectMode && (
                    <td className="checkbox-col">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(c.id)}
                        onChange={() => toggleSelected(c.id)}
                        aria-label={`Select ${c.email}`}
                      />
                    </td>
                  )}
                  <td>{c.email}</td>
                  <td>{[c.first_name, c.last_name].filter(Boolean).join(" ") || "—"}</td>
                  <td>
                    <span className={`badge ${c.status}`}>{c.status}</span>
                  </td>
                  <td>
                    <div className="row-actions">
                      <button className="btn secondary" onClick={() => handleEdit(c)}>
                        Edit
                      </button>
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