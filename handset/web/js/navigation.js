/**
 * iPhone Link - Bottom Navigation & Apple Gesture Controller
 */

export function sendMirrorGesture(action, payload = {}) {
  const mirrorFrame = document.querySelector("#screen-view");
  if (mirrorFrame?.contentWindow) {
    mirrorFrame.contentWindow.postMessage({ type: "gesture", action, ...payload }, "*");
  }
}

export function initNavigation() {
  document.querySelector("#nav-home")?.addEventListener("click", () => {
    sendMirrorGesture("home");
  });

  document.querySelector("#nav-recent")?.addEventListener("click", () => {
    sendMirrorGesture("switcher");
  });

  document.querySelector("#nav-swipe-left")?.addEventListener("click", () => {
    sendMirrorGesture("swipe", { direction: "left" });
  });

  document.querySelector("#nav-swipe-right")?.addEventListener("click", () => {
    sendMirrorGesture("swipe", { direction: "right" });
  });
}
