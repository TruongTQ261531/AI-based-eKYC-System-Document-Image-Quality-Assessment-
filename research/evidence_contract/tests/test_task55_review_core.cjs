const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../task55/review_core.js');

const packet = {
  packet_id: 'review-core-unit',
  purpose: 'ui_unit_control',
  pages: [{image_id: 'img', file_sha256: 'sha', fields: [{slot_id: 'F1', field_key: 'id_number'}]}]
};

test('partial draft survives backup export and load without becoming a submitted label', () => {
  const draft = core.initial(packet);
  draft.answers.F1 = {...core.blank(), touched: true, notes: 'injected unit control'};
  const backup = core.exportReview(packet, draft).value;
  assert.equal(backup.export_kind, 'draft');
  assert.equal(backup.mode, 'unit_injected');
  assert.equal(backup.items[0].entry_complete, false);
  assert.equal(core.restoreBackup(packet, backup).answers.F1.notes, draft.answers.F1.notes);
  assert.ok(core.exportReview(packet, draft, true).errors.length);
});

test('browser storage failure recommends the file fallback', () => {
  const storage = {setItem() { throw new Error('forbidden'); }};
  const result = core.saveDraft(core.initial(packet), storage);
  assert.equal(result.saved, false);
  assert.match(result.message, /JSON/);
});

test('malformed storage never overwrites a bad draft while restoring', () => {
  const corrupt = {...core.initial(packet), answers: {F1: {sources: null}}};
  const storage = {getItem() { return JSON.stringify(corrupt); }, setItem() { assert.fail('write during restore'); }};
  const result = core.restore(packet, storage);
  assert.ok(result.warning);
  assert.deepEqual(result.state, core.initial(packet));
});

test('visible observation requires per-source states, while unknown language is expressible', () => {
  const draft = core.initial(packet);
  draft.profile = {reviewer_id: 'unit', role: 'unknown', output_exposure: 'none'};
  draft.answers.F1 = {...core.blank(), touched: true, availability: 'visible', readability: 'language_unknown',
    semantic_key_confirmed: 'uncertain', prior_exposure: 'no', sources: [{kind: 'other', location: 'bottom',
      availability: 'visible', readability: 'language_unknown', observed_text: '', mrz_line_1: '', mrz_line_2: ''}]};
  assert.equal(core.progress(packet, draft).complete, 1);
  assert.equal(core.exportReview(packet, draft, true).value.items[0].readability, 'language_unknown');
  draft.answers.F1.sources[0].readability = '';
  assert.equal(core.progress(packet, draft).complete, 0);
});

test('wrong image backup is rejected', () => {
  const draft = core.initial(packet);
  draft.answers.F1 = {...core.blank(), touched: true};
  const backup = core.exportReview(packet, draft).value;
  backup.items[0].image_sha256 = 'wrong';
  assert.throws(() => core.restoreBackup(packet, backup), /không khớp/);
});
