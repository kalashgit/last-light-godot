"use strict";
/* Tiny, dependency-free GLB geometry inspector for the read-only review dashboard.
 * Supports actual glTF 2.0 triangle meshes, node transforms and PBR base colors.
 * No script execution, remote libraries, textures, file upload or mesh editing.
 */
(function (root) {
  const MAX_BYTES = 12_000_000;
  const MAX_TRIANGLES = 120_000;

  function parseGLB(buffer) {
    if (!(buffer instanceof ArrayBuffer) || buffer.byteLength < 28 || buffer.byteLength > MAX_BYTES)
      throw new Error("GLB size outside review limit");
    const data = new DataView(buffer);
    if (data.getUint32(0, true) !== 0x46546c67 || data.getUint32(4, true) !== 2 ||
        data.getUint32(8, true) !== buffer.byteLength)
      throw new Error("Invalid GLB header");
    const jsonLength = data.getUint32(12, true);
    if (data.getUint32(16, true) !== 0x4e4f534a || 20 + jsonLength + 8 > buffer.byteLength)
      throw new Error("Missing GLB JSON or binary chunk");
    const gltf = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 20, jsonLength)));
    const binOffset = 20 + jsonLength;
    const binLength = data.getUint32(binOffset, true);
    if (data.getUint32(binOffset + 4, true) !== 0x004e4942 || binOffset + 8 + binLength > buffer.byteLength)
      throw new Error("Missing GLB binary geometry");
    const binStart = binOffset + 8;
    if (!Array.isArray(gltf.meshes) || !Array.isArray(gltf.accessors) || !Array.isArray(gltf.bufferViews) || !Array.isArray(gltf.nodes))
      throw new Error("Missing glTF geometry tables");

    function accessor(index, expectedType) {
      const info = gltf.accessors[index];
      if (!info || info.type !== expectedType || !Number.isSafeInteger(info.count) || info.count < 1 || info.count > 500_000 ||
          info.bufferView === undefined || info.sparse)
        throw new Error("Unsupported or sparse accessor");
      const view = gltf.bufferViews[info.bufferView];
      if (!view || (view.buffer ?? 0) !== 0) throw new Error("Unsupported buffer view");
      const components = {SCALAR: 1, VEC3: 3}[expectedType];
      const bytes = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[info.componentType];
      if (!bytes || (expectedType === "VEC3" && info.componentType !== 5126))
        throw new Error("Unsupported accessor component type");
      const stride = view.byteStride || components * bytes;
      const offset = (view.byteOffset || 0) + (info.byteOffset || 0);
      const end = offset + (info.count - 1) * stride + components * bytes;
      if (stride < components * bytes || end > (view.byteOffset || 0) + view.byteLength || end > binLength)
        throw new Error("Accessor exceeds binary bounds");
      const output = new Array(info.count * components);
      for (let row = 0; row < info.count; row++) {
        for (let c = 0; c < components; c++) {
          const at = binStart + offset + row * stride + c * bytes;
          output[row * components + c] = info.componentType === 5126 ? data.getFloat32(at, true)
            : info.componentType === 5125 ? data.getUint32(at, true)
            : info.componentType === 5123 ? data.getUint16(at, true) : data.getUint8(at);
        }
      }
      return output;
    }
    const identity = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
    function multiply(a, b) {
      const out = new Array(16).fill(0);
      for (let col = 0; col < 4; col++) for (let row = 0; row < 4; row++)
        for (let k = 0; k < 4; k++) out[col * 4 + row] += a[k * 4 + row] * b[col * 4 + k];
      return out;
    }
    function localMatrix(node) {
      if (node.matrix) {
        if (node.matrix.length !== 16) throw new Error("Invalid node matrix");
        return node.matrix;
      }
      const [x, y, z, w] = node.rotation || [0, 0, 0, 1];
      const [sx, sy, sz] = node.scale || [1, 1, 1];
      const [tx, ty, tz] = node.translation || [0, 0, 0];
      const x2 = x + x, y2 = y + y, z2 = z + z;
      const xx = x * x2, yy = y * y2, zz = z * z2;
      const xy = x * y2, xz = x * z2, yz = y * z2;
      const wx = w * x2, wy = w * y2, wz = w * z2;
      return [(1 - yy - zz) * sx, (xy + wz) * sx, (xz - wy) * sx, 0,
        (xy - wz) * sy, (1 - xx - zz) * sy, (yz + wx) * sy, 0,
        (xz + wy) * sz, (yz - wx) * sz, (1 - xx - yy) * sz, 0,
        tx, ty, tz, 1];
    }
    function point(matrix, vertex) {
      const [x, y, z] = vertex;
      return [matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
        matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
        matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14]];
    }
    const positions = [], normals = [], colors = [];
    let triangles = 0, meshObjects = 0;
    const mins = [Infinity, Infinity, Infinity], maxs = [-Infinity, -Infinity, -Infinity];
    function addMesh(meshIndex, matrix) {
      const mesh = gltf.meshes[meshIndex];
      if (!mesh?.primitives?.length) throw new Error("Node references missing geometry");
      meshObjects++;
      for (const prim of mesh.primitives) {
        if (prim.mode !== undefined && prim.mode !== 4) throw new Error("Only triangle primitives supported");
        if (prim.attributes?.POSITION === undefined) throw new Error("Mesh has no positions");
        const source = accessor(prim.attributes.POSITION, "VEC3");
        const indices = prim.indices === undefined ? Array.from({length: source.length / 3}, (_, i) => i) : accessor(prim.indices, "SCALAR");
        if (indices.length % 3 !== 0) throw new Error("Non-triangular index buffer");
        triangles += indices.length / 3;
        if (triangles > MAX_TRIANGLES) throw new Error("GLB exceeds phone triangle budget");
        const material = gltf.materials?.[prim.material];
        const base = material?.pbrMetallicRoughness?.baseColorFactor || [0.68, 0.72, 0.78, 1];
        for (let i = 0; i < indices.length; i += 3) {
          const verts = [indices[i], indices[i + 1], indices[i + 2]].map(idx => {
            if (!Number.isInteger(idx) || idx < 0 || idx * 3 + 2 >= source.length)
              throw new Error("Index outside vertex buffer");
            return point(matrix, source.slice(idx * 3, idx * 3 + 3));
          });
          const a = verts[0], b = verts[1], c = verts[2];
          const ab = b.map((v, idx) => v - a[idx]), ac = c.map((v, idx) => v - a[idx]);
          const n = [ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0]];
          const length = Math.hypot(...n) || 1;
          for (const v of verts) {
            if (!v.every(Number.isFinite)) throw new Error("Non-finite mesh coordinates");
            for (let j = 0; j < 3; j++) { mins[j] = Math.min(mins[j], v[j]); maxs[j] = Math.max(maxs[j], v[j]); }
            positions.push(...v);
            normals.push(...n.map(x => x / length));
            colors.push(...base.slice(0, 3));
          }
        }
      }
    }
    const children = new Set(gltf.nodes.flatMap(n => n.children || []));
    const scene = gltf.scenes?.[gltf.scene || 0];
    const roots = scene?.nodes || gltf.nodes.map((_, i) => i).filter(i => !children.has(i));
    const active = new Set();
    function visit(index, parent, depth) {
      if (depth > 64 || active.has(index) || !gltf.nodes[index]) throw new Error("Invalid scene hierarchy");
      active.add(index);
      const node = gltf.nodes[index];
      const world = multiply(parent, localMatrix(node));
      if (node.mesh !== undefined) addMesh(node.mesh, world);
      for (const child of node.children || []) visit(child, world, depth + 1);
      active.delete(index);
    }
    for (const index of roots) visit(index, identity(), 0);
    if (!triangles || !meshObjects) throw new Error("GLB contains no actual triangles");
    return {positions: new Float32Array(positions), normals: new Float32Array(normals),
      colors: new Float32Array(colors), triangles, meshObjects,
      center: mins.map((v, i) => (v + maxs[i]) / 2),
      diameter: Math.max(...mins.map((v, i) => maxs[i] - v), 0.001)};
  }

  class Viewer {
    constructor(canvas) {
      this.canvas = canvas;
      this.gl = canvas.getContext("webgl2", {alpha: true, antialias: true}) ||
        canvas.getContext("webgl", {alpha: true, antialias: true});
      if (!this.gl) throw new Error("WebGL unavailable on this device");
      this.yaw = Math.PI / 4; this.pitch = Math.PI / 6; this.zoom = 1;
      this.model = null; this.pending = false;
      this.setup();
      canvas.style.touchAction = "none";
      canvas.addEventListener("pointerdown", event => {
        this.drag = [event.pointerId, event.clientX, event.clientY];
        canvas.setPointerCapture(event.pointerId);
      });
      canvas.addEventListener("pointermove", event => {
        if (!this.drag || this.drag[0] !== event.pointerId) return;
        this.yaw += (event.clientX - this.drag[1]) * 0.012;
        this.pitch = Math.max(-1.25, Math.min(1.35, this.pitch + (event.clientY - this.drag[2]) * 0.012));
        this.drag = [event.pointerId, event.clientX, event.clientY]; this.drawSoon();
      });
      for (const eventName of ["pointerup", "pointercancel", "lostpointercapture"])
        canvas.addEventListener(eventName, () => { this.drag = null; });
      canvas.addEventListener("wheel", event => { event.preventDefault();
        this.zoom = Math.max(0.45, Math.min(3, this.zoom * (event.deltaY > 0 ? 0.92 : 1.08)));
        this.drawSoon(); }, {passive: false});
      if (typeof ResizeObserver !== "undefined") new ResizeObserver(() => this.drawSoon()).observe(canvas);
    }
    setup() {
      const gl = this.gl;
      const vert = `attribute vec3 position; attribute vec3 normal; attribute vec3 color;
        uniform vec3 uCenter,uRight,uUp,uFacing; uniform float uScale;
        varying vec3 vColor,vNormal;
        void main(){vec3 p=position-uCenter;
          gl_Position=vec4(dot(p,uRight)*uScale,dot(p,uUp)*uScale,dot(p,uFacing)*uScale*0.35,1.0);
          vColor=color;vNormal=normal;}`;
      const frag = `precision mediump float; varying vec3 vColor,vNormal;
        void main(){float light=0.46+0.54*max(0.0,dot(normalize(vNormal),normalize(vec3(-0.5,0.78,-0.35))));
          gl_FragColor=vec4(vColor*light,1.0);}`;
      function shader(type, source) {const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);
        if (!gl.getShaderParameter(s,gl.COMPILE_STATUS)) throw new Error("Viewer shader compilation failed");return s;}
      const program = gl.createProgram();
      gl.attachShader(program,shader(gl.VERTEX_SHADER,vert));
      gl.attachShader(program,shader(gl.FRAGMENT_SHADER,frag));
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error("Viewer shader link failed");
      this.program = program; this.uniforms = {};
      for (const name of ["uCenter","uRight","uUp","uFacing","uScale"])
        this.uniforms[name] = gl.getUniformLocation(program,name);
      this.attributes = ["position","normal","color"].map(n=>gl.getAttribLocation(program,n));
      this.buffers = [gl.createBuffer(),gl.createBuffer(),gl.createBuffer()];
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);
    }
    async load(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Could not fetch verified GLB");
      const buffer = await response.arrayBuffer();
      const parsed = parseGLB(buffer);
      const gl=this.gl;
      for(const [i,values] of [parsed.positions,parsed.normals,parsed.colors].entries()) {
        gl.bindBuffer(gl.ARRAY_BUFFER,this.buffers[i]);gl.bufferData(gl.ARRAY_BUFFER,values,gl.STATIC_DRAW);
      }
      this.model=parsed;this.zoom=1;this.drawSoon();
      return parsed;
    }
    drawSoon() {if(this.pending)return;this.pending=true;
      requestAnimationFrame(()=>{this.pending=false;this.draw();});}
    draw() {
      if (!this.model || this.canvas.hidden) return;
      const gl=this.gl, canvas=this.canvas;
      const pixelRatio=Math.min(2,window.devicePixelRatio||1);
      const w=Math.max(1,Math.round(canvas.clientWidth*pixelRatio)),h=Math.max(1,Math.round(canvas.clientHeight*pixelRatio));
      if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
      gl.viewport(0,0,w,h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      // GLB/glTF uses +Y up, including exported Blender assets.
      const dir=[Math.sin(this.yaw)*Math.cos(this.pitch),Math.sin(this.pitch),Math.cos(this.yaw)*Math.cos(this.pitch)];
      const right=[Math.cos(this.yaw),0,-Math.sin(this.yaw)];
      const up=[-Math.sin(this.yaw)*Math.sin(this.pitch),Math.cos(this.pitch),-Math.cos(this.yaw)*Math.sin(this.pitch)];
      const aspect=w/h, scale=(1.2/this.model.diameter)*this.zoom;
      const vec=(name,value)=>gl.uniform3fv(this.uniforms[name],value);
      gl.useProgram(this.program);
      vec("uCenter",this.model.center);vec("uRight",right.map(x=>x/(aspect>1?aspect:1)));
      vec("uUp",up.map(x=>x*(aspect<1?aspect:1)));vec("uFacing",dir);
      gl.uniform1f(this.uniforms.uScale,scale);
      for(let i=0;i<3;i++){gl.bindBuffer(gl.ARRAY_BUFFER,this.buffers[i]);
        gl.enableVertexAttribArray(this.attributes[i]);gl.vertexAttribPointer(this.attributes[i],3,gl.FLOAT,false,0,0);}
      gl.drawArrays(gl.TRIANGLES,0,this.model.positions.length/3);
    }
  }
  root.LLGlbViewer={Viewer,parseGLB,MAX_BYTES,MAX_TRIANGLES};
})(typeof window !== "undefined" ? window : globalThis);
