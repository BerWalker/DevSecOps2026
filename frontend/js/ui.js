/* ==========================================================================
   ui.js — shared layout (sidebar/topbar) and formatting utilities
   ========================================================================== */

const NAV_ITEMS = [
  { href: "dashboard.html", label: "Overview", glyph: "01" },
  { href: "campaigns.html", label: "Campaigns", glyph: "02" },
];

/**
 * Builds the application shell (sidebar + topbar) inside #app-root.
 * @param {string} activeHref - current file, to highlight the active link
 * @param {string} title - title shown in the topbar
 */
function renderShell(activeHref, title) {
  const root = document.getElementById("app-root");
  const email = Session.getEmail() || "—";

  const navHtml = NAV_ITEMS.map((item) => {
    const active = item.href === activeHref ? " is-active" : "";
    return `<a class="sidebar__link${active}" href="${item.href}">
      <span class="sidebar__link-glyph">${item.glyph}</span>${item.label}
    </a>`;
  }).join("");

  root.innerHTML = `
    <div class="app">
      <aside class="sidebar">
        <div class="sidebar__brand">
          <span class="sidebar__brand-mark"></span>
          <span class="sidebar__brand-text">phishguard<span>/console</span></span>
        </div>
        <nav>${navHtml}</nav>
        <div class="sidebar__footer">
          <div class="sidebar__user">
            <span class="sidebar__user-label">Session</span>
            ${escapeHtml(email)}
          </div>
          <button class="btn btn--ghost btn--sm btn--full" id="logout-btn" type="button">Sign out</button>
        </div>
      </aside>
      <div class="main">
        <header class="topbar">
          <h1>${escapeHtml(title)}</h1>
          <span class="topbar__meta" id="topbar-meta"></span>
        </header>
        <div class="content" id="content"></div>
      </div>
    </div>
  `;

  document.getElementById("logout-btn").addEventListener("click", handleLogout);
  return document.getElementById("content");
}

async function handleLogout() {
  const btn = document.getElementById("logout-btn");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Signing out...";
  }
  try {
    await Api.logout();
  } catch {
    /* even if it fails, clear the local session */
  }
  Session.clear();
  window.location.href = "index.html";
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value === null || value === undefined ? "" : String(value);
  return div.innerHTML;
}

function formatDateTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("en-US", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatPercent(rate) {
  if (rate === null || rate === undefined) return "0%";
  return `${Math.round(rate * 1000) / 10}%`;
}

function setTopbarMeta(text) {
  const el = document.getElementById("topbar-meta");
  if (el) el.textContent = text;
}

/** Shows an alert inside a container; replaces previous content. */
function showAlert(container, message, variant = "error") {
  container.innerHTML = `<div class="alert alert--${variant}">${escapeHtml(message)}</div>`;
}

function clearAlert(container) {
  container.innerHTML = "";
}
