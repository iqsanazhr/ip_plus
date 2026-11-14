/**
 * Empirical Test Suite 2: H.265 Macroblock Padding Trim Verification in drawFrame()
 * Challenger 2 for iPhone-Link
 */

const assert = require("assert");

function evaluatePaddingTrim(opts) {
  const {
    rawW = 1216,
    rawH = 2656,
    isRealPhoneActive = true,
    fitMode = "autofit",
    currentCrop = { top: 0, bottom: 0, left: 0, right: 0 },
    currentRotation = 0,
  } = opts;

  const scaleH = rawH / 2656;
  const scaleW = rawW / 1216;

  // The EXACT logic from handset/web/mirror.js:3801-3844
  const shouldTrimPadding = isRealPhoneActive || fitMode !== "contain";
  const nativeTrimTop = 0;
  const nativeTrimBot = shouldTrimPadding ? Math.round(58 * scaleH) : 0;
  const nativeTrimLeft = 0;
  const nativeTrimRight = shouldTrimPadding ? Math.round(14 * scaleW) : 0;

  const pxScale = Math.max(3, Math.round(rawW / 346));
  const uTop = Math.max(0, (Number(currentCrop.top) || 0) * pxScale);
  const uBot = Math.max(0, (Number(currentCrop.bottom) || 0) * pxScale);
  const uLeft = Math.max(0, (Number(currentCrop.left) || 0) * pxScale);
  const uRight = Math.max(0, (Number(currentCrop.right) || 0) * pxScale);

  let manualTrimTop = uTop,
    manualTrimBot = uBot,
    manualTrimLeft = uLeft,
    manualTrimRight = uRight;
  const rotNorm = ((currentRotation % 360) + 360) % 360;
  if (rotNorm === 270) {
    manualTrimTop = uLeft;
    manualTrimBot = uRight;
    manualTrimLeft = uBot;
    manualTrimRight = uTop;
  } else if (rotNorm === 90) {
    manualTrimTop = uRight;
    manualTrimBot = uLeft;
    manualTrimLeft = uTop;
    manualTrimRight = uBot;
  } else if (rotNorm === 180) {
    manualTrimTop = uBot;
    manualTrimBot = uTop;
    manualTrimLeft = uRight;
    manualTrimRight = uLeft;
  }

  const srcTrimTop = nativeTrimTop + manualTrimTop;
  const srcTrimBot = nativeTrimBot + manualTrimBot;
  const srcTrimLeft = nativeTrimLeft + manualTrimLeft;
  const srcTrimRight = nativeTrimRight + manualTrimRight;

  const cleanW = Math.max(64, rawW - srcTrimLeft - srcTrimRight);
  const cleanH = Math.max(64, rawH - srcTrimTop - srcTrimBot);
  const cleanCenterX = srcTrimLeft + cleanW / 2;
  const cleanCenterY = srcTrimTop + cleanH / 2;

  return {
    shouldTrimPadding,
    nativeTrimTop,
    nativeTrimBot,
    nativeTrimLeft,
    nativeTrimRight,
    cleanW,
    cleanH,
    cleanCenterX,
    cleanCenterY,
    srcTrimTop,
    srcTrimBot,
    srcTrimLeft,
    srcTrimRight,
  };
}

console.log("===============================================================================");
console.log("EMPIRICAL TEST SUITE 2: H.265 58PX MACROBLOCK PADDING TRIM IN drawFrame()");
console.log("===============================================================================\n");

let passed = 0;
let total = 0;

function runTest(desc, fn) {
  total++;
  try {
    fn();
    passed++;
    console.log(`  [PASS] ${desc}`);
  } catch (err) {
    console.error(`  [FAIL] ${desc}: ${err.message}`);
    throw err;
  }
}

// 1. Real Phone Mode ALWAYS enforces trimming regardless of fitMode
runTest("Real Phone Mode + contain fitMode: shouldTrimPadding must be TRUE", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: true, fitMode: "contain" });
  assert.strictEqual(res.shouldTrimPadding, true);
  assert.strictEqual(res.nativeTrimBot, 58);
  assert.strictEqual(res.nativeTrimRight, 14);
});

runTest("Real Phone Mode + autofit fitMode: shouldTrimPadding must be TRUE", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: true, fitMode: "autofit" });
  assert.strictEqual(res.shouldTrimPadding, true);
  assert.strictEqual(res.nativeTrimBot, 58);
});

runTest("Real Phone Mode + fill fitMode: shouldTrimPadding must be TRUE", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: true, fitMode: "fill" });
  assert.strictEqual(res.shouldTrimPadding, true);
  assert.strictEqual(res.nativeTrimBot, 58);
});

// 2. Non-real-phone mode behavior
runTest("Standard Mode + contain fitMode: shouldTrimPadding must be FALSE (shows raw stream)", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: false, fitMode: "contain" });
  assert.strictEqual(res.shouldTrimPadding, false);
  assert.strictEqual(res.nativeTrimBot, 0);
  assert.strictEqual(res.nativeTrimRight, 0);
});

runTest("Standard Mode + autofit: shouldTrimPadding must be TRUE", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: false, fitMode: "autofit" });
  assert.strictEqual(res.shouldTrimPadding, true);
  assert.strictEqual(res.nativeTrimBot, 58);
});

// 3. Top and Left Trim are strictly zero to protect status bar & Dynamic Island
runTest("Top and Left native trims must strictly remain 0px", () => {
  const res = evaluatePaddingTrim({ isRealPhoneActive: true });
  assert.strictEqual(res.nativeTrimTop, 0, "nativeTrimTop must be 0");
  assert.strictEqual(res.nativeTrimLeft, 0, "nativeTrimLeft must be 0");
});

// 4. Clean geometry calculations for iPhone 17 Pro (1216 x 2656)
runTest("iPhone 17 Pro clean geometry verification", () => {
  const res = evaluatePaddingTrim({ rawW: 1216, rawH: 2656, isRealPhoneActive: true });
  assert.strictEqual(res.cleanW, 1202, "Clean width should be 1216 - 14 = 1202");
  assert.strictEqual(res.cleanH, 2598, "Clean height should be 2656 - 58 = 2598");
  assert.strictEqual(res.cleanCenterX, 601, "Clean Center X should be 601");
  assert.strictEqual(res.cleanCenterY, 1299, "Clean Center Y should be 1299");
});

// 5. Resolution scaling across diverse stream resolutions
const TEST_RESOLUTIONS = [
  { name: "iPhone 15 Pro", w: 1179, h: 2556, expectedBot: Math.round(58 * (2556 / 2656)) },
  { name: "Full HD 1080p", w: 1080, h: 1920, expectedBot: Math.round(58 * (1920 / 2656)) },
  { name: "720p HD", w: 720, h: 1280, expectedBot: Math.round(58 * (1280 / 2656)) },
  { name: "iPad Retina", w: 1536, h: 2048, expectedBot: Math.round(58 * (2048 / 2656)) },
];

for (const tr of TEST_RESOLUTIONS) {
  runTest(`Resolution scale: ${tr.name} (${tr.w}x${tr.h})`, () => {
    const res = evaluatePaddingTrim({ rawW: tr.w, rawH: tr.h, isRealPhoneActive: true });
    assert.strictEqual(res.nativeTrimBot, tr.expectedBot);
    assert(res.cleanW > 0 && res.cleanW <= tr.w);
    assert(res.cleanH > 0 && res.cleanH <= tr.h);
    assert.strictEqual(res.nativeTrimTop, 0);
  });
}

// 6. Manual Crop UI slider integration with Rotations
runTest("Manual crop UI mapping with 270° rotation", () => {
  const crop = { top: 5, bottom: 10, left: 2, right: 3 };
  const res = evaluatePaddingTrim({
    rawW: 1216,
    rawH: 2656,
    isRealPhoneActive: true,
    currentCrop: crop,
    currentRotation: 270,
  });

  // At 270 deg: manualTrimTop = uLeft, manualTrimBot = uRight, manualTrimLeft = uBot, manualTrimRight = uTop
  const pxScale = Math.round(1216 / 346); // 4
  assert.strictEqual(res.srcTrimTop, 0 + crop.left * pxScale);
  assert.strictEqual(res.srcTrimBot, 58 + crop.right * pxScale);
  assert.strictEqual(res.srcTrimLeft, 0 + crop.bottom * pxScale);
  assert.strictEqual(res.srcTrimRight, 14 + crop.top * pxScale);
});

// 7. Degradation under extreme minimal resolutions (Underflow Protection)
runTest("Underflow protection under tiny resolutions (e.g. 50x50)", () => {
  const res = evaluatePaddingTrim({ rawW: 50, rawH: 50, isRealPhoneActive: true });
  assert.strictEqual(res.cleanW, 64, "cleanW should clamp to minimum 64px");
  assert.strictEqual(res.cleanH, 64, "cleanH should clamp to minimum 64px");
});

console.log(`\nTOTAL TESTS: ${total} | PASSED: ${passed} | FAILED: 0`);
console.log(">>> ALL H.265 PADDING TRIM TESTS PASSED! <<<\n");
