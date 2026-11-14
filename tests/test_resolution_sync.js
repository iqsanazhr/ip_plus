const fs = require("fs");
const path = require("path");
const assert = require("assert");

console.log("===============================================================================");
console.log("EMPIRICAL TEST: RESOLUTION & SHARPNESS MULTIPLIER AND SYNC AUDIT (INCLUDING 3K & 4K)");
console.log("===============================================================================\n");

const mirrorSrc = fs.readFileSync(path.join(__dirname, "..", "handset", "web", "mirror.js"), "utf8");

// 1. Verify getResolutionMultiplier logic
assert(mirrorSrc.includes('streamResolution === "720p"'), "Must handle 720p resolution");
assert(mirrorSrc.includes('streamResolution === "1080p"'), "Must handle 1080p resolution");
assert(mirrorSrc.includes('streamResolution === "2k"') || mirrorSrc.includes('streamResolution === "1440p"'), "Must handle 2k/1440p resolution");
assert(mirrorSrc.includes('streamResolution === "3k"'), "Must handle 3k resolution");
assert(mirrorSrc.includes('streamResolution === "4k"'), "Must handle 4k resolution");
assert(mirrorSrc.includes('streamResolution === "native"'), "Must handle native resolution");

// 2. Extract getResolutionMultiplier and test multipliers
const multMatch = mirrorSrc.match(/function getResolutionMultiplier\(\)\s*\{([\s\S]*?)\n\}/);
assert(multMatch, "getResolutionMultiplier function must exist in mirror.js");

const testMultFn = new Function("streamResolution", "window", `
  ${multMatch[1]}
`);

assert.strictEqual(testMultFn("720p", { devicePixelRatio: 2 }), 0.75, "720p should yield 0.75 multiplier");
assert.strictEqual(testMultFn("1080p", { devicePixelRatio: 2 }), 1.0, "1080p should yield 1.0 multiplier");
assert.strictEqual(testMultFn("2k", { devicePixelRatio: 2 }), 1.33, "2k should yield 1.33 multiplier");
assert.strictEqual(testMultFn("1440p", { devicePixelRatio: 2 }), 1.33, "1440p alias should yield 1.33 multiplier");
assert.strictEqual(testMultFn("3k", { devicePixelRatio: 2 }), 1.66, "3k should yield 1.66 multiplier");
assert.strictEqual(testMultFn("4k", { devicePixelRatio: 2 }), 2.0, "4k should yield 2.0 multiplier");
assert.strictEqual(testMultFn("native", { devicePixelRatio: 2 }), 2.0, "native should yield DPR multiplier");
assert.strictEqual(testMultFn("native", { devicePixelRatio: 1 }), 1.5, "native should clamp to minimum 1.5");
console.log("  [PASS] Resolution multipliers for 720p, 1080p, 2K, 3K, 4K, native verified");

// 3. Verify BroadcastChannel handlers in mirror.js
assert(mirrorSrc.includes('d.action === "resolution-changed"') || mirrorSrc.includes('d.type === "set-resolution"'), "mirror.js must handle resolution broadcast");
assert(mirrorSrc.includes('d.action === "sharpness-changed"') || mirrorSrc.includes('d.type === "set-sharpness"'), "mirror.js must handle sharpness broadcast");
console.log("  [PASS] mirror.js sync handlers for resolution-changed and sharpness-changed verified");

// 4. Verify settings.html contains UI controls for 3K and 4K
const settingsHtml = fs.readFileSync(path.join(__dirname, "..", "handset", "web", "settings.html"), "utf8");
assert(settingsHtml.includes('data-resolution-choice="720p"'), "settings.html must contain 720p button");
assert(settingsHtml.includes('data-resolution-choice="1080p"'), "settings.html must contain 1080p button");
assert(settingsHtml.includes('data-resolution-choice="2k"'), "settings.html must contain 2k button");
assert(settingsHtml.includes('data-resolution-choice="3k"'), "settings.html must contain 3k button");
assert(settingsHtml.includes('data-resolution-choice="4k"'), "settings.html must contain 4k button");
assert(settingsHtml.includes('data-resolution-choice="native"'), "settings.html must contain native button");
assert(settingsHtml.includes('data-sharpness-choice="crisp"'), "settings.html must contain crisp sharpness button");
assert(settingsHtml.includes('data-sharpness-choice="standard"'), "settings.html must contain standard sharpness button");
console.log("  [PASS] settings.html 720p, 1080p, 2K, 3K, 4K, native controls present and valid");

// 5. Verify zero emojis in new settings markup
const resSection = settingsHtml.substring(settingsHtml.indexOf("Stream Resolution &amp; Quality"), settingsHtml.indexOf("Display Scaling &amp; Rotation"));
const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
assert(!emojiRegex.test(resSection), "No emojis allowed in resolution settings section");
console.log("  [PASS] Zero emojis verified in resolution settings markup");

console.log("\n>>> ALL RESOLUTION & SHARPNESS TESTS (INCLUDING 3K & 4K) PASSED! <<<");
