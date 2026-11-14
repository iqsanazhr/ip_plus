/**
 * iPhone Link - Landscape & Orientation Controller
 */

import { dom, state } from "./state.js";
import { showToast } from "./utils.js";

export function toggleLandscapeMode() {
  state.isLandscapeMode = !state.isLandscapeMode;
  dom.appRoot?.classList.toggle("is-landscape", state.isLandscapeMode);

  const badge = document.querySelector("#rotate-mode-badge");
  badge?.classList.toggle("is-landscape", state.isLandscapeMode);

  if (window.pywebview?.api?.set_orientation) {
    window.pywebview.api.set_orientation(state.isLandscapeMode, state.isDrawerOpen);
  }

  showToast(state.isLandscapeMode ? "Mode Landscape (Horizontal)" : "Mode Portrait (Vertikal)");

  setTimeout(() => {
    dom.screenView?.contentWindow?.postMessage({ type: "resize" }, "*");
  }, 100);
}

export function initLandscape() {
  dom.btnRotateLandscape?.addEventListener("click", toggleLandscapeMode);
  dom.islandBtnRotate?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleLandscapeMode();
  });
}
