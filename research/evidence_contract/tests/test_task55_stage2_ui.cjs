const test = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {runInNewContext} = require('node:vm');

test('output review locks conditions before displaying predictions and requires notes for errors', () => {
  const source = readFileSync(join(__dirname, '../task55/ifv_stage2.js'), 'utf8');
  const elements = new Map();
  const field = (id) => {
    if (!elements.has(id)) elements.set(id, {value: '', add() {}, addEventListener() {}});
    return elements.get(id);
  };
  const observed = {availability: 'visible', readability: 'readable', observed_transcript: 'UNIT',
    sources: [], notes: ''};
  const packet = {packet_id: 'stage2-ui-unit', cases: [{case_id: 'CASE-unit', label: 'Unit Field',
    contract: 'C3', target_label: 'Another Field', before_evidence: observed, after_evidence: observed,
    author_reference: 'UNIT', before_image: 'unit-a.png', after_image: 'unit-b.png',
    before_output: {value: 'UNIT', structured_output_usable: true},
    after_output: {value: 'WRONG_UNIT', structured_output_usable: true}}]};
  let saved;
  runInNewContext(source, {
    window: {OUTPUT_PACKET: packet, addEventListener() {}},
    document: {getElementById: field},
    localStorage: {getItem() { return null; }, setItem(key, value) { saved = JSON.parse(value); }},
    Option: function () {}
  });
  assert.equal(field('output').hidden, true);
  assert.equal(field('after-value').textContent, '');
  field('reveal').onclick();
  assert.equal(field('output').hidden, true);
  assert.equal(saved, undefined);
  field('test_validity').value = 'valid';
  field('reason').value = 'Unit test evidence';
  field('reveal').onclick();
  assert.equal(saved['CASE-unit'].test_validity, 'valid');
  assert.equal(field('reason').disabled, true);
  assert.equal(field('after-value').textContent, 'WRONG_UNIT');
  field('before_reading').value = 'correct';
  field('after_reading').value = 'wrong_value';
  field('save').onclick();
  assert.equal(saved['CASE-unit'].after_reading, undefined);
  field('output-note').value = 'Injected mismatch';
  field('save').onclick();
  assert.equal(saved['CASE-unit'].after_reading, 'wrong_value');
});
