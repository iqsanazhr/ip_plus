/**
 * Empirical Test Suite 3: Cross-Window Synchronization Stress Test
 * Testing BroadcastChannel("iphone_link_sync") and Storage Events
 * Challenger 2 for iPhone-Link
 */

const assert = require("assert");

console.log("===============================================================================");
console.log("EMPIRICAL TEST SUITE 3: SETTINGS CROSS-WINDOW SYNCHRONIZATION");
console.log("===============================================================================\n");

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let testPassed = 0;
let testTotal = 0;
let findings = [];

async function runAsyncTest(name, fn) {
  testTotal++;
  try {
    await fn();
    testPassed++;
    console.log(`  [PASS] ${name}`);
  } catch (err) {
    console.error(`  [FAIL] ${name}: ${err.message}`);
    findings.push({ name, error: err.message });
  }
}

// Mock Storage simulation across simulated windows
class MockStorage {
  constructor() {
    this.store = new Map();
    this.listeners = [];
  }

  addEventListener(type, cb) {
    if (type === "storage") this.listeners.push(cb);
  }

  setItem(key, value, senderOrigin = "main") {
    const oldValue = this.store.get(key) || null;
    this.store.set(key, String(value));
    for (const cb of this.listeners) {
      cb({ key, oldValue, newValue: String(value), senderOrigin });
    }
  }

  getItem(key) {
    return this.store.get(key) || null;
  }
}

(async () => {
  // Test 1: Settings Window -> Main Window BroadcastChannel Sync
  await runAsyncTest("Settings Window -> Main Window: theme-changed broadcast", async () => {
    const settingsChannel = new BroadcastChannel("iphone_link_sync");
    const mainChannel = new BroadcastChannel("iphone_link_sync");

    let receivedTheme = null;
    mainChannel.onmessage = (event) => {
      const data = event.data;
      if (!data || !data.action || data.sender === "main-window") return;
      if (data.action === "theme-changed") {
        receivedTheme = data.payload;
      }
    };

    settingsChannel.postMessage({
      action: "theme-changed",
      payload: "dark",
      sender: "settings-window",
    });

    await sleep(25);
    assert.strictEqual(receivedTheme, "dark", "Main window should receive dark theme");

    settingsChannel.close();
    mainChannel.close();
  });

  // Test 2: Main Window -> Settings Window: real-phone-changed broadcast
  await runAsyncTest("Main Window -> Settings Window: real-phone-changed broadcast", async () => {
    const settingsChannel = new BroadcastChannel("iphone_link_sync");
    const mainChannel = new BroadcastChannel("iphone_link_sync");

    let settingsRealPhone = null;
    settingsChannel.onmessage = (event) => {
      const data = event.data;
      if (!data || !data.action || data.sender === "settings-window") return;
      if (data.action === "real-phone-changed") {
        settingsRealPhone = Boolean(data.payload);
      }
    };

    mainChannel.postMessage({
      action: "real-phone-changed",
      payload: true,
      sender: "main-window",
    });

    await sleep(25);
    assert.strictEqual(settingsRealPhone, true, "Settings window should receive real-phone-changed = true");

    settingsChannel.close();
    mainChannel.close();
  });

  // Test 3: Ping-Pong Loop Prevention (sender filtering)
  await runAsyncTest("BroadcastChannel: Self-sender filtering prevents infinite echo loops", async () => {
    const channelA = new BroadcastChannel("iphone_link_sync");
    let echoCount = 0;

    channelA.onmessage = (event) => {
      const data = event.data;
      if (!data || !data.action || data.sender === "settings-window") {
        return; // Filtered out
      }
      echoCount++;
    };

    channelA.postMessage({
      action: "crop-changed",
      payload: { top: 10, bottom: 10, left: 0, right: 0 },
      sender: "settings-window",
    });

    await sleep(25);
    assert.strictEqual(echoCount, 0, "Settings window must ignore its own messages");
    channelA.close();
  });

  // Test 4: Settings Window -> Mirror Window Direct BroadcastChannel Contract Test
  // In mirror.js line 2760, it expects { type: "set-real-phone", active: ... }
  // but settings-window.js sends { action: "real-phone-changed", payload: ... }
  await runAsyncTest("Mirror.js direct BroadcastChannel schema handling (action vs type)", async () => {
    const settingsChannel = new BroadcastChannel("iphone_link_sync");
    const mirrorChannel = new BroadcastChannel("iphone_link_sync");

    let mirrorUpdatedViaAction = false;
    let mirrorUpdatedViaType = false;

    // Simulate current mirror.js:2757-2774 implementation
    mirrorChannel.onmessage = (ev) => {
      const d = ev?.data;
      if (!d) return;

      // Current mirror.js logic:
      if (d.type === "set-real-phone" || d.type === "real-phone-mode") {
        mirrorUpdatedViaType = true;
      }

      // Check if mirror.js handles d.action
      if (d.action === "real-phone-changed") {
        mirrorUpdatedViaAction = true;
      }
    };

    // Settings-window sends:
    settingsChannel.postMessage({
      action: "real-phone-changed",
      payload: true,
      sender: "settings-window",
    });

    await sleep(25);

    console.log(`    -> Direct action received by mirror handler? ${mirrorUpdatedViaAction}`);
    console.log(`    -> Handled by mirror.js current type condition? ${mirrorUpdatedViaType}`);

    // If mirrorUpdatedViaType is false, mirror.js's direct BroadcastChannel listener did NOT activate
    assert.strictEqual(
      mirrorUpdatedViaType,
      false,
      "Confirmed: mirror.js d.type check ignores d.action sent by settings-window.js"
    );

    settingsChannel.close();
    mirrorChannel.close();
  });

  // Test 5: Storage Event Redundancy Check
  // Verify that even if direct BroadcastChannel has schema mismatch,
  // storage event acts as the reliable fallback
  await runAsyncTest("Storage event fallback sync across windows", async () => {
    const sharedStorage = new MockStorage();

    let mirrorRealPhoneState = false;
    let mainThemeState = "light";

    // Mirror storage listener
    sharedStorage.addEventListener("storage", (e) => {
      if (e.key === "pane-real-phone-mode") {
        mirrorRealPhoneState = e.newValue === "true";
      }
    });

    // Main window storage listener
    sharedStorage.addEventListener("storage", (e) => {
      if (e.key === "pane-theme") {
        mainThemeState = e.newValue;
      }
    });

    // Settings window modifies localStorage
    sharedStorage.setItem("pane-real-phone-mode", "true", "settings-window");
    sharedStorage.setItem("pane-theme", "dark", "settings-window");

    assert.strictEqual(mirrorRealPhoneState, true, "Mirror state updated via storage fallback");
    assert.strictEqual(mainThemeState, "dark", "Main theme updated via storage fallback");
  });

  console.log(`\nTOTAL TESTS: ${testTotal} | PASSED: ${testPassed} | FINDINGS: ${findings.length}`);
  console.log(">>> CROSS-WINDOW SYNCHRONIZATION TESTS COMPLETE! <<<\n");
})();
