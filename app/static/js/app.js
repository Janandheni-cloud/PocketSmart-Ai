/* PocketSmart AI - frontend logic (no build step, plain JS). */

const TOKEN_KEY = "pocketsmart_token";

/** Small fetch wrapper: sets JSON headers (unless sending FormData) and throws on non-2xx. */
async function api(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
    ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
  };
  const res = await fetch(url, { ...options, headers });
  let data = {};
  try {
    data = await res.json();
  } catch {
    /* no JSON body */
  }
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: "Bearer " + token } : {};
}

/** Same as api(), but attaches the bearer token from localStorage. */
async function authed(url, options = {}) {
  options.headers = { ...(options.headers || {}), ...authHeaders() };
  return api(url, options);
}

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m])
  );
}

function bindLogin() {
  const form = document.getElementById("loginForm");
  form.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const body = Object.fromEntries(new FormData(e.target));
      const result = await api("/api/auth/login", { method: "POST", body: JSON.stringify(body) });
      saveToken(result.access_token);
      location.href = "/dashboard";
    } catch (err) {
      document.getElementById("message").textContent = err.message;
    }
  };
}

function bindRegister() {
  const form = document.getElementById("registerForm");
  form.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const body = Object.fromEntries(new FormData(e.target));
      const result = await api("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(body),
      });
      saveToken(result.access_token);
      location.href = "/dashboard";
    } catch (err) {
      document.getElementById("message").textContent = err.message;
    }
  };
}

function renderResult(data) {
  const modeNote = data.ai_used
    ? "Gemini AI used"
    : "Fallback mode used (add GEMINI_API_KEY for AI)";

  const recommendationsHtml = data.recommendations
    .map(
      (r) => `
      <div class="recommendation">
        <strong>${escapeHtml(r.name)}</strong>
        <div class="small">${escapeHtml(r.category)} · ${escapeHtml(r.platform)}</div>
        <div class="price">₹${Number(r.estimated_price).toLocaleString("en-IN")}</div>
        <p>${escapeHtml(r.reason)}</p>
        <a href="${r.search_url}" target="_blank" rel="noopener">Search on ${escapeHtml(r.platform)}</a>
      </div>`
    )
    .join("");

  const tipsHtml = data.tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("");

  document.getElementById("result").innerHTML = `
    <div class="result">
      <h2>Recommendations</h2>
      <p class="small">${modeNote}</p>
      <h3>Budget allocation</h3>
      <pre>${escapeHtml(JSON.stringify(data.allocation, null, 2))}</pre>
      ${recommendationsHtml}
      <h3>Tips</h3>
      <ul>${tipsHtml}</ul>
      <p class="small">${escapeHtml(data.disclaimer)}</p>
    </div>`;
}

function bindPlanner(formId, url) {
  const form = document.getElementById(formId);
  form.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const body = Object.fromEntries(new FormData(e.target));
      body.budget = Number(body.budget);
      if (body.guests) body.guests = Number(body.guests);
      const result = await authed(url, { method: "POST", body: JSON.stringify(body) });
      renderResult(result);
    } catch (err) {
      document.getElementById("result").innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  };
}

function bindJewelry() {
  const form = document.getElementById("jewelryForm");
  form.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const result = await authed("/api/generate-jewelry", {
        method: "POST",
        body: new FormData(e.target),
      });
      renderResult(result);
    } catch (err) {
      document.getElementById("result").innerHTML = `<p class="error">${escapeHtml(err.message)}</p>`;
    }
  };
}

async function loadDashboard() {
  try {
    const session = await authed("/api/auth/session-info");
    document.getElementById("welcome").textContent = `Welcome, ${session.user.name}`;

    const historyItems = await authed("/api/history");
    document.getElementById("recent").innerHTML =
      historyItems
        .slice(0, 5)
        .map(
          (item) => `
          <div class="recommendation">
            <strong>${escapeHtml(item.planner)}</strong>
            <div class="small">${escapeHtml(item.created_at)}</div>
          </div>`
        )
        .join("") || "<p>No recommendations yet.</p>";
  } catch {
    location.href = "/login";
  }
}

async function loadHistory() {
  try {
    const historyItems = await authed("/api/history");
    document.getElementById("history").innerHTML =
      historyItems
        .map(
          (item) => `
          <div class="recommendation">
            <h3>${escapeHtml(item.planner.toUpperCase())}</h3>
            <div class="small">${escapeHtml(item.created_at)}</div>
            <p>Budget: ₹${Number(item.request.budget).toLocaleString("en-IN")}</p>
            <a href="/api/recommendations-details/${item.id}" target="_blank">Open JSON details</a>
          </div>`
        )
        .join("") || "<p>No history yet.</p>";
  } catch {
    location.href = "/login";
  }
}

document.getElementById("logoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  location.href = "/login";
});
