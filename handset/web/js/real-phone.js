/**
 * iPhone Link - Real Phone Mode Controller
 */

import { dom, state } from "./state.js";
import { showToast } from "./utils.js";

export function applyRealPhoneMode(active, notify = true) {
  state.isRealPhoneMode = Boolean(active);
  localStorage.setItem("pane-real-phone-mode", state.isRealPhoneMode ? "true" : "false");

  document.documentElement.classList.toggle("is-real-phone", state.isRealPhoneMode);
  document.body.classList.toggle("is-real-phone", state.isRealPhoneMode);

  if (state.isRealPhoneMode) {
    dom.appRoot?.classList.add("is-real-phone");
    dom.workspace?.classList.add("is-real-phone");
    dom.btnRealPhoneMode?.classList.add("is-active");
    if (dom.toggleRealPhoneMode) dom.toggleRealPhoneMode.checked = true;
    if (notify) showToast("Real Phone Mode Aktif (Alt+P untuk keluar)");
  } else {
    dom.appRoot?.classList.remove("is-real-phone");
    dom.workspace?.classList.remove("is-real-phone");
    dom.btnRealPhoneMode?.classList.remove("is-active");
    if (dom.toggleRealPhoneMode) dom.toggleRealPhoneMode.checked = false;
    if (notify) showToast("Kembali ke Mode Standar");
  }

  let currentAspect = state.lastDeviceAspect || (1125 / 2436);
  if (state.isLandscapeMode) {
    if (currentAspect < 1.0) currentAspect = 1.0 / currentAspect;
  } else {
    if (currentAspect > 1.0) currentAspect = 1.0 / currentAspect;
  }

  if (window.pywebview?.api?.set_real_phone_mode) {
    window.pywebview.api.set_real_phone_mode(state.isRealPhoneMode, currentAspect);
  }

  setTimeout(() => {
    dom.screenView?.contentWindow?.postMessage({ type: "resize" }, "*");
    window.pywebview?.api?.reapply_window_region?.();
  }, 40);
  setTimeout(() => {
    dom.screenView?.contentWindow?.postMessage({ type: "resize" }, "*");
    window.pywebview?.api?.reapply_window_region?.();
  }, 180);
}

export function toggleRealPhoneModeState(notify = true) {
  applyRealPhoneMode(!state.isRealPhoneMode, notify);
}

export function initRealPhoneMode() {
  dom.btnRealPhoneMode?.addEventListener("click", () => toggleRealPhoneModeState(true));
  dom.toggleRealPhoneMode?.addEventListener("change", (e) => applyRealPhoneMode(e.target.checked, true));

  // Dynamic Island Buttons
  dom.islandBtnNormal?.addEventListener("click", (e) => {
    e.stopPropagation();
    applyRealPhoneMode(false, true);
  });
  dom.islandBtnMin?.addEventListener("click", (e) => {
    e.stopPropagation();
    window.pywebview?.api?.minimize?.();
  });
  dom.islandBtnClose?.addEventListener("click", (e) => {
    e.stopPropagation();
    if (window.pywebview?.api?.close) {
      window.pywebview.api.close();
    } else {
      window.close();
    }
  });

  // Proportional Aspect Ratio Resize Grip
  dom.phoneResizeGrip?.addEventListener("mousedown", (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.pywebview?.api?.start_window_resize) {
      window.pywebview.api.start_window_resize("bottom_right");
    }
  });

  // Apply initial state from localStorage
  if (state.isRealPhoneMode) {
    applyRealPhoneMode(true, false);
  }
}
