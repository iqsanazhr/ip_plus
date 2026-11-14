/**
 * Empirical Test Suite 4: Emil Kowalski Motion Standards & CSS Architecture Validation
 * Challenger 2 for iPhone-Link
 */

const fs = require("fs");
const path = require("path");
const assert = require("assert");

console.log("===============================================================================");
console.log("EMPIRICAL TEST SUITE 4: EMIL KOWALSKI MOTION & CSS COMPLIANCE");
console.log("===============================================================================\n");

const TARGET_FILES = [
  "handset/web/css/settings.css",
  "handset/web/mirror.css",
  "handset/web/css/real-phone.css",
  "handset/web/css/base.css",
  "handset/web/css/dynamic-island.css",
  "handset/web/css/iphone-border.css",
  "handset/web/css/drawer.css",
];

let totalChecks = 0;
let violations = [];

// Helper to strip CSS comments
function stripComments(css) {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

// Regex helpers for Emil Kowalski standards
const RGX_TRANSITION_ALL = /transition\s*:\s*([^;}]*\ball\b[^;}]*)/gi;
const RGX_SCALE_ZERO = /scale\(\s*0\s*\)/gi;
const RGX_DURATION = /(\d+(?:\.\d+)?)\s*(ms|s)/gi;

TARGET_FILES.forEach((relPath) => {
  const fullPath = path.join(__dirname, "..", relPath);
  if (!fs.existsSync(fullPath)) {
    violations.push({ file: relPath, rule: "File Existence", msg: "File not found" });
    return;
  }

  const rawCss = fs.readFileSync(fullPath, "utf8");
  const cleanCss = stripComments(rawCss);

  console.log(`Inspecting: ${relPath}`);

  // 1. Check for `transition: all`
  totalChecks++;
  let matchAll;
  while ((matchAll = RGX_TRANSITION_ALL.exec(cleanCss)) !== null) {
    violations.push({
      file: relPath,
      rule: "Hard Rule: No `transition: all`",
      msg: `Found banned 'transition: all' snippet: "${matchAll[0].trim()}"`,
    });
  }

  // 2. Check for `scale(0)`
  totalChecks++;
  let matchScale;
  while ((matchScale = RGX_SCALE_ZERO.exec(cleanCss)) !== null) {
    violations.push({
      file: relPath,
      rule: "Hard Rule: No `scale(0)`",
      msg: `Found banned 'scale(0)' snippet: "${matchScale[0].trim()}" (must use scale(0.95)+opacity)`,
    });
  }

  // 3. Check for transition/animation durations > 300ms
  // Extract all property declarations with transition or animation
  const lines = cleanCss.split("\n");
  lines.forEach((line, lineNo) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("transition:") || trimmed.startsWith("transition-duration:") ||
        trimmed.startsWith("animation:") || trimmed.startsWith("animation-duration:")) {
      totalChecks++;
      
      // Parse duration
      let durMatch;
      while ((durMatch = RGX_DURATION.exec(trimmed)) !== null) {
        const val = parseFloat(durMatch[1]);
        const unit = durMatch[2];
        const ms = unit === "s" ? val * 1000 : val;

        // Skip accessibility reset (e.g. 0.01ms)
        if (ms > 300) {
          violations.push({
            file: relPath,
            rule: "Standard: Duration <= 300ms",
            msg: `Line ${lineNo + 1}: Duration ${ms}ms exceeds 300ms maximum: "${trimmed}"`,
          });
        }
      }
    }
  });

  // 4. Check for accessibility prefers-reduced-motion in files with transitions
  if (cleanCss.includes("transition:") || cleanCss.includes("animation:")) {
    totalChecks++;
    if (!rawCss.includes("prefers-reduced-motion")) {
      violations.push({
        file: relPath,
        rule: "Accessibility: prefers-reduced-motion",
        msg: `File has transitions but lacks @media (prefers-reduced-motion: reduce)`,
      });
    }
  }

  // 5. Check for touch hover protection in interactive styles
  if (cleanCss.includes(":hover")) {
    totalChecks++;
    if (!rawCss.includes("hover: hover") && !rawCss.includes("pointer: fine")) {
      violations.push({
        file: relPath,
        rule: "Touch Protection: hover media query",
        msg: `File contains :hover pseudo-class without @media (hover: hover) and (pointer: fine) guard`,
      });
    }
  }
});

console.log(`\nTOTAL CHECKS EXECUTED: ${totalChecks}`);
console.log(`TOTAL VIOLATIONS DETECTED: ${violations.length}\n`);

if (violations.length > 0) {
  console.log("DETECTED CSS VIOLATIONS & DEVIATIONS:");
  violations.forEach((v, i) => {
    console.log(`  [${i + 1}] [${v.file}] ${v.rule}:`);
    console.log(`      ${v.msg}`);
  });
} else {
  console.log(">>> ALL CSS EMIL KOWALSKI MOTION STANDARDS PASSED WITH ZERO VIOLATIONS! <<<");
}
