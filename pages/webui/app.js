const bridge = window.AstrBotPluginPage;
const canUseBridge = Boolean(bridge?.apiGet && window.parent !== window);
const { mat4, vec3 } = window.glMatrix || {};

const els = {
  subtitle: document.getElementById("subtitle"),
  refreshButton: document.getElementById("refreshButton"),
  categorySelect: document.getElementById("categorySelect"),
  searchInput: document.getElementById("searchInput"),
  fileCount: document.getElementById("fileCount"),
  fileList: document.getElementById("fileList"),
  activeTitle: document.getElementById("activeTitle"),
  activeMeta: document.getElementById("activeMeta"),
  viewer: document.getElementById("viewer"),
  canvas: document.getElementById("renderCanvas"),
  emptyState: document.getElementById("emptyState"),
  resetViewButton: document.getElementById("resetViewButton"),
  materialsButton: document.getElementById("materialsButton"),
  materialsDrawer: document.getElementById("materialsDrawer"),
  closeMaterialsButton: document.getElementById("closeMaterialsButton"),
  materialsList: document.getElementById("materialsList"),
  statusText: document.getElementById("statusText"),
  atlasImage: document.getElementById("atlasImage"),
};

let categories = [];
let files = [];
let selectedFile = null;
let resources = null;
let renderer = null;
let structure = null;
let gl = null;
let cameraPitch = 0.8;
let cameraYaw = 0.5;
let cameraPos = vec3?.create();
let materialCounts = {};
let isDragging = false;
let dragLast = null;

function unwrap(response) {
  if (response && typeof response === "object" && "ok" in response) {
    if (!response.ok) {
      throw new Error(response.error || "请求失败");
    }
    return response.data;
  }
  return response;
}

async function apiGet(endpoint, params = {}) {
  if (canUseBridge) {
    return unwrap(await bridge.apiGet(endpoint, params));
  }
  const query = new URLSearchParams(params);
  const suffix = query.toString() ? `?${query}` : "";
  const response = await fetch(`/api/plug/litematic/${endpoint}${suffix}`);
  return unwrap(await response.json());
}

function setStatus(text) {
  els.statusText.textContent = text;
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) {
    return "-";
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function upperPowerOfTwo(value) {
  return 2 ** Math.ceil(Math.log2(Math.max(value, 1)));
}

function stripNbtTyping(nbtData) {
  if (nbtData && typeof nbtData === "object" && Object.hasOwn(nbtData, "type")) {
    if (nbtData.type === "compound") {
      const dict = {};
      for (const [key, value] of Object.entries(nbtData.value || {})) {
        dict[key] = stripNbtTyping(value);
      }
      return dict;
    }
    if (nbtData.type === "list") {
      return Object.values(nbtData.value?.value || {}).map((value) => stripNbtTyping(value));
    }
    return nbtData.value;
  }

  if (nbtData && nbtData.constructor === Object) {
    const dict = {};
    for (const [key, value] of Object.entries(nbtData)) {
      dict[key] = stripNbtTyping(value);
    }
    return dict;
  }
  return nbtData;
}

function readPackedBlock(regionData, index, bits) {
  const mask = (1 << bits) - 1;
  const startOffset = index * bits;
  const startArrayIndex = startOffset >>> 5;
  const endArrayIndex = ((index + 1) * bits - 1) >>> 5;
  const startBitOffset = startOffset & 0x1f;
  const halfIndex = startArrayIndex >>> 1;

  let blockStart = 0;
  let blockEnd = 0;
  if ((startArrayIndex & 1) === 0) {
    blockStart = regionData[halfIndex]?.[1] ?? 0;
    blockEnd = regionData[halfIndex]?.[0] ?? 0;
  } else {
    blockStart = regionData[halfIndex]?.[0] ?? 0;
    blockEnd = regionData[halfIndex + 1]?.[1] ?? 0;
  }

  if (startArrayIndex === endArrayIndex) {
    return (blockStart >>> startBitOffset) & mask;
  }
  const endOffset = 32 - startBitOffset;
  return ((blockStart >>> startBitOffset) & mask) | ((blockEnd << endOffset) & mask);
}

function processRegionData(regionData, bits, width, height, depth) {
  const xSize = Math.abs(width);
  const ySize = Math.abs(height);
  const zSize = Math.abs(depth);
  const yShift = xSize * zSize;
  const zShift = xSize;
  const blocks = Array.from({ length: xSize }, () =>
    Array.from({ length: ySize }, () => Array.from({ length: zSize }, () => 0)),
  );

  for (let x = 0; x < xSize; x += 1) {
    for (let y = 0; y < ySize; y += 1) {
      for (let z = 0; z < zSize; z += 1) {
        blocks[x][y][z] = readPackedBlock(regionData, y * yShift + z * zShift + x, bits);
      }
    }
  }
  return blocks;
}

function readVector(value, fallback = [0, 0, 0]) {
  if (!value) {
    return fallback;
  }
  return [Number(value.x ?? fallback[0]), Number(value.y ?? fallback[1]), Number(value.z ?? fallback[2])];
}

function readLitematic(bytes) {
  const nbtData = window.deepslate.readNbt(bytes);
  const root = nbtData.value;
  const regions = root.Regions?.value;
  if (!regions) {
    throw new Error("文件中没有找到 Regions 数据");
  }

  const litematicRegions = [];
  for (const [name, regionNbt] of Object.entries(regions)) {
    const region = regionNbt.value;
    const palette = stripNbtTyping(region.BlockStatePalette);
    const bits = Math.max(1, Math.ceil(Math.log2(Math.max(palette.length, 1))));
    const size = readVector(stripNbtTyping(region.Size), [0, 0, 0]);
    const position = readVector(stripNbtTyping(region.Position), [0, 0, 0]);
    const blocks = processRegionData(region.BlockStates.value, bits, size[0], size[1], size[2]);

    litematicRegions.push({
      name,
      width: Math.abs(size[0]),
      height: Math.abs(size[1]),
      depth: Math.abs(size[2]),
      position,
      blocks,
      palette,
    });
  }
  return { regions: litematicRegions };
}

function getBounds(litematic) {
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (const region of litematic.regions) {
    for (let axis = 0; axis < 3; axis += 1) {
      min[axis] = Math.min(min[axis], region.position[axis]);
    }
    max[0] = Math.max(max[0], region.position[0] + region.width);
    max[1] = Math.max(max[1], region.position[1] + region.height);
    max[2] = Math.max(max[2], region.position[2] + region.depth);
  }
  return { min, size: max.map((value, index) => Math.max(1, value - min[index])) };
}

function collectMaterials(litematic) {
  const counts = {};
  for (const region of litematic.regions) {
    for (let x = 0; x < region.width; x += 1) {
      for (let y = 0; y < region.height; y += 1) {
        for (let z = 0; z < region.depth; z += 1) {
          const blockId = region.blocks[x][y][z];
          const block = region.palette[blockId];
          const name = block?.Name;
          if (name && name !== "minecraft:air") {
            counts[name] = (counts[name] || 0) + 1;
          }
        }
      }
    }
  }
  return counts;
}

function structureFromLitematic(litematic) {
  const bounds = getBounds(litematic);
  const nextStructure = new window.deepslate.Structure(bounds.size);

  for (const region of litematic.regions) {
    const offset = region.position.map((value, index) => value - bounds.min[index]);
    for (let x = 0; x < region.width; x += 1) {
      for (let y = 0; y < region.height; y += 1) {
        for (let z = 0; z < region.depth; z += 1) {
          const blockId = region.blocks[x][y][z];
          const block = region.palette[blockId];
          const name = block?.Name;
          if (!name || name === "minecraft:air") {
            continue;
          }
          const pos = [x + offset[0], y + offset[1], z + offset[2]];
          if (block.Properties) {
            nextStructure.addBlock(pos, name, block.Properties);
          } else {
            nextStructure.addBlock(pos, name);
          }
        }
      }
    }
  }
  return nextStructure;
}

async function waitForImage(image) {
  if (image.complete && image.naturalWidth > 0) {
    return;
  }
  await new Promise((resolve, reject) => {
    image.addEventListener("load", resolve, { once: true });
    image.addEventListener("error", () => reject(new Error("材质图集加载失败")), { once: true });
  });
}

async function loadResources() {
  if (resources) {
    return resources;
  }
  if (!window.deepslate || !window.LITEMATIC_ASSETS || !window.LITEMATIC_OPAQUE_BLOCKS) {
    throw new Error("Deepslate 或材质资源未加载");
  }

  await waitForImage(els.atlasImage);

  const blockDefinitions = {};
  Object.keys(window.LITEMATIC_ASSETS.blockstates).forEach((id) => {
    blockDefinitions[`minecraft:${id}`] = window.deepslate.BlockDefinition.fromJson(
      id,
      window.LITEMATIC_ASSETS.blockstates[id],
    );
  });

  const blockModels = {};
  Object.keys(window.LITEMATIC_ASSETS.models).forEach((id) => {
    blockModels[`minecraft:${id}`] = window.deepslate.BlockModel.fromJson(id, window.LITEMATIC_ASSETS.models[id]);
  });
  Object.values(blockModels).forEach((model) => model.flatten({ getBlockModel: (id) => blockModels[id] }));

  const atlasSize = upperPowerOfTwo(Math.max(els.atlasImage.width, els.atlasImage.height));
  const atlasCanvas = document.createElement("canvas");
  atlasCanvas.width = atlasSize;
  atlasCanvas.height = atlasSize;
  const atlasCtx = atlasCanvas.getContext("2d");
  atlasCtx.drawImage(els.atlasImage, 0, 0);
  const atlasData = atlasCtx.getImageData(0, 0, atlasSize, atlasSize);

  const idMap = {};
  Object.keys(window.LITEMATIC_ASSETS.textures).forEach((id) => {
    const [u, v, du, dv] = window.LITEMATIC_ASSETS.textures[id];
    const dv2 = du !== dv && id.startsWith("block/") ? du : dv;
    idMap[`minecraft:${id}`] = [u / atlasSize, v / atlasSize, (u + du) / atlasSize, (v + dv2) / atlasSize];
  });
  const textureAtlas = new window.deepslate.TextureAtlas(atlasData, idMap);

  resources = {
    getBlockDefinition(id) {
      return blockDefinitions[id];
    },
    getBlockModel(id) {
      return blockModels[id];
    },
    getTextureUV(id) {
      return textureAtlas.getTextureUV(id);
    },
    getTextureAtlas() {
      return textureAtlas.getTextureAtlas();
    },
    getBlockFlags(id) {
      const key = id.toString();
      return {
        opaque: window.LITEMATIC_OPAQUE_BLOCKS.has(key),
        self_culling: !window.LITEMATIC_NON_SELF_CULLING.has(key),
        semi_transparent: window.LITEMATIC_TRANSPARENT_BLOCKS.has(key),
      };
    },
    getBlockProperties() {
      return null;
    },
    getDefaultBlockProperties() {
      return null;
    },
  };

  return resources;
}

function initCanvas() {
  if (gl) {
    return;
  }
  gl = els.canvas.getContext("webgl");
  if (!gl) {
    throw new Error("当前浏览器不支持 WebGL");
  }

  els.canvas.addEventListener("mousedown", (event) => {
    if (event.button !== 0) {
      return;
    }
    isDragging = true;
    dragLast = [event.clientX, event.clientY];
  });
  window.addEventListener("mousemove", (event) => {
    if (!isDragging || !dragLast) {
      return;
    }
    cameraYaw += (event.clientX - dragLast[0]) / 220;
    cameraPitch += (event.clientY - dragLast[1]) / 220;
    dragLast = [event.clientX, event.clientY];
    draw();
  });
  window.addEventListener("mouseup", () => {
    isDragging = false;
    dragLast = null;
  });
  els.canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    moveCamera([0, 0, -event.deltaY / 160]);
    draw();
  });

  const moves = {
    KeyW: [0, 0, 0.45],
    KeyS: [0, 0, -0.45],
    KeyA: [0.45, 0, 0],
    KeyD: [-0.45, 0, 0],
    ArrowUp: [0, 0, 0.45],
    ArrowDown: [0, 0, -0.45],
    ArrowLeft: [0.45, 0, 0],
    ArrowRight: [-0.45, 0, 0],
    Space: [0, -0.45, 0],
    ShiftLeft: [0, 0.45, 0],
  };
  window.addEventListener("keydown", (event) => {
    if (!moves[event.code]) {
      return;
    }
    event.preventDefault();
    moveCamera(moves[event.code]);
    draw();
  });

  window.addEventListener("resize", draw);
}

function moveCamera(direction) {
  const offset = vec3.fromValues(direction[0], direction[1], direction[2]);
  vec3.rotateX(offset, offset, [0, 0, 0], -cameraPitch);
  vec3.rotateY(offset, offset, [0, 0, 0], -cameraYaw);
  vec3.add(cameraPos, cameraPos, offset);
}

function resetView() {
  if (!structure) {
    return;
  }
  const size = structure.getSize();
  cameraPitch = 0.8;
  cameraYaw = 0.5;
  vec3.set(cameraPos, -size[0] / 2, -size[1] / 2, -size[2] / 2);
  draw();
}

function resizeCanvas() {
  const rect = els.viewer.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.floor(rect.width * scale));
  const height = Math.max(1, Math.floor(rect.height * scale));
  if (els.canvas.width !== width || els.canvas.height !== height) {
    els.canvas.width = width;
    els.canvas.height = height;
  }
  gl.viewport(0, 0, width, height);
}

function draw() {
  if (!renderer || !gl) {
    return;
  }
  resizeCanvas();
  cameraYaw %= Math.PI * 2;
  cameraPitch = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, cameraPitch));
  const view = mat4.create();
  mat4.rotateX(view, view, cameraPitch);
  mat4.rotateY(view, view, cameraYaw);
  mat4.translate(view, view, cameraPos);
  renderer.drawStructure(view);
  renderer.drawGrid(view);
}

function renderMaterials() {
  const rows = Object.entries(materialCounts).sort(([, left], [, right]) => right - left);
  if (!rows.length) {
    els.materialsList.innerHTML = '<div class="empty-list">暂无材料数据</div>';
    return;
  }
  els.materialsList.replaceChildren(
    ...rows.map(([name, count]) => {
      const row = document.createElement("div");
      row.className = "material-row";
      row.innerHTML = '<span class="material-name"></span><span class="material-count"></span>';
      row.querySelector(".material-name").textContent = name.replace("minecraft:", "");
      row.querySelector(".material-count").textContent = String(count);
      return row;
    }),
  );
}

function renderCategories() {
  els.categorySelect.replaceChildren(
    ...categories.map((category) => {
      const option = document.createElement("option");
      option.value = category.name;
      option.textContent = `${category.name} (${category.count})`;
      return option;
    }),
  );
}

function renderFiles() {
  const query = els.searchInput.value.trim().toLowerCase();
  const visibleFiles = query ? files.filter((file) => file.name.toLowerCase().includes(query)) : files;
  els.fileCount.textContent = `${visibleFiles.length} 个`;

  if (!visibleFiles.length) {
    els.fileList.innerHTML = '<div class="empty-list">没有匹配文件</div>';
    return;
  }

  els.fileList.replaceChildren(
    ...visibleFiles.map((file) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `file-item ${selectedFile?.name === file.name ? "active" : ""}`;
      button.innerHTML = '<span class="file-name"></span><span class="file-meta"></span>';
      button.querySelector(".file-name").textContent = file.name;
      button.querySelector(".file-meta").textContent = `${formatBytes(file.size)} · ${file.modified_at}`;
      button.addEventListener("click", () => loadFile(file));
      return button;
    }),
  );
}

async function loadCategories() {
  categories = await apiGet("categories");
  renderCategories();
  if (categories.length) {
    els.categorySelect.value = categories[0].name;
    await loadFiles();
  } else {
    files = [];
    renderFiles();
  }
}

async function loadFiles() {
  const category = els.categorySelect.value;
  if (!category) {
    return;
  }
  selectedFile = null;
  const data = await apiGet("files", { category });
  files = data.files || [];
  renderFiles();
}

async function loadFile(file) {
  selectedFile = file;
  renderFiles();
  setStatus("正在读取文件...");
  els.activeTitle.textContent = file.name;
  els.activeMeta.textContent = `${els.categorySelect.value} · ${formatBytes(file.size)} · ${file.modified_at}`;

  const data = await apiGet("file", {
    category: els.categorySelect.value,
    filename: file.name,
  });

  setStatus("正在解析 litematic...");
  const litematic = readLitematic(base64ToBytes(data.content_base64));
  materialCounts = collectMaterials(litematic);
  renderMaterials();

  setStatus("正在构建 Deepslate 结构...");
  structure = structureFromLitematic(litematic);
  renderer = new window.deepslate.StructureRenderer(gl, structure, resources, { chunkSize: 8 });
  els.emptyState.hidden = true;
  resetView();
  setStatus(`渲染完成：${litematic.regions.length} 个区域，${Object.keys(materialCounts).length} 种材料`);
}

async function refresh() {
  try {
    setStatus("正在刷新文件列表...");
    await loadCategories();
    setStatus("文件列表已刷新");
  } catch (error) {
    setStatus(error?.message || String(error));
  }
}

async function boot() {
  try {
    if (canUseBridge && bridge?.ready) {
      const context = await bridge.ready();
      if (context?.displayName) {
        els.subtitle.textContent = context.displayName;
      }
    }
    if (!mat4 || !vec3) {
      throw new Error("gl-matrix 未加载");
    }
    initCanvas();
    await loadResources();
    await refresh();
  } catch (error) {
    setStatus(error?.message || String(error));
  }
}

els.refreshButton.addEventListener("click", refresh);
els.categorySelect.addEventListener("change", loadFiles);
els.searchInput.addEventListener("input", renderFiles);
els.resetViewButton.addEventListener("click", resetView);
els.materialsButton.addEventListener("click", () => {
  els.materialsDrawer.hidden = false;
});
els.closeMaterialsButton.addEventListener("click", () => {
  els.materialsDrawer.hidden = true;
});

await boot();
