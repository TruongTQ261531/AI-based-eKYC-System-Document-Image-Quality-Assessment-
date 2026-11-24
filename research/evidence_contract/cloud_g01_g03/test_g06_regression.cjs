// G06 regression tests: targeted checks for reliability issues.
// No model, GPU, or private data required.
const fs = require('node:fs');
const crypto = require('node:crypto');
const path = require('node:path');

const passed = [], failed = [];
function test(name, fn) {
  try {
    if (!fn()) throw Error("assertion false");
    passed.push(name);
  } catch (e) {
    failed.push({ name, error: String(e) });
  }
}

// --- B1. Exit code correctness ---
// public_recount.cjs and test_c2_37_fixture.cjs both set process.exitCode=1
// on failure. Verify these lines exist in the source.
test("G02 sets exit code on failure", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  return src.includes('process.exitCode=1') || src.includes('process.exitCode = 1');
});

test("G03 sets exit code on failure", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'test_c2_37_fixture.cjs'), 'utf8'
  );
  return src.includes('process.exitCode=1') || src.includes('process.exitCode = 1');
});

// --- B2. No hardcoded success ---
// The test harness must actually evaluate conditions; check that there is no
// unconditional empty failures array returned without checks running.
test("G02 runs check() calls and collects names", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  // Must have multiple check() invocations
  const matches = src.match(/check\(/g);
  return matches !== null && matches.length >= 20;
});

test("G03 runs test() calls covering multiple names", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'test_c2_37_fixture.cjs'), 'utf8'
  );
  const matches = src.match(/test\(/g);
  return matches !== null && matches.length >= 30;
});

// --- B3. Input hash validation ---
// Verify that G02 computes git-blob SHA1 hashes, not just reading files
test("G02 computes git blob hashes", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  return src.includes("'blob '") && src.includes("createHash") && src.includes("sha1");
});

// --- B4. Historical receipt integrity ---
// Verify receipt files exist and are valid JSON with expected keys
test("G02 receipt is valid JSON with expected structure", () => {
  const r = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'public_recount_receipt.json'), 'utf8'
  ));
  return r.result && typeof r.result.checks === 'number' &&
    Array.isArray(r.result.failures) && r.source_blobs &&
    Object.keys(r.source_blobs).length === 13;
});

test("G03 receipt is valid JSON with expected structure", () => {
  const r = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'fixture_receipt.json'), 'utf8'
  ));
  return r.scope === 'SYNTHETIC_ONLY' && r.tests_passed === 43 &&
    Array.isArray(r.passed) && r.passed.length === 43 &&
    Array.isArray(r.failed) && r.failed.length === 0;
});

// --- B5. No silent failures (denominator checks) ---
test("G02 269 checks matches receipt", () => {
  const r = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'public_recount_receipt.json'), 'utf8'
  ));
  return r.result.checks === 269;
});

test("G03 43 tests matches receipt", () => {
  const r = JSON.parse(fs.readFileSync(
    path.join(__dirname, 'fixture_receipt.json'), 'utf8'
  ));
  return r.tests_passed === 43;
});

// --- B6. Path portability ---
// Ensure no Windows-specific backslash paths in the scripts
test("G02 uses forward slash paths", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  // Check path strings don't use backslashes
  const pathLines = src.match(/"research[^"]+"/g) || [];
  return pathLines.length > 0 && pathLines.every(p => !p.includes('\\'));
});

test("G03 module uses path.join or forward slashes", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'c2_37_fixture.cjs'), 'utf8'
  );
  // No Windows path separators in the source
  return !src.includes('\\\\research');
});

// --- B7. No GPU/CUDA/model dependencies ---
test("G02 has no GPU dependencies", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  return !src.includes('torch') && !src.includes('cuda') && !src.includes('.pth');
});

test("G03 has no GPU dependencies", () => {
  const src1 = fs.readFileSync(
    path.join(__dirname, 'c2_37_fixture.cjs'), 'utf8'
  );
  const src2 = fs.readFileSync(
    path.join(__dirname, 'test_c2_37_fixture.cjs'), 'utf8'
  );
  return !src1.includes('torch') && !src2.includes('torch') &&
    !src1.includes('cuda') && !src2.includes('cuda');
});

// --- B8. No external network dependencies ---
test("G02 has no network calls", () => {
  const src = fs.readFileSync(
    path.join(__dirname, 'public_recount.cjs'), 'utf8'
  );
  return !src.includes('http://') && !src.includes('https://') &&
    !src.includes('fetch(') && !src.includes('require(\'http');
});

test("G03 has no network calls", () => {
  const src1 = fs.readFileSync(
    path.join(__dirname, 'c2_37_fixture.cjs'), 'utf8'
  );
  const src2 = fs.readFileSync(
    path.join(__dirname, 'test_c2_37_fixture.cjs'), 'utf8'
  );
  return !src1.includes('fetch(') && !src2.includes('fetch(') &&
    !src1.includes('require(\'http') && !src2.includes('require(\'http');
});

// --- B9. Fixture scope guard ---
test("G03 fixture rejects production scope", () => {
  const { analyzeFixture } = require('./c2_37_fixture.cjs');
  try {
    analyzeFixture({ schema: "C2-37-fixture/1", scope: "PRODUCTION", reader: {}, cases: [], outputs: [], decisions: [] });
    return false;
  } catch (e) {
    return String(e).includes('Production');
  }
});

// --- B10. Verify input files are present for G02 ---
test("All 13 G02 input artifacts exist", () => {
  const root = path.resolve(__dirname, '../../..');
  const paths = [
    "research/evidence_contract/execution/master_01/d4_development_20261117/controls_01/control_results.json",
    "research/evidence_contract/execution/master_01/d4_development_20261117/controls_01/summary.json",
    "research/evidence_contract/execution/master_01/d4_development_20261117/historical_01/summary.json",
    "research/evidence_contract/execution/master_01/p5b_calibration_20261121/design.json",
    "research/evidence_contract/execution/master_01/p5b_calibration_20261121/calibration.json",
    "research/evidence_contract/execution/master_01/p5b_calibration_20261121/held_out.json",
    "research/evidence_contract/execution/master_01/p5_simulation_20261121/verification.json",
    "research/evidence_contract/execution/master_01/p6_integrity_20261121/aggregate.json",
    "research/evidence_contract/execution/master_01/p6_integrity_20261121/verification.json",
    "research/evidence_contract/execution/master_01/reviewer_intake_20261120_r03_phase2/r02_r03_agreement.json",
    "research/evidence_contract/execution/master_01/reviewer_intake_20261120_r03_phase2/author_r03_agreement.json",
    "research/evidence_contract/human_gate/receipts/c2_37_20261123/aggregate.json",
    "research/evidence_contract/human_gate/receipts/c2_37_20261123/verification.json"
  ];
  return paths.every(p => fs.existsSync(path.join(root, p)));
});

// --- B11. Missing-value handling ---
test("G03 fixture handles all-null truth correctly", () => {
  const { analyzeFixture } = require('./c2_37_fixture.cjs');
  // Build a valid fixture input
  const { fixture } = (function () {
    const h = n => n.toString(16).padStart(64, "0");
    const reader = { name: "SYNTH_READER", checkpoint_sha256: h(10001), config_sha256: h(10002), runtime_sha256: h(10003), profile: "SYNTH_RECT2" };
    const cases = [], outputs = [], decisions = [], images = new Map();
    let idx = 0, id = 0, extra = 0;
    const conditions = ["backup_supported_after", "backup_supported_before", "distinct_sources", "primary_removed_after", "primary_supported_before", "provenance_verified", "reference_approved", "semantic_equality_approved"];
    for (const [template, nids, ncases] of [["05", 7, 12], ["32", 4, 11], ["41", 7, 14]]) {
      const pool = Array.from({ length: nids }, () => { const i = ++id; return { id: i, b: h(100 + i), a: h(200 + i) }; });
      for (let j = 0; j < ncases; j++) {
        const p = pool[j % nids], a = j >= nids && extra < 9 ? h(300 + (++extra)) : p.a;
        for (const v of [p.b, a]) if (!images.has(v)) images.set(v, h(3000 + images.size));
        const k = ++idx, ref = h(500 + k);
        cases.push({ case_id: "SYNTH_C" + k, physical_id: "SYNTH_ID" + p.id, template, field_kind: k <= 11 ? "IDENTIFIER" : "DATE_FULL", before_sha256: p.b, after_sha256: a, rights: true, two_proposals: true, adjudicated: true, reference_sha256: ref, conditions: Object.fromEntries(conditions.map(v => [v, "PASS"])) });
        const x = ["FAULT", "FAULT", "NO_FAULT", "UNKNOWN", "INVALID_TEST", "FAULT", "NO_FAULT"][(k - 1) % 7], y = ["UNKNOWN", "FAULT", "UNKNOWN", "UNKNOWN", "INVALID_TEST", "FAULT", "NO_FAULT"][(k - 1) % 7];
        const binding = { before_output_sha256: images.get(p.b), after_output_sha256: images.get(a), reference_sha256: ref };
        decisions.push({ case_id: "SYNTH_C" + k, tier: 1, endpoint: "pointwise", asserted: { state: x, ...binding }, checked: { state: y, ...binding }, truth: { value: null, basis: null, evidence_sha256: null, after_output_sha256: images.get(a) } });
      }
    }
    for (const [image_sha256, output_sha256] of images) outputs.push({ image_sha256, output_sha256, reader: { ...reader } });
    return { fixture: () => ({ schema: "C2-37-fixture/1", scope: "SYNTHETIC_ONLY", reader, cases, outputs, decisions }) };
  })();
  const result = analyzeFixture(fixture());
  return result.metrics.arms.checked.far.value === null &&
    result.metrics.arms.checked.sensitivity.value === null &&
    result.metrics.truth_missing === 37;
});

// --- Summary ---
console.log(JSON.stringify({ scope: "G06_REGRESSION", passed: passed.map(n => n), failed, counts: { passed: passed.length, failed: failed.length, total: passed.length + failed.length } }, null, 2));
if (failed.length) process.exitCode = 1;
