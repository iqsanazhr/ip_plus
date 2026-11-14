/**
 * Empirical Verification of handset/web/mirror.js BroadcastChannel message handler
 * Author: Challenger Re-verification (teamwork_challenger_verif_1)
 */

const fs = require("fs");
const path = require("path");
const assert = require("assert");

console.log("===============================================================================");
console.log("EMPIRICAL TEST: MIRROR.JS BROADCASTCHANNEL HANDLER & SCHEMA COMPLIANCE");
console.log("===============================================================================\n");

// Read mirror.js directly
const mirrorSrc = fs.readFileSync(path.join(__dirname, "..", "handset", "web", "mirror.js"), "utf8");

// Extract the BroadcastChannel onmessage handler block from mirror.js
// Lines 2757-2775: syncChannel.onmessage = (ev) => { ... };
const match = mirrorSrc.match(/syncChannel\.onmessage\s*=\s*\(ev\)\s*=>\s*\{([\s\S]*?)\n\s*\};\s*\n\s*\}\s*\n\s*\}\s*catch/);
assert(match, "Failed to locate syncChannel.onmessage handler in mirror.js");

const handlerBody = match[1];
console.log("Successfully extracted onmessage handler from mirror.js directly.\n");

// Test harness state
let realPhoneState = null;
let fitMode = "initial";
let fitCanvasCallCount = 0;
let drawFrameCallCount = 0;
let lastFrame = null;

function updateRealPhoneState(active) {
  realPhoneState = active;
}

function fitCanvas() {
  fitCanvasCallCount++;
}

function drawFrame(frame) {
  drawFrameCallCount++;
}

// Instantiate handler function with mock environment
const handler = new Function(
  "ev",
  "updateRealPhoneState",
  "fitCanvas",
  "drawFrame",
  "getLastFrame",
  "getFitMode",
  "setFitMode",
  `
  let lastFrame = getLastFrame();
  let fitMode = getFitMode();
  ${handlerBody}
  setFitMode(fitMode);
`
);

function dispatch(evData) {
  handler(
    { data: evData },
    updateRealPhoneState,
    fitCanvas,
    drawFrame,
    () => lastFrame,
    () => fitMode,
    (m) => { fitMode = m; }
  );
}

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  [PASS] ${name}`);
  } catch (err) {
    failed++;
    console.error(`  [FAIL] ${name}: ${err.message}`);
  }
}

// 1. Settings Window -> real-phone-changed (true)
test("action: 'real-phone-changed' with payload: true updates realPhoneState and calls fitCanvas", () => {
  fitCanvasCallCount = 0;
  dispatch({ action: "real-phone-changed", payload: true, sender: "settings-window" });
  assert.strictEqual(realPhoneState, true);
  assert.strictEqual(fitCanvasCallCount, 1);
});

// 2. Settings Window -> real-phone-changed (false)
test("action: 'real-phone-changed' with payload: false updates realPhoneState", () => {
  dispatch({ action: "real-phone-changed", payload: false, sender: "settings-window" });
  assert.strictEqual(realPhoneState, false);
});

// 3. Settings Window -> fit-mode-changed (contain)
test("action: 'fit-mode-changed' with payload: 'contain' sets fitMode = 'contain'", () => {
  fitCanvasCallCount = 0;
  dispatch({ action: "fit-mode-changed", payload: "contain", sender: "settings-window" });
  assert.strictEqual(fitMode, "contain");
  assert.strictEqual(fitCanvasCallCount, 1);
});

// 4. Settings Window -> fit-mode-changed (fill)
test("action: 'fit-mode-changed' with payload: 'fill' sets fitMode = 'fill'", () => {
  dispatch({ action: "fit-mode-changed", payload: "fill", sender: "settings-window" });
  assert.strictEqual(fitMode, "fill");
});

// 5. Settings Window -> fit-mode-changed (autofit)
test("action: 'fit-mode-changed' with payload: 'autofit' sets fitMode = 'autofit'", () => {
  dispatch({ action: "fit-mode-changed", payload: "autofit", sender: "settings-window" });
  assert.strictEqual(fitMode, "autofit");
});

// 6. Settings Window -> fit-mode-changed (unrecognized string falls back to autofit)
test("action: 'fit-mode-changed' with invalid payload falls back to 'autofit'", () => {
  dispatch({ action: "fit-mode-changed", payload: "stretch_xyz", sender: "settings-window" });
  assert.strictEqual(fitMode, "autofit");
});

// 7. Legacy schema: type: 'set-real-phone', active: true
test("Legacy type: 'set-real-phone' with active: true", () => {
  dispatch({ type: "set-real-phone", active: true });
  assert.strictEqual(realPhoneState, true);
});

// 8. Legacy schema: type: 'real-phone-mode', enabled: false
test("Legacy type: 'real-phone-mode' with enabled: false", () => {
  dispatch({ type: "real-phone-mode", enabled: false });
  assert.strictEqual(realPhoneState, false);
});

// 9. Legacy schema: type: 'real-phone-mode', value: true
test("Legacy type: 'real-phone-mode' with value: true", () => {
  dispatch({ type: "real-phone-mode", value: true });
  assert.strictEqual(realPhoneState, true);
});

// 10. Legacy schema: type: 'set-fit-mode', mode: 'contain'
test("Legacy type: 'set-fit-mode' with mode: 'contain'", () => {
  dispatch({ type: "set-fit-mode", mode: "contain" });
  assert.strictEqual(fitMode, "contain");
});

// 11. Redraw on lastFrame availability
test("drawFrame called when lastFrame is present", () => {
  lastFrame = { width: 1179, height: 2556 };
  drawFrameCallCount = 0;
  dispatch({ action: "real-phone-changed", payload: true });
  assert.strictEqual(drawFrameCallCount, 1);
  dispatch({ action: "fit-mode-changed", payload: "contain" });
  assert.strictEqual(drawFrameCallCount, 2);
  lastFrame = null;
});

// 12. Robustness: null / undefined / empty message handling
test("Handles null, empty object, and malformed messages without throwing", () => {
  assert.doesNotThrow(() => dispatch(null));
  assert.doesNotThrow(() => dispatch(undefined));
  assert.doesNotThrow(() => dispatch({}));
  assert.doesNotThrow(() => dispatch({ action: "unrelated-action", payload: 123 }));
  assert.doesNotThrow(() => dispatch("plain string message"));
});

console.log(`\nTOTAL TESTS: ${passed + failed} | PASSED: ${passed} | FAILED: ${failed}`);
if (failed > 0) {
  process.exit(1);
} else {
  console.log(">>> MIRROR.JS BROADCASTCHANNEL HANDLER EMPIRICALLY VERIFIED WITH ZERO ERRORS! <<<\n");
}
