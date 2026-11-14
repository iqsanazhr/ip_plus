/**
 * iPhone Link - Keyboard Shortcuts & Hotkey Router
 */

import { toggleRealPhoneModeState, applyRealPhoneMode } from "./real-phone.js";
import { toggleLandscapeMode } from "./landscape.js";
import { state } from "./state.js";

export function initKeyboardShortcuts() {
  window.addEventListener("keydown", (e) => {
    // Escape to exit Real Phone Mode or Fullscreen
    if (e.key === "Escape" && state.isRealPhoneMode) {
      applyRealPhoneMode(false, true);
      return;
    }

    // Alt+P: Toggle Real Phone Mode
    if (e.altKey && (e.key === "p" || e.key === "P")) {
      e.preventDefault();
      toggleRealPhoneModeState(true);
      return;
    }

    // Alt+H: Toggle Landscape / Portrait
    if (e.altKey && (e.key === "h" || e.key === "H")) {
      e.preventDefault();
      toggleLandscapeMode();
      return;
    }

    // Alt+U: Wake & Unlock iPhone
    if (e.altKey && (e.key === "u" || e.key === "U")) {
      e.preventDefault();
      if (typeof window.triggerWakeUnlockIphone === "function") {
        window.triggerWakeUnlockIphone();
      }
      return;
    }

    // Alt+L: Lock iPhone Screen
    if (e.altKey && (e.key === "l" || e.key === "L")) {
      e.preventDefault();
      if (typeof window.triggerLockIphone === "function") {
        window.triggerLockIphone();
      }
      return;
    }

    // Alt+D: Stealth Dim Mode
    if (e.altKey && (e.key === "d" || e.key === "D")) {
      e.preventDefault();
      if (typeof window.triggerToggleStealthDim === "function") {
        window.triggerToggleStealthDim();
      }
      return;
    }

    // Alt+C: Copy iOS to PC
    if (e.altKey && (e.key === "c" || e.key === "C")) {
      e.preventDefault();
      if (typeof window.triggerCopyIphoneTextWithFeedback === "function") {
        window.triggerCopyIphoneTextWithFeedback();
      }
      return;
    }

    // Alt+V: Paste PC to iPhone
    if (e.altKey && (e.key === "v" || e.key === "V")) {
      e.preventDefault();
      if (typeof window.triggerPastePcTextWithFeedback === "function") {
        window.triggerPastePcTextWithFeedback();
      }
      return;
    }

    // Alt+R: Clear Clipboard Cache
    if (e.altKey && (e.key === "r" || e.key === "R")) {
      e.preventDefault();
      if (typeof window.triggerClearCopyCacheWithFeedback === "function") {
        window.triggerClearCopyCacheWithFeedback();
      }
      return;
    }

    // Alt+B: Grab Link via QR Bridge
    if (e.altKey && (e.key === "b" || e.key === "B")) {
      e.preventDefault();
      if (typeof window.triggerScanQrLinkWithFeedback === "function") {
        window.triggerScanQrLinkWithFeedback();
      }
      return;
    }
  });
}
