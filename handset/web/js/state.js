/**
 * iPhone Link - Centralized State & DOM References
 */

export const dom = {
  appRoot: document.querySelector("#app-root"),
  appBar: document.querySelector(".app-bar"),
  mainBody: document.querySelector("#main-body"),
  displayCol: document.querySelector("#display-col"),
  workspace: document.querySelector("#workspace"),
  phoneShell: document.querySelector("#phone-shell"),
  phoneScreen: document.querySelector("#phone-screen"),
  screenView: document.querySelector("#screen-view"),
  screenEmpty: document.querySelector("#screen-empty"),
  placeholderStartBtn: document.querySelector("#placeholder-start-btn"),
  controlPane: document.querySelector("#control-pane"),
  quickNav: document.querySelector("#quick-nav"),
  toastNotification: document.querySelector("#toast-notification"),
  phoneResizeGrip: document.querySelector("#phone-resize-grip"),
  dynamicIslandNotch: document.querySelector("#dynamic-island-notch"),

  // Buttons
  btnRealPhoneMode: document.querySelector("#btn-real-phone-mode"),
  toggleRealPhoneMode: document.querySelector("#toggle-real-phone-mode"),
  btnRotateLandscape: document.querySelector("#btn-rotate-landscape"),
  btnSettings: document.querySelector("#btn-settings"),
  btnCloseSettings: document.querySelector("#close-settings"),
  btnAudioTop: document.querySelector("#btn-audio-top"),
  btnAudioDrawer: document.querySelector("#btn-audio-drawer"),
  audioVolSlider: document.querySelector("#audio-vol-slider"),
  audioVolVal: document.querySelector("#audio-vol-val"),
  btnAudioPair: document.querySelector("#btn-audio-pair"),
  audioStatusBadge: document.querySelector("#audio-status-badge"),

  // Dynamic Island Buttons
  islandBtnRotate: document.querySelector("#island-btn-rotate"),
  islandBtnNormal: document.querySelector("#island-btn-normal"),
  islandBtnMin: document.querySelector("#island-btn-min"),
  islandBtnClose: document.querySelector("#island-btn-close"),

  // Window Controls
  winMin: document.querySelector("#win-min"),
  winClose: document.querySelector("#win-close"),
  winMax: document.querySelector("#win-max"),
};

export const state = {
  isRealPhoneMode: localStorage.getItem("pane-real-phone-mode") === "true",
  isLandscapeMode: false,
  isFullSize: false,
  isDrawerOpen: false,
  audioSinkEnabled: false,
  audioVolume: 100,
  currentTheme: localStorage.getItem("pane-theme") || "dark",
  lastDeviceAspect: 1125 / 2436,
  crop: {
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
  },
};
