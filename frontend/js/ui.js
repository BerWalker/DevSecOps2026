/* ==========================================================================
   ui.js — layout partilhado (sidebar/topbar) e utilitários de formatação
   ========================================================================== */

const NAV_ITEMS = [
  { href: "dashboard.html", label: "Visão geral", glyph: "01" },
  { href: "campaigns.html", label: "Campanhas", glyph: "02" },
];

/**
 * Constrói o shell da aplicação (sidebar + topbar) dentro de #app-root.
 * @param {string} activeHref - ficheiro atual, para realçar o link ativo
 * @param {string} title - título mostrado na topbar
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
            <span class="sidebar__user-label">Sessão</span>
            ${escapeHtml(email)}
          </div>
          <button class="btn btn--ghost btn--sm btn--full" id="logout-btn" type="button">Terminar sessão</button>
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
    btn.textContent = "A terminar...";
  }
  try {
    await Api.logout();
  } catch {
    /* mesmo que falhe, limpamos a sessão localmente */
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
  return date.toLocaleString("pt-BR", {
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

/** Mostra um alerta dentro de um contentor; substitui o conteúdo anterior. */
function showAlert(container, message, variant = "error") {
  container.innerHTML = `<div class="alert alert--${variant}">${escapeHtml(message)}</div>`;
}

function clearAlert(container) {
  container.innerHTML = "";
}
