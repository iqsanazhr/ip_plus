/**
 * iPhone Link - Standalone macOS-Style Settings Controller
 * Handles cross-window synchronization via BroadcastChannel, Storage events, and HTTP API.
 */

(function () {
  "use strict";

  // Cross-Window Synchronization Channel
  const syncChannel = new BroadcastChannel("iphone_link_sync");

  function broadcastChange(action, payload) {
    try {
      syncChannel.postMessage({ action, payload, sender: "settings-window" });
    } catch (err) {
      console.warn("[SettingsBroadcastError]", err);
    }
  }

  // Toast Notification Helper (Emil Kowalski 160ms curve)
  let toastTimer = null;
  function showToast(message, duration = 2200) {
    const toast = document.querySelector("#settings-toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove("is-visible");
    }, duration);
  }

  // HTTP API Helpers
  async function apiGet(path) {
    try {
      const res = await fetch(path);
      if (!res.ok) return null;
      return await res.json();
    } catch (_) {
      return null;
    }
  }

  async function apiPost(path, data = {}) {
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) return null;
      return await res.json();
    } catch (_) {
      return null;
    }
  }

  // ==================== macOS Traffic Lights & Titlebar Controls ====================
  function initTrafficLights() {
    document.querySelector("#mac-btn-close")?.addEventListener("click", () => {
      if (window.pywebview?.api?.close_settings) {
        window.pywebview.api.close_settings();
      } else {
        window.close();
      }
    });

    document.querySelector("#mac-btn-min")?.addEventListener("click", () => {
      if (window.pywebview?.api?.minimize_settings) {
        window.pywebview.api.minimize_settings();
      }
    });

    document.querySelector("#mac-btn-max")?.addEventListener("click", () => {
      if (window.pywebview?.api?.maximize_settings) {
        window.pywebview.api.maximize_settings();
      }
    });

    // Double-click on content header or drag region zooms / restores window like macOS
    document.querySelector(".content-header")?.addEventListener("dblclick", () => {
      if (window.pywebview?.api?.maximize_settings) {
        window.pywebview.api.maximize_settings();
      }
    });
  }

  // ==================== Tab Switching ====================
  function initTabs() {
    const tabs = document.querySelectorAll("#sidebar-nav .nav-item");
    const panes = document.querySelectorAll(".tab-pane");
    const titleEl = document.querySelector("#category-title");
    const scrollContainer = document.querySelector("#content-scroll");

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const targetId = tab.getAttribute("data-tab");
        if (!targetId) return;

        tabs.forEach((t) => {
          t.classList.remove("is-active");
          t.setAttribute("aria-selected", "false");
        });
        tab.classList.add("is-active");
        tab.setAttribute("aria-selected", "true");

        panes.forEach((pane) => {
          const isMatch = pane.id === targetId;
          pane.hidden = !isMatch;
          pane.classList.toggle("is-active", isMatch);
        });

        const text = tab.querySelector(".nav-text")?.textContent || "Settings";
        if (titleEl) titleEl.textContent = text;
        if (scrollContainer) scrollContainer.scrollTop = 0;
      });
    });
  }

  // ==================== Search Filtering ====================
  function initSearch() {
    const searchInput = document.querySelector("#settings-search");
    if (!searchInput) return;

    searchInput.addEventListener("input", (e) => {
      const query = (e.target.value || "").trim().toLowerCase();
      const panes = document.querySelectorAll(".tab-pane");
      const tabs = document.querySelectorAll("#sidebar-nav .nav-item");

      if (!query) {
        // Restore active tab
        const activeTab = document.querySelector("#sidebar-nav .nav-item.is-active");
        const activeTabId = activeTab?.getAttribute("data-tab") || "tab-appearance";
        panes.forEach((p) => {
          p.hidden = p.id !== activeTabId;
          p.querySelectorAll(".settings-group").forEach((g) => g.classList.remove("is-filtered-out"));
        });
        tabs.forEach((t) => (t.style.display = ""));
        return;
      }

      // Filter groups across all panels
      let firstMatchedTabId = null;
      panes.forEach((pane) => {
        let paneHasMatch = false;
        const groups = pane.querySelectorAll(".settings-group");
        groups.forEach((group) => {
          const text = (group.textContent || "").toLowerCase();
          const keywords = (group.getAttribute("data-keywords") || "").toLowerCase();
          const isMatch = text.includes(query) || keywords.includes(query);
          group.classList.toggle("is-filtered-out", !isMatch);
          if (isMatch) paneHasMatch = true;
        });

        // Hide or show tab item in sidebar
        const tabBtn = document.querySelector(`#sidebar-nav .nav-item[data-tab="${pane.id}"]`);
        if (tabBtn) {
          tabBtn.style.display = paneHasMatch ? "" : "none";
        }
        if (paneHasMatch && !firstMatchedTabId) {
          firstMatchedTabId = pane.id;
        }
      });

      // Switch to first matching tab if current tab has no match
      if (firstMatchedTabId) {
        const currentActivePane = document.querySelector(".tab-pane:not([hidden])");
        if (!currentActivePane || currentActivePane.querySelectorAll(".settings-group:not(.is-filtered-out)").length === 0) {
          const targetTabBtn = document.querySelector(`#sidebar-nav .nav-item[data-tab="${firstMatchedTabId}"]`);
          targetTabBtn?.click();
        }
      }
    });
  }

  // ==================== Settings Controls & Data Binding ====================
  async function initSettingsControls() {
    // Synchronize initial state from backend persistent variables
    try {
      const be = await apiGet("/api/settings");
      if (be && typeof be === "object") {
        if (be.theme) localStorage.setItem("pane-theme", be.theme);
        if (be.realPhoneMode !== undefined) localStorage.setItem("pane-real-phone-mode", String(be.realPhoneMode));
        if (be.resolution) localStorage.setItem("pane-resolution", be.resolution);
        if (be.sharpness) localStorage.setItem("pane-sharpness", be.sharpness);
        if (be.fitMode) localStorage.setItem("pane-fit-mode", be.fitMode);
        if (be.autoRotateGame !== undefined) localStorage.setItem("pane-auto-rotate-game", be.autoRotateGame ? "on" : "off");
        else if (be.autoRotate !== undefined) localStorage.setItem("pane-auto-rotate-game", be.autoRotate ? "on" : "off");
        if (be.trackpadSpeed !== undefined) localStorage.setItem("pane-trackpad-speed", String(be.trackpadSpeed));
        if (be.crossPlatformShortcuts !== undefined) localStorage.setItem("pane-shortcuts", String(be.crossPlatformShortcuts));
        if (be.pastePcClipboard !== undefined) localStorage.setItem("pane-paste-pc", String(be.pastePcClipboard));
        if (be.recordingFolder) localStorage.setItem("pane-recording-folder", be.recordingFolder);
        if (be.crop && typeof be.crop === "object") localStorage.setItem("pane-crop-edges", JSON.stringify(be.crop));
      }
    } catch (_) {}

    // 1. Theme (Dark / Light)
    const savedTheme = localStorage.getItem("pane-theme") || "dark";
    applyTheme(savedTheme);

    document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const choice = btn.getAttribute("data-theme-choice");
        if (!choice) return;
        applyTheme(choice);
        localStorage.setItem("pane-theme", choice);
        broadcastChange("theme-changed", choice);
        apiPost("/api/settings", { theme: choice });
        if (window.pywebview?.api?.set_theme) {
          window.pywebview.api.set_theme(choice);
        }
      });
    });

    // 2. Real Phone Mode
    const realPhoneToggle = document.querySelector("#toggle-real-phone-mode");
    const isRealPhone = localStorage.getItem("pane-real-phone-mode") === "true";
    if (realPhoneToggle) {
      realPhoneToggle.checked = isRealPhone;
      realPhoneToggle.addEventListener("change", (e) => {
        const checked = e.target.checked;
        localStorage.setItem("pane-real-phone-mode", String(checked));
        broadcastChange("real-phone-changed", checked);
        apiPost("/api/settings", { realPhoneMode: checked });
        if (window.pywebview?.api?.set_real_phone_mode) {
          window.pywebview.api.set_real_phone_mode(checked);
        }
        showToast(checked ? "Real Phone Mode Enabled" : "Real Phone Mode Disabled");
      });
    }

    const btnResetRealPhoneScale = document.querySelector("#btn-reset-real-phone-scale");
    if (btnResetRealPhoneScale) {
      btnResetRealPhoneScale.addEventListener("click", async () => {
        if (window.pywebview?.api?.reset_real_phone_scale) {
          await window.pywebview.api.reset_real_phone_scale();
        }
        showToast("Real Phone scale reset to 100%");
      });
    }

    // 2b. Stream Resolution & Quality
    const savedResolution = localStorage.getItem("pane-resolution") || "1080p";
    applyResolutionButtons(savedResolution);

    document.querySelectorAll("[data-resolution-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const res = btn.getAttribute("data-resolution-choice");
        if (!res) return;
        applyResolutionButtons(res);
        localStorage.setItem("pane-resolution", res);
        broadcastChange("resolution-changed", res);
        apiPost("/api/settings", { resolution: res });
        const labels = {
          "720p": "720p Balanced",
          "1080p": "1080p Full HD",
          "2k": "2K Quad HD",
          "1440p": "2K Quad HD",
          "3k": "3K Retina Extreme",
          "4k": "4K Ultra HD",
          "native": "Ultra Native 1:1"
        };
        showToast("Resolution: " + (labels[res] || res));
      });
    });

    // 2c. Subpixel Text & Edge Sharpness
    const savedSharpness = localStorage.getItem("pane-sharpness") || "crisp";
    applySharpnessButtons(savedSharpness);

    document.querySelectorAll("[data-sharpness-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const sharp = btn.getAttribute("data-sharpness-choice");
        if (!sharp) return;
        applySharpnessButtons(sharp);
        localStorage.setItem("pane-sharpness", sharp);
        broadcastChange("sharpness-changed", sharp);
        apiPost("/api/settings", { sharpness: sharp });
        showToast(sharp === "crisp" ? "Retina Sharpness Active" : "Standard Sharpness Active");
      });
    });

    // 3. Display Fit Mode
    const savedFit = localStorage.getItem("pane-fit-mode") || "autofit";
    if (!localStorage.getItem("pane-fit-mode")) {
      try { localStorage.setItem("pane-fit-mode", "autofit"); } catch (_) {}
    }
    applyFitModeButtons(savedFit);

    document.querySelectorAll("[data-fit-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const fit = btn.getAttribute("data-fit-choice");
        if (!fit) return;
        applyFitModeButtons(fit);
        localStorage.setItem("pane-fit-mode", fit);
        broadcastChange("fit-mode-changed", fit);
        apiPost("/api/settings", { fitMode: fit });
      });
    });

    // 4. Auto-Rotate Game Mode
    const savedAutoRotate = localStorage.getItem("pane-auto-rotate-game") || "off";
    applyAutoRotateButtons(savedAutoRotate);

    document.querySelectorAll("[data-auto-rotate-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const val = btn.getAttribute("data-auto-rotate-choice");
        if (!val) return;
        applyAutoRotateButtons(val);
        localStorage.setItem("pane-auto-rotate-game", val);
        broadcastChange("auto-rotate-game-changed", val);
        apiPost("/api/settings", { autoRotateGame: val === "on" });
      });
    });

    // 5. Edge Crop Calibration
    let savedCrop = { top: 0, bottom: 0, left: 0, right: 0 };
    try {
      const parsed = JSON.parse(localStorage.getItem("pane-crop-edges") || "{}");
      savedCrop = {
        top: Number(parsed.top) || 0,
        bottom: Number(parsed.bottom) || 0,
        left: Number(parsed.left) || 0,
        right: Number(parsed.right) || 0,
      };
    } catch (_) {}

    ["top", "bottom", "left", "right"].forEach((side) => {
      const slider = document.querySelector(`#crop-${side}-slider`);
      const numInput = document.querySelector(`#crop-${side}-num`);
      if (slider && numInput) {
        slider.value = String(savedCrop[side]);
        numInput.value = String(savedCrop[side]);

        slider.addEventListener("input", (e) => {
          const val = parseInt(e.target.value, 10) || 0;
          numInput.value = String(val);
          savedCrop[side] = val;
          broadcastChange("crop-preview", savedCrop);
        });

        numInput.addEventListener("change", (e) => {
          let val = parseInt(e.target.value, 10) || 0;
          val = Math.max(0, Math.min(120, val));
          e.target.value = String(val);
          slider.value = String(val);
          savedCrop[side] = val;
          broadcastChange("crop-preview", savedCrop);
        });
      }
    });

    document.querySelector("#btn-save-crop")?.addEventListener("click", async () => {
      localStorage.setItem("pane-crop-edges", JSON.stringify(savedCrop));
      await apiPost("/api/settings", { crop: savedCrop });
      broadcastChange("crop-changed", savedCrop);
      showToast("Crop edges saved");
    });

    document.querySelector("#btn-reset-crop")?.addEventListener("click", () => {
      ["top", "bottom", "left", "right"].forEach((side) => {
        savedCrop[side] = 0;
        const slider = document.querySelector(`#crop-${side}-slider`);
        const numInput = document.querySelector(`#crop-${side}-num`);
        if (slider) slider.value = "0";
        if (numInput) numInput.value = "0";
      });
      broadcastChange("crop-preview", savedCrop);
      showToast("Crop reset to 0px");
    });

    // 5b. Screen Recording Folder Controls
    const recordingFolderInput = document.querySelector("#recording-folder-input");
    const btnBrowseRecording = document.querySelector("#btn-browse-recording-folder");
    const btnOpenRecording = document.querySelector("#btn-open-recording-folder");

    async function loadRecordingFolder() {
      try {
        let folder = "";
        if (window.pywebview?.api?.get_recording_folder) {
          const res = await window.pywebview.api.get_recording_folder();
          if (res && res.folder) folder = res.folder;
        } else {
          const res = await apiGet("/api/recording/folder");
          if (res && res.folder) folder = res.folder;
        }
        if (folder && recordingFolderInput) {
          recordingFolderInput.value = folder;
        }
      } catch (_) {}
    }
    loadRecordingFolder();

    if (btnBrowseRecording) {
      btnBrowseRecording.addEventListener("click", async () => {
        try {
          if (window.pywebview?.api?.choose_recording_folder) {
            const res = await window.pywebview.api.choose_recording_folder();
            if (res && res.success && res.folder) {
              if (recordingFolderInput) recordingFolderInput.value = res.folder;
              showToast("Recording folder updated successfully");
            }
          } else {
            const current = recordingFolderInput ? recordingFolderInput.value : "";
            const newFolder = prompt("Enter screen recording folder path:", current);
            if (newFolder && newFolder.trim()) {
              const trimmed = newFolder.trim();
              const res = await apiPost("/api/recording/folder", { folder: trimmed });
              if (res && res.folder) {
                if (recordingFolderInput) recordingFolderInput.value = res.folder;
                showToast("Recording folder updated successfully");
              }
            }
          }
        } catch (err) {
          showToast("Failed to select folder: " + err.message);
        }
      });
    }

    if (btnOpenRecording) {
      btnOpenRecording.addEventListener("click", async () => {
        try {
          if (window.pywebview?.api?.open_recording_folder) {
            await window.pywebview.api.open_recording_folder();
          } else {
            await apiPost("/api/recording/open", {});
          }
          showToast("Opening recording folder...");
        } catch (err) {
          showToast("Failed to open folder: " + err.message);
        }
      });
    }

    // 6. Audio Routing Controls
    const audioStatusBadge = document.querySelector("#audio-status-badge");
    const toggleAudioSink = document.querySelector("#toggle-audio-sink");
    const audioVolSlider = document.querySelector("#audio-vol-slider");
    const audioVolVal = document.querySelector("#audio-vol-val");

    async function refreshAudioStatus() {
      const res = await apiGet("/api/audio/status");
      if (res) {
        const isEnabled = Boolean(res.enabled);
        if (toggleAudioSink) toggleAudioSink.checked = isEnabled;
        updateAudioBadge(res);
        if (res.volume !== undefined && audioVolSlider) {
          audioVolSlider.value = String(res.volume);
          if (audioVolVal) audioVolVal.textContent = `${res.volume}%`;
        }
        if (isEnabled) scheduleAudioPoll();
      }
    }
    refreshAudioStatus();

    toggleAudioSink?.addEventListener("change", async (e) => {
      const shouldEnable = e.target.checked;
      if (shouldEnable) {
        if (audioStatusBadge) {
          audioStatusBadge.textContent = "◌ Connecting…";
          audioStatusBadge.classList.add("connecting");
          audioStatusBadge.classList.remove("active");
        }
      } else {
        if (audioStatusBadge) {
          audioStatusBadge.textContent = "○ Off";
          audioStatusBadge.classList.remove("active", "connecting");
        }
      }

      const res = await apiPost("/api/audio/toggle", { enable: shouldEnable, enabled: shouldEnable });
      if (res) {
        const isEnabled = Boolean(res.enabled);
        if (toggleAudioSink) toggleAudioSink.checked = isEnabled;
        updateAudioBadge(res);
        broadcastChange("audio-changed", res);
        showToast(isEnabled ? "Audio Sink Enabled" : "Audio Sink Disabled");
        if (isEnabled) {
          scheduleAudioPoll();
        } else if (audioPollTimer) {
          clearInterval(audioPollTimer);
          audioPollTimer = null;
        }
      } else {
        refreshAudioStatus();
      }
    });

    if (audioVolSlider) {
      audioVolSlider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value, 10) || 0;
        if (audioVolVal) audioVolVal.textContent = `${val}%`;
        apiPost("/api/audio/volume", { volume: val });
        broadcastChange("audio-volume-changed", val);
      });
    }

    document.querySelector("#btn-audio-pair")?.addEventListener("click", () => {
      apiPost("/api/audio/pair");
      showToast("Opening Windows Bluetooth Settings...");
    });

    // 7. Trackpad & Gestures
    let currentSpeed = parseInt(localStorage.getItem("pane-trackpad-speed"), 10) || 100;
    const speedSlider = document.querySelector("#trackpad-speed-slider");
    const speedNum = document.querySelector("#trackpad-speed-num");

    function applySpeedUI(speed) {
      currentSpeed = speed;
      if (speedSlider) speedSlider.value = String(speed);
      if (speedNum) speedNum.value = String(speed);
      document.querySelectorAll("[data-speed-choice]").forEach((btn) => {
        const match = parseInt(btn.getAttribute("data-speed-choice"), 10) === speed;
        btn.classList.toggle("is-active", match);
      });
    }
    applySpeedUI(currentSpeed);

    document.querySelectorAll("[data-speed-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const val = parseInt(btn.getAttribute("data-speed-choice"), 10);
        if (val) applySpeedUI(val);
      });
    });

    speedSlider?.addEventListener("input", (e) => {
      const val = parseInt(e.target.value, 10) || 100;
      currentSpeed = val;
      if (speedNum) speedNum.value = String(val);
      document.querySelectorAll("[data-speed-choice]").forEach((b) => b.classList.remove("is-active"));
    });

    speedNum?.addEventListener("change", (e) => {
      let val = parseInt(e.target.value, 10) || 100;
      val = Math.max(30, Math.min(200, val));
      currentSpeed = val;
      e.target.value = String(val);
      if (speedSlider) speedSlider.value = String(val);
      document.querySelectorAll("[data-speed-choice]").forEach((b) => b.classList.remove("is-active"));
    });

    document.querySelector("#btn-save-speed")?.addEventListener("click", async () => {
      localStorage.setItem("pane-trackpad-speed", String(currentSpeed));
      await apiPost("/api/settings", { trackpadSpeed: currentSpeed });
      broadcastChange("trackpad-speed-changed", currentSpeed);
      showToast(`Trackpad speed saved (${currentSpeed}%)`);
    });

    // 8. Keyboard & Shortcuts
    let shortcutsEnabled = localStorage.getItem("pane-shortcuts") !== "false";
    let pastePcEnabled = localStorage.getItem("pane-paste-pc") !== "false";

    function updateKeyboardButtons() {
      document.querySelectorAll("[data-shortcut-choice]").forEach((btn) => {
        const match = (btn.getAttribute("data-shortcut-choice") === "true") === shortcutsEnabled;
        btn.classList.toggle("is-active", match);
      });
      document.querySelectorAll("[data-paste-pc-choice]").forEach((btn) => {
        const match = (btn.getAttribute("data-paste-pc-choice") === "true") === pastePcEnabled;
        btn.classList.toggle("is-active", match);
      });
    }
    updateKeyboardButtons();

    document.querySelectorAll("[data-shortcut-choice]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        shortcutsEnabled = btn.getAttribute("data-shortcut-choice") === "true";
        localStorage.setItem("pane-shortcuts", String(shortcutsEnabled));
        updateKeyboardButtons();
        broadcastChange("keyboard-shortcuts-changed", {
          crossPlatformShortcuts: shortcutsEnabled,
          pastePcClipboard: pastePcEnabled,
        });
        await apiPost("/api/settings", { crossPlatformShortcuts: shortcutsEnabled });
      });
    });

    document.querySelectorAll("[data-paste-pc-choice]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        pastePcEnabled = btn.getAttribute("data-paste-pc-choice") === "true";
        localStorage.setItem("pane-paste-pc", String(pastePcEnabled));
        updateKeyboardButtons();
        broadcastChange("keyboard-shortcuts-changed", {
          crossPlatformShortcuts: shortcutsEnabled,
          pastePcClipboard: pastePcEnabled,
        });
        await apiPost("/api/settings", { pastePcClipboard: pastePcEnabled });
      });
    });

    document.querySelector("#btn-clear-copy-cache")?.addEventListener("click", async () => {
      await apiPost("/api/keyboard/shortcut", { action: "clear-copy-cache" });
      showToast("Clipboard cache cleared");
    });

    document.querySelector("#btn-toggle-onscreen-kb")?.addEventListener("click", async () => {
      await apiPost("/api/keyboard/toggle-onscreen");
      showToast("Toggled iOS Keyboard");
    });

    // Modern Shortcuts Interactive Filter & Reset Handler
    const shortcutsFilterInput = document.querySelector("#shortcuts-filter-input");
    const emptyState = document.querySelector("#shortcuts-empty-state");
    const queryEcho = document.querySelector("#search-query-echo");
    const categoryGroups = document.querySelectorAll(".shortcuts-category-group");

    if (shortcutsFilterInput) {
      shortcutsFilterInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        let totalVisible = 0;

        categoryGroups.forEach((group) => {
          let visibleInGroup = 0;
          const rows = group.querySelectorAll(".shortcut-row");
          rows.forEach((row) => {
            const name = (row.getAttribute("data-name") || "").toLowerCase();
            const keys = (row.getAttribute("data-keys") || "").toLowerCase();
            const text = row.textContent.toLowerCase();
            const matches = !query || name.includes(query) || keys.includes(query) || text.includes(query);
            if (matches) {
              row.hidden = false;
              row.removeAttribute("hidden");
              visibleInGroup++;
              totalVisible++;
            } else {
              row.hidden = true;
              row.setAttribute("hidden", "");
            }
          });

          if (visibleInGroup > 0) {
            group.hidden = false;
            group.removeAttribute("hidden");
          } else {
            group.hidden = true;
            group.setAttribute("hidden", "");
          }
        });

        if (emptyState) {
          if (totalVisible === 0 && query) {
            emptyState.classList.add("is-visible");
            if (queryEcho) queryEcho.textContent = e.target.value;
          } else {
            emptyState.classList.remove("is-visible");
          }
        }
      });
    }

    document.querySelectorAll(".shortcut-trash-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const row = btn.closest(".shortcut-row");
        const name = row?.querySelector(".shortcut-action-name")?.textContent || "Shortcut";
        showToast(`${name}: Default restored`);
      });
    });

    // 9. Screen & Security
    const pinInput = document.querySelector("#input-unlock-pin");
    if (pinInput) {
      pinInput.value = localStorage.getItem("iphone_link_unlock_pin") || "";
      pinInput.addEventListener("input", (e) => {
        localStorage.setItem("iphone_link_unlock_pin", e.target.value);
      });
    }

    const pinVisibilityBtn = document.querySelector("#btn-toggle-pin-visibility");
    const eyeOpenSvg = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="icon-eye"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    const eyeSlashSvg = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="icon-eye"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;

    pinVisibilityBtn?.addEventListener("click", () => {
      if (pinInput) {
        const isPassword = pinInput.type === "password";
        pinInput.type = isPassword ? "text" : "password";
        pinVisibilityBtn.innerHTML = isPassword ? eyeSlashSvg : eyeOpenSvg;
      }
    });

    document.querySelector("#btn-wake-unlock")?.addEventListener("click", async () => {
      const pin = pinInput?.value || "";
      await apiPost("/api/device/wake-unlock", { pin });
      showToast("Sent Wake & Unlock");
    });

    document.querySelector("#btn-lock-iphone")?.addEventListener("click", async () => {
      await apiPost("/api/device/lock");
      showToast("Sent Lock Screen");
    });

    let stealthActive = false;
    const btnStealth = document.querySelector("#btn-stealth-mode");
    btnStealth?.addEventListener("click", async () => {
      stealthActive = !stealthActive;
      btnStealth.textContent = stealthActive ? "Stealth: ON" : "Stealth: OFF";
      btnStealth.classList.toggle("ctl-accent", stealthActive);
      await apiPost("/api/device/stealth-mode", { enabled: stealthActive });
      showToast(stealthActive ? "Stealth Mode ON" : "Stealth Mode OFF");
    });

    document.querySelector("#btn-wipe-privacy")?.addEventListener("click", () => {
      localStorage.removeItem("iphone_link_unlock_pin");
      localStorage.removeItem("pane-unlock-pin");
      if (pinInput) pinInput.value = "";
      if (window.pywebview?.api?.wipe_privacy_data) {
        window.pywebview.api.wipe_privacy_data();
      }
      showToast("Saved PIN & Privacy Data Wiped");
    });

    document.querySelector("#btn-hide-to-tray")?.addEventListener("click", () => {
      if (window.pywebview?.api?.minimize_to_tray) {
        window.pywebview.api.minimize_to_tray();
      }
    });

    // 10. Connection & Devices
    let currentTransport = "usb";
    document.querySelectorAll("[data-transport]").forEach((btn) => {
      btn.addEventListener("click", () => {
        currentTransport = btn.getAttribute("data-transport") || "usb";
        document.querySelectorAll("[data-transport]").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        showToast(`Switched transport to ${currentTransport.toUpperCase()}`);
      });
    });

    document.querySelector("#btn-wifi-scan")?.addEventListener("click", async () => {
      const desc = document.querySelector("#wifi-status-desc");
      if (desc) desc.textContent = "Scanning local subnet for iPhone...";
      const res = await apiPost("/api/wifi/scan");
      if (desc) desc.textContent = res?.message || "Scan finished";
      showToast("Wi-Fi network scan completed");
    });

    document.querySelector("#btn-wifi-pair")?.addEventListener("click", async () => {
      const res = await apiPost("/api/wifi/pair");
      showToast(res?.message || "Wi-Fi pairing initiated");
    });

    async function loadDevices() {
      const listEl = document.querySelector("#devices-list");
      if (!listEl) return;
      let res = await apiGet("/api/devices");
      if (!res || !Array.isArray(res.devices) || res.devices.length === 0) {
        res = await apiGet("/api/status");
      }
      const devs = res?.devices || [];
      if (Array.isArray(devs) && devs.length > 0) {
        listEl.innerHTML = devs
          .map(
            (d) =>
              `<li class="device-item">
                <span class="device-info">
                  <svg class="device-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <rect x="5" y="2" width="14" height="20" rx="4"/>
                    <line x1="12" y1="18" x2="12.01" y2="18" stroke-width="2.5"/>
                  </svg>
                  <strong>${escapeHtml(d.name || "iPhone")}</strong> (${escapeHtml((d.udid || "").substring(0, 8))}...)
                </span>
                <span class="badge-key">${escapeHtml(d.connection_type || d.connection || "USB")}</span>
              </li>`
          )
          .join("");
      } else {
        listEl.innerHTML = `<li class="device-empty">No device currently detected</li>`;
      }
    }
    loadDevices();

    document.querySelector("#btn-refresh-devices")?.addEventListener("click", () => {
      loadDevices();
      showToast("Refreshed device list");
    });
  }

  // Helpers
  function applyTheme(theme) {
    const val = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", val);
    document.body.setAttribute("data-theme", val);
    document.querySelectorAll("[data-theme-choice]").forEach((btn) => {
      const match = btn.getAttribute("data-theme-choice") === val;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-checked", String(match));
    });
  }

  function applyResolutionButtons(res) {
    const norm = (res === "1440p") ? "2k" : res;
    document.querySelectorAll("[data-resolution-choice]").forEach((btn) => {
      const choice = btn.getAttribute("data-resolution-choice");
      const match = (choice === norm) || (choice === res);
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-checked", String(match));
    });
  }

  function applySharpnessButtons(sharp) {
    document.querySelectorAll("[data-sharpness-choice]").forEach((btn) => {
      const match = btn.getAttribute("data-sharpness-choice") === sharp;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-checked", String(match));
    });
  }

  function applyFitModeButtons(mode) {
    document.querySelectorAll("[data-fit-choice]").forEach((btn) => {
      const match = btn.getAttribute("data-fit-choice") === mode;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-checked", String(match));
    });
  }

  function applyAutoRotateButtons(val) {
    document.querySelectorAll("[data-auto-rotate-choice]").forEach((btn) => {
      const match = btn.getAttribute("data-auto-rotate-choice") === val;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-checked", String(match));
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  let audioPollTimer = null;
  function scheduleAudioPoll() {
    if (audioPollTimer) clearInterval(audioPollTimer);
    audioPollTimer = setInterval(async () => {
      const toggle = document.querySelector("#toggle-audio-sink");
      if (!toggle || !toggle.checked) {
        clearInterval(audioPollTimer);
        audioPollTimer = null;
        return;
      }
      const res = await apiGet("/api/audio/status");
      if (res) {
        updateAudioBadge(res);
        if (!res.enabled && toggle) {
          toggle.checked = false;
          clearInterval(audioPollTimer);
          audioPollTimer = null;
        }
      }
    }, 2000);
  }

  function updateAudioBadge(res) {
    const badge = document.querySelector("#audio-status-badge");
    if (!badge) return;
    const isEnabled = Boolean(res?.enabled);
    const state = (res?.state || "").toLowerCase();

    if (!isEnabled) {
      badge.textContent = "○ Off";
      badge.classList.remove("active", "connecting");
    } else if (state === "opened" || state === "active") {
      badge.textContent = "● Active";
      badge.classList.add("active");
      badge.classList.remove("connecting");
    } else {
      badge.textContent = "◌ Connecting…";
      badge.classList.remove("active");
      badge.classList.add("connecting");
    }
  }

  // Cross-Window Listener for Incoming Sync Messages
  syncChannel.onmessage = (event) => {
    const data = event.data;
    if (!data || !data.action || data.sender === "settings-window") return;

    switch (data.action) {
      case "theme-changed":
        applyTheme(data.payload);
        break;
      case "real-phone-changed": {
        const toggle = document.querySelector("#toggle-real-phone-mode");
        if (toggle) toggle.checked = Boolean(data.payload);
        break;
      }
      case "fit-mode-changed":
        applyFitModeButtons(data.payload);
        break;
      case "resolution-changed":
        applyResolutionButtons(data.payload);
        break;
      case "sharpness-changed":
        applySharpnessButtons(data.payload);
        break;
      case "crop-changed":
      case "crop-preview":
        if (data.payload) {
          ["top", "bottom", "left", "right"].forEach((side) => {
            if (data.payload[side] !== undefined) {
              const slider = document.querySelector(`#crop-${side}-slider`);
              const num = document.querySelector(`#crop-${side}-num`);
              if (slider) slider.value = String(data.payload[side]);
              if (num) num.value = String(data.payload[side]);
            }
          });
        }
        break;
      case "audio-changed": {
        const toggle = document.querySelector("#toggle-audio-sink");
        if (toggle && data.payload?.enabled !== undefined) {
          toggle.checked = Boolean(data.payload.enabled);
        }
        updateAudioBadge(data.payload);
        if (data.payload?.enabled) {
          scheduleAudioPoll();
        } else if (audioPollTimer) {
          clearInterval(audioPollTimer);
          audioPollTimer = null;
        }
        break;
      }
      case "audio-volume-changed": {
        const slider = document.querySelector("#audio-vol-slider");
        const valPill = document.querySelector("#audio-vol-val");
        if (slider) slider.value = String(data.payload);
        if (valPill) valPill.textContent = `${data.payload}%`;
        break;
      }
    }
  };

  // Listen to Storage events for multi-window synchronization
  window.addEventListener("storage", (e) => {
    if (e.key === "pane-theme" && e.newValue) {
      applyTheme(e.newValue);
    } else if (e.key === "pane-real-phone-mode") {
      const toggle = document.querySelector("#toggle-real-phone-mode");
      if (toggle) toggle.checked = e.newValue === "true";
    } else if (e.key === "pane-fit-mode" && e.newValue) {
      applyFitModeButtons(e.newValue);
    } else if (e.key === "pane-resolution" && e.newValue) {
      applyResolutionButtons(e.newValue);
    } else if (e.key === "pane-sharpness" && e.newValue) {
      applySharpnessButtons(e.newValue);
    }
  });

  // Initialize once DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    initTrafficLights();
    initTabs();
    initSearch();
    initSettingsControls();
  });
})();
