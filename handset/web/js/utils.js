/**
 * iPhone Link - UI Utilities & Toast Notifications
 */

import { dom } from "./state.js";

let _toastTimer = null;

export function showToast(message, duration = 2800) {
  if (!dom.toastNotification) return;

  dom.toastNotification.textContent = message;
  dom.toastNotification.classList.add("is-visible");

  if (_toastTimer) {
    window.clearTimeout(_toastTimer);
  }

  _toastTimer = window.setTimeout(() => {
    dom.toastNotification.classList.remove("is-visible");
  }, duration);
}

export function debounce(fn, wait = 150) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}
