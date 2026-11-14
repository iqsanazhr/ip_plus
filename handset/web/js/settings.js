/**
 * iPhone Link - Settings Drawer & Appearance Controller
 */

import { dom, state } from "./state.js";

export function toggleSettings(forceState = null) {
  state.isDrawerOpen = forceState !== null ? Boolean(forceState) : !state.isDrawerOpen;

  if (dom.controlPane) {
    dom.controlPane.hidden = !state.isDrawerOpen;
  }

  if (window.pywebview?.api?.set_drawer) {
    window.pywebview.api.set_drawer(state.isDrawerOpen);
  }
}

export function setTheme(theme) {
  state.currentTheme = theme === "light" ? "light" : "dark";
  localStorage.setItem("pane-theme", state.currentTheme);

  document.documentElement.setAttribute("data-theme", state.currentTheme);
  dom.appRoot?.setAttribute("data-theme", state.currentTheme);

  document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
    const isSelected = btn.getAttribute("data-theme-choice") === state.currentTheme;
    btn.classList.toggle("is-active", isSelected);
    btn.setAttribute("aria-checked", isSelected ? "true" : "false");
  });

  if (window.pywebview?.api?.set_theme) {
    window.pywebview.api.set_theme(state.currentTheme);
  }
}

export function initSettings() {
  dom.btnSettings?.addEventListener("click", () => toggleSettings());
  dom.btnCloseSettings?.addEventListener("click", () => toggleSettings(false));

  document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const choice = btn.getAttribute("data-theme-choice");
      setTheme(choice);
    });
  });

  // Apply initial theme
  setTheme(state.currentTheme);
}
