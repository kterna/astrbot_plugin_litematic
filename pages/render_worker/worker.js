const { mat4, vec3 } = window.glMatrix || {};

const canvas = document.getElementById("renderCanvas");
const atlasImage = document.getElementById("atlasImage");

let gl = null;
let resources = null;
let renderer = null;
let structure = null;
let structureSize = [1, 1, 1];
let materialCounts = {};
let regionCount = 0;

function upperPowerOfTwo(value) {
  return 2 ** Math.ceil(Math.log2(Math.max(value, 1)));
}

function base64ToBytes(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
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
    for (let x = 0; x < region.width; x += 1) {
      for (let y = 0; y < region.height; y += 1) {
        for (let z = 0; z < region.depth; z += 1) {
          const blockId = region.blocks[x][y][z];
          const block = region.palette[blockId];
          const name = block?.Name;
          if (!name || name === "minecraft:air") {
            continue;
          }
          const pos = [x + region.position[0], y + region.position[1], z + region.position[2]];
          for (let axis = 0; axis < 3; axis += 1) {
            min[axis] = Math.min(min[axis], pos[axis]);
            max[axis] = Math.max(max[axis], pos[axis] + 1);
          }
        }
      }
    }
  }
  if (!Number.isFinite(min[0])) {
    return { min: [0, 0, 0], size: [1, 1, 1] };
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
  await waitForImage(atlasImage);

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

  const atlasSize = upperPowerOfTwo(Math.max(atlasImage.width, atlasImage.height));
  const atlasCanvas = document.createElement("canvas");
  atlasCanvas.width = atlasSize;
  atlasCanvas.height = atlasSize;
  const atlasCtx = atlasCanvas.getContext("2d");
  atlasCtx.drawImage(atlasImage, 0, 0);
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

function resizeCanvas(width, height) {
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  canvas.width = width;
  canvas.height = height;
  gl.viewport(0, 0, width, height);
  if (renderer) {
    renderer.setViewport(0, 0, width, height);
  }
}

function viewPresetAngles(viewType) {
  switch (String(viewType || "iso").toLowerCase()) {
    case "top":
      return { pitch: Math.PI / 2, yaw: 0, zoom: 0.94 };
    case "front":
    case "north":
      return { pitch: 0, yaw: 0, zoom: 0.94 };
    case "south":
      return { pitch: 0, yaw: Math.PI, zoom: 0.94 };
    case "side":
    case "east":
      return { pitch: 0, yaw: -Math.PI / 2, zoom: 0.94 };
    case "west":
      return { pitch: 0, yaw: Math.PI / 2, zoom: 0.94 };
    default:
      return { pitch: 0.72, yaw: 0.72, zoom: 0.96 };
  }
}

function fitCamera(width, height, pitch, yaw, zoom = 0.96) {
  const aspect = width / Math.max(1, height);
  const verticalHalfFov = (70 * Math.PI) / 360;
  const horizontalHalfFov = Math.atan(Math.tan(verticalHalfFov) * aspect);
  const fill = Math.max(0.35, Math.min(Number.isFinite(zoom) ? zoom : 0.96, 0.995));
  const half = [structureSize[0] / 2, structureSize[1] / 2, structureSize[2] / 2];
  const rot = mat4.create();
  mat4.rotateX(rot, rot, pitch);
  mat4.rotateY(rot, rot, yaw);

  const points = [];
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      for (const sz of [-1, 1]) {
        const point = vec3.fromValues(half[0] * sx, half[1] * sy, half[2] * sz);
        vec3.transformMat4(point, point, rot);
        points.push([point[0], point[1], point[2]]);
      }
    }
  }

  const distanceForScale = (scale) => {
    let required = 2;
    for (const point of points) {
      const x = Math.abs(point[0] * scale);
      const y = Math.abs(point[1] * scale);
      const z = point[2] * scale;
      required = Math.max(
        required,
        z + x / (Math.tan(horizontalHalfFov) * fill),
        z + y / (Math.tan(verticalHalfFov) * fill),
      );
    }
    return required + 2;
  };

  let scale = 1;
  let distance = distanceForScale(scale);

  if (distance > 470) {
    scale = 470 / distance;
    distance = distanceForScale(scale);
  }
  return { scale, distance };
}

function rotatedBounds(pitch, yaw, scale = 1) {
  const half = [structureSize[0] / 2, structureSize[1] / 2, structureSize[2] / 2];
  const rot = mat4.create();
  mat4.rotateX(rot, rot, pitch);
  mat4.rotateY(rot, rot, yaw);

  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      for (const sz of [-1, 1]) {
        const point = vec3.fromValues(half[0] * sx * scale, half[1] * sy * scale, half[2] * sz * scale);
        vec3.transformMat4(point, point, rot);
        for (let axis = 0; axis < 3; axis += 1) {
          min[axis] = Math.min(min[axis], point[axis]);
          max[axis] = Math.max(max[axis], point[axis]);
        }
      }
    }
  }
  return { min, max };
}

function setPerspectiveProjection(fovDegrees = 70) {
  const projection = mat4.create();
  const fov = (fovDegrees * Math.PI) / 180;
  const aspect = canvas.width / Math.max(1, canvas.height);
  mat4.perspective(projection, fov, aspect, 0.1, 5000);
  renderer.projMatrix = projection;
}

function setOrthographicProjection(pitch, yaw, scale) {
  const bounds = rotatedBounds(pitch, yaw, scale);
  const width = Math.max(1, bounds.max[0] - bounds.min[0]);
  const height = Math.max(1, bounds.max[1] - bounds.min[1]);
  const padX = Math.max(0.01, width * 0.001);
  const padY = Math.max(0.01, height * 0.001);
  const projection = mat4.create();
  mat4.ortho(
    projection,
    bounds.min[0] - padX,
    bounds.max[0] + padX,
    bounds.min[1] - padY,
    bounds.max[1] + padY,
    0.1,
    Math.max(100, bounds.max[2] - bounds.min[2] + 100),
  );
  renderer.projMatrix = projection;
  return bounds;
}

function legacyCameraView(options = {}) {
  const center = [structureSize[0] / 2, structureSize[1] / 2, structureSize[2] / 2];
  const maxSize = Math.max(structureSize[0], structureSize[1], structureSize[2]);
  const distance = maxSize * (Number.isFinite(options.distanceFactor) ? options.distanceFactor : 2);
  const angle = Number.isFinite(options.angle) ? options.angle : 0;
  const elevation = Number.isFinite(options.elevation) ? options.elevation : Math.PI / 6;
  const mode = String(options.animationType || "rotation").toLowerCase();
  const eye = [center[0], center[1], center[2]];

  if (mode === "orbit") {
    eye[0] += distance * Math.cos(angle) * Math.cos(elevation);
    eye[1] += distance * Math.sin(elevation);
    eye[2] += distance * Math.sin(angle) * Math.cos(elevation);
  } else {
    eye[0] += distance * Math.cos(angle);
    eye[1] += distance * Math.sin(elevation);
    eye[2] += distance * Math.sin(angle);
  }

  const view = mat4.create();
  mat4.lookAt(view, eye, center, [0, 1, 0]);
  return view;
}

function drawFrame(options = {}) {
  if (!renderer || !gl) {
    throw new Error("渲染器未初始化");
  }
  if (Number.isFinite(options.width) && Number.isFinite(options.height)) {
    resizeCanvas(Math.max(64, Math.floor(options.width)), Math.max(64, Math.floor(options.height)));
  }
  const preset = viewPresetAngles(options.viewType);
  const pitch = Number.isFinite(options.pitch) ? options.pitch : preset.pitch;
  const yaw = Number.isFinite(options.yaw) ? options.yaw : preset.yaw;
  const zoom = Number.isFinite(options.zoom) ? options.zoom : preset.zoom;
  const fit = fitCamera(canvas.width, canvas.height, pitch, yaw, zoom);
  const fitScale = Number.isFinite(options.scale) ? options.scale : fit.scale;
  const distance = Number.isFinite(options.distance) ? options.distance : fit.distance;

  if (options.background === "transparent") {
    gl.clearColor(0, 0, 0, 0);
  } else {
    gl.clearColor(0.062, 0.071, 0.078, 1);
  }
  gl.clearDepth(1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

  const view = mat4.create();
  if (options.cameraMode === "legacy") {
    setPerspectiveProjection(Number.isFinite(options.fov) ? options.fov : 30);
    mat4.copy(view, legacyCameraView(options));
  } else if (options.projection === "orthographic") {
    const bounds = setOrthographicProjection(pitch, yaw, fitScale);
    const depth = Math.max(100, bounds.max[2] - bounds.min[2] + 100);
    mat4.translate(view, view, [0, 0, -depth / 2]);
    mat4.rotateX(view, view, pitch);
    mat4.rotateY(view, view, yaw);
    mat4.scale(view, view, [fitScale, fitScale, fitScale]);
    mat4.translate(view, view, [-structureSize[0] / 2, -structureSize[1] / 2, -structureSize[2] / 2]);
  } else {
    setPerspectiveProjection(70);
    mat4.translate(view, view, [0, 0, -distance]);
    mat4.rotateX(view, view, pitch);
    mat4.rotateY(view, view, yaw);
    mat4.scale(view, view, [fitScale, fitScale, fitScale]);
    mat4.translate(view, view, [-structureSize[0] / 2, -structureSize[1] / 2, -structureSize[2] / 2]);
  }
  renderer.drawStructure(view);
  if (options.grid !== false) {
    renderer.drawGrid(view);
  }
}

window.renderLitematicBase64 = async function renderLitematicBase64(base64, options = {}) {
  if (!mat4 || !vec3) {
    throw new Error("gl-matrix 未加载");
  }
  gl = gl || canvas.getContext("webgl", { preserveDrawingBuffer: true, alpha: true });
  if (!gl) {
    throw new Error("当前浏览器不支持 WebGL");
  }
  await loadResources();

  const width = Math.max(64, Math.floor(options.width || 1024));
  const height = Math.max(64, Math.floor(options.height || 768));
  resizeCanvas(width, height);

  const litematic = readLitematic(base64ToBytes(base64));
  materialCounts = collectMaterials(litematic);
  regionCount = litematic.regions.length;
  structure = structureFromLitematic(litematic);
  structureSize = structure.getSize();
  renderer = new window.deepslate.StructureRenderer(gl, structure, resources, { chunkSize: 8 });
  drawFrame(options);

  return {
    regions: regionCount,
    materials: Object.keys(materialCounts).length,
    size: structureSize,
  };
};

window.renderFrame = function renderFrame(options = {}) {
  drawFrame(options);
  return true;
};
