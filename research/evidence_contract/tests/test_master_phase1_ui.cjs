const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = path.join(__dirname, '../task55');
const core = require(path.join(source, 'review_core.js'));

test('phase 1 wires save, JSON export, and reload with image provenance in an offline fixture', async () => {
  const packet = {packet_id: 'unit-only', purpose: 'ui_unit_control', pages: [
    {image_id: 'unit-img', image: 'images/unit.png', file_sha256: 'a'.repeat(64),
      fields: [{slot_id: 'F-test', field_key: 'field', label: 'Field label'}]}
  ]};
  const nodes = new Map();
  const callbacks = new Map();
  const local = new Map();
  const validation = {};
  const add = {};
  const section = {
    dataset: {slot: 'F-test'},
    addEventListener: (event, callback) => callbacks.set(event, callback),
    querySelector: (selector) => selector === '.add-source' ? add : validation,
    querySelectorAll: () => []
  };
  function get(id) {
    if (!nodes.has(id)) nodes.set(id, {value: ''});
    return nodes.get(id);
  }
  get('fields').querySelectorAll = () => [section];
  let download;
  const document = {
    getElementById: get, body: {append() {}}, createElement: () => ({click() {}, remove() {}})
  };
  const window = {BLIND_PACKET: packet, BlindReviewCore: core, confirm: () => true,
    localStorage: {getItem: key => local.get(key), setItem: (key, value) => local.set(key, value)},
    addEventListener() {}, scrollTo() {}};
  vm.runInNewContext(fs.readFileSync(path.join(source, 'review_ui.js'), 'utf8'),
    {document, window, Blob, URL: {createObjectURL: value => {download = value; return 'unit-url';}, revokeObjectURL() {}},
      setTimeout: callback => callback()});
  assert.equal(get('image').src, 'images/unit.png');
  assert.match(get('progress').textContent, /0\/1/);
  for (const [field, value] of Object.entries({reviewer_id: 'unit-reviewer', role: 'unknown', output_exposure: 'none'})) {
    get('profile-' + field).value = value;
    get('profile-' + field).oninput();
  }
  for (const [key, value] of Object.entries({availability: 'not_seen', readability: 'unreadable',
    semantic_key_confirmed: 'uncertain', prior_exposure: 'no', notes: 'in-memory unit observation'})) {
    callbacks.get('input')({target: {dataset: {key}, closest: () => null, value}});
  }
  get('save').onclick();
  const backup = JSON.parse(local.get('document-review/unit-only'));
  assert.equal(backup.answers['F-test'].notes, 'in-memory unit observation');
  get('export-review').onclick();
  const value = JSON.parse(await download.text());
  assert.equal(value.mode, 'unit_injected');
  assert.equal(value.items[0].image_sha256, 'a'.repeat(64));
  assert.equal(value.reviewer.reviewer_id, 'unit-reviewer');
  await get('restore-backup').onchange({target: {files: [{text: async () => JSON.stringify(value)}]}});
  assert.match(get('progress').textContent, /1\/1/);
  assert.match(get('message').textContent, /Đã lưu/);
});
