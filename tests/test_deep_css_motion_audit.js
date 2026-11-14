/**
 * Deep Empirical CSS Motion & Emil Kowalski Standard Audit
 * Tests handset/web/mirror.css, base.css, settings.css, etc.
 */

const fs = require("fs");
const path = require("path");
const assert = require("assert");

console.log("===============================================================================");
console.log("EMPIRICAL TEST: DEEP CSS MOTION & EMIL KOWALSKI STANDARD AUDIT");
console.log("===============================================================================\n");

const cssFiles = [
  "handset/web/mirror.css",
  "handset/web/css/base.css",
  "handset/web/css/settings.css",
  "handset/web/css/real-phone.css",
  "handset/web/css/dynamic-island.css"
];

let checksTotal = 0;
let checksPassed = 0;
let violations = [];

function check(file, description, condition, details = "") {
  checksTotal++;
  if (condition) {
    checksPassed++;
    console.log(`  [PASS] [${path.basename(file)}] ${description}`);
  } else {
    violations.push({ file, description, details });
    console.error(`  [FAIL] [${path.basename(file)}] ${description}: ${details}`);
  }
}

for (const relPath of cssFiles) {
  const fullPath = path.join(__dirname, "..", relPath);
  if (!fs.existsSync(fullPath)) continue;
  const rawContent = fs.readFileSync(fullPath, "utf8");
  // Strip CSS comments to avoid false matches on docstrings
  const content = rawContent.replace(/\/\*[\s\S]*?\*\//g, "");

  // 1. No transition: all
  const hasTransitionAll = /transition\s*:\s*all\b/i.test(content);
  check(relPath, "Explicit properties (No 'transition: all')", !hasTransitionAll, "Found transition: all in rules");

  // 2. No scale(0) entry animation
  const hasScale0 = /scale\(0(?:\.0+)?\)/i.test(content);
  check(relPath, "No scale(0) entry animation", !hasScale0, "Found scale(0) in rules");

  // 3. Durations <= 300ms
  const durationMatches = content.matchAll(/(?:transition|animation)(?:-duration)?\s*:[^;]*?(\d+(?:\.\d+)?)(m?s)/gi);
  let durationOver300 = false;
  let durationViolations = [];
  for (const m of durationMatches) {
    const val = parseFloat(m[1]);
    const unit = m[2].toLowerCase();
    const ms = unit === "s" ? val * 1000 : val;
    // exclude tiny accessibility reset like 0.01ms
    if (ms > 300) {
      durationOver300 = true;
      durationViolations.push(`${m[0].trim()} (${ms}ms)`);
    }
  }
  check(relPath, "All transition/animation durations <= 300ms", !durationOver300, durationViolations.join(", "));

  // 4. prefers-reduced-motion
  const hasReducedMotion = /@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)/i.test(rawContent);
  if (relPath === "handset/web/mirror.css" || relPath === "handset/web/css/base.css" || relPath === "handset/web/css/settings.css") {
    check(relPath, "Accessibility: @media (prefers-reduced-motion: reduce) present", hasReducedMotion, "Missing prefers-reduced-motion block");
  }

  // 5. hover protection
  if (content.includes(":hover")) {
    const hasHoverGuard = /@media\s*\(\s*hover\s*:\s*hover\s*\)\s*and\s*\(\s*pointer\s*:\s*fine\s*\)/i.test(rawContent);
    if (relPath === "handset/web/css/base.css" || relPath === "handset/web/css/settings.css") {
      check(relPath, "Touch protection: @media (hover: hover) and (pointer: fine) present", hasHoverGuard, "Unprotected :hover rules");
    }
  }
}

console.log(`\nTOTAL CHECKS: ${checksTotal} | PASSED: ${checksPassed} | VIOLATIONS: ${violations.length}`);
if (violations.length > 0) {
  process.exit(1);
} else {
  console.log(">>> DEEP CSS MOTION & EMIL KOWALSKI STANDARD EMPIRICALLY COMPLIANT! <<<\n");
}
