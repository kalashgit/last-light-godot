/* Offline tests of the browser geometry parser. No WebGL/browser is mocked as real. */
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

require(path.resolve(__dirname, '../../tools/recipe_architect/dashboard/glb_viewer.js'));
const {parseGLB} = global.LLGlbViewer;

function fixture({translate = [2, 3, 4], mode = 4, index = 0, instances = 1} = {}) {
  const vertices = Buffer.alloc(36);
  [0, 0, 0, 1, 0, 0, 0, 1, 0].forEach((value, i) => vertices.writeFloatLE(value, i * 4));
  const indices = Buffer.alloc(6);
  [0, 1, index === 0 ? 2 : index].forEach((value, i) => indices.writeUInt16LE(value, i * 2));
  const binary = Buffer.concat([vertices, indices, Buffer.alloc(2)]);
  const json = {
    asset: {version: '2.0'},
    nodes: Array.from({length: instances}, () => ({mesh: 0, translation: translate})),
    scenes: [{nodes: Array.from({length: instances}, (_, i) => i)}], scene: 0,
    meshes: [{primitives: [{attributes: {POSITION: 0}, indices: 1, material: 0, mode}]}],
    materials: [{pbrMetallicRoughness: {baseColorFactor: [0.7, 0.2, 0.4, 1]}}],
    accessors: [{bufferView: 0, componentType: 5126, count: 3, type: 'VEC3'},
      {bufferView: 1, componentType: 5123, count: 3, type: 'SCALAR'}],
    bufferViews: [{buffer: 0, byteOffset: 0, byteLength: 36},
      {buffer: 0, byteOffset: 36, byteLength: 6}],
    buffers: [{byteLength: binary.length}]
  };
  const raw = Buffer.from(JSON.stringify(json));
  const padded = Buffer.concat([raw, Buffer.alloc((4 - raw.length % 4) % 4, 32)]);
  const header = Buffer.alloc(20);
  header.write('glTF'); header.writeUInt32LE(2, 4);
  header.writeUInt32LE(20 + padded.length + 8 + binary.length, 8);
  header.writeUInt32LE(padded.length, 12); header.write('JSON', 16);
  const binHead = Buffer.alloc(8);
  binHead.writeUInt32LE(binary.length, 0); binHead.write('BIN\0', 4);
  const file = Buffer.concat([header, padded, binHead, binary]);
  return file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength);
}

test('parses real indexed geometry and preserves translated node positions', () => {
  const model = parseGLB(fixture());
  assert.equal(model.triangles, 1);
  assert.equal(model.meshObjects, 1);
  assert.deepEqual(model.center, [2.5, 3.5, 4]);
  assert.deepEqual(Array.from(model.colors.slice(0, 3)).map(v => v.toFixed(1)), ['0.7','0.2','0.4']);
});

test('multiple scene nodes are independent geometry instances', () => {
  const model = parseGLB(fixture({instances: 2}));
  assert.equal(model.meshObjects, 2);
  assert.equal(model.triangles, 2);
});

test('rejects non-triangle primitives, invalid indices and malformed GLB', () => {
  assert.throws(() => parseGLB(fixture({mode: 5})), /triangle primitives/);
  assert.throws(() => parseGLB(fixture({index: 9})), /outside vertex buffer/);
  const broken = fixture();
  new DataView(broken).setUint32(8, 4, true);
  assert.throws(() => parseGLB(broken), /Invalid GLB header/);
});
