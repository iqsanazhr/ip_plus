/**
 * iPhone Link - Modern Modular Frontend Bootstrapper
 */

import { initRealPhoneMode, applyRealPhoneMode, toggleRealPhoneModeState } from "./real-phone.js";
import { initLandscape, toggleLandscapeMode } from "./landscape.js";
import { initSettings, toggleSettings, setTheme } from "./settings.js";
import { initKeyboardShortcuts } from "./keyboard.js";
import { initNavigation } from "./navigation.js";
import { showToast } from "./utils.js";
import { dom, state } from "./state.js";

// Expose public API methods to window for backward compatibility with pywebview & tests
window.applyRealPhoneMode = applyRealPhoneMode;
window.toggleRealPhoneModeState = toggleRealPhoneModeState;
window.toggleLandscapeMode = toggleLandscapeMode;
window.toggleSettings = toggleSettings;
window.setTheme = setTheme;
window.showToast = showToast;

export function bootstrap() {
  initRealPhoneMode();
  initLandscape();
  initSettings();
  initKeyboardShortcuts();
  initNavigation();

  // Native Window Buttons
  dom.winMin?.addEventListener("click", () => {
    window.pywebview?.api?.minimize?.();
  });

  dom.winClose?.addEventListener("click", () => {
    if (window.pywebview?.api?.close) {
      window.pywebview.api.close();
    } else {
      window.close();
    }
  });

  dom.placeholderStartBtn?.addEventListener("click", () => {
    const showScreenBtn = document.querySelector("#show-screen");
    showScreenBtn?.click();
  });
}

// Auto-bootstrap when document is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
