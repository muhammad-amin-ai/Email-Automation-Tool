const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function getToken() {
  return localStorage.getItem("access_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("access_token", token);
  } else {
    localStorage.removeItem("access_token");
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  let data = null;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    let message = (data && (data.detail || data.message)) || `Request failed (${response.status})`;
    if (data && Array.isArray(data.errors) && data.errors.length > 0) {
      const details = data.errors
        .map((err) => `${err.field ? `${err.field}: ` : ""}${err.message}`)
        .join("; ");
      message = `${typeof message === "string" ? message : ""} ${details}`.trim();
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export const api = {
  register: (email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request("/auth/me"),

  listContacts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/contacts${qs ? `?${qs}` : ""}`);
  },
  createContact: (payload) => request("/contacts", { method: "POST", body: JSON.stringify(payload) }),
  updateContact: (id, payload) => request(`/contacts/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteContact: (id) => request(`/contacts/${id}`, { method: "DELETE" }),
  importContacts: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request("/contacts/import", { method: "POST", body: formData });
  },

  listTemplates: () => request("/templates"),
  createTemplate: (payload) => request("/templates", { method: "POST", body: JSON.stringify(payload) }),
  updateTemplate: (id, payload) => request(`/templates/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTemplate: (id) => request(`/templates/${id}`, { method: "DELETE" }),

  listCampaigns: () => request("/campaigns"),
  createCampaign: (payload) => request("/campaigns", { method: "POST", body: JSON.stringify(payload) }),
  updateCampaign: (id, payload) => request(`/campaigns/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteCampaign: (id) => request(`/campaigns/${id}`, { method: "DELETE" }),
  startCampaign: (id) => request(`/campaigns/${id}/start`, { method: "POST" }),
  pauseCampaign: (id) => request(`/campaigns/${id}/pause`, { method: "POST" }),
  campaignJobs: (id) => request(`/campaigns/${id}/jobs`),

  generateEmail: (payload) => request("/ai/generate-email", { method: "POST", body: JSON.stringify(payload) }),
  generateSubject: (payload) => request("/ai/generate-subject", { method: "POST", body: JSON.stringify(payload) }),
  personalizeEmail: (payload) => request("/ai/personalize-email", { method: "POST", body: JSON.stringify(payload) }),

  analyticsSummary: () => request("/analytics/summary"),
};