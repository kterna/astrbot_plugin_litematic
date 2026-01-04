from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from ..image_render.texture_manager import TextureManager


class TextureSampler:
    """基于资源包纹理采样颜色"""

    def __init__(self, resource_dir: str, native_textures: bool = False) -> None:
        self.texture_manager = TextureManager(resource_dir)
        self.texture_size = self.texture_manager.texture_size
        self.native_textures = native_textures
        self._color_cache: Dict[Tuple[Any, ...], Tuple[int, int, int]] = {}
        self._image_cache: Dict[Tuple[str, Optional[Tuple[int, int, int]]], Image.Image] = {}
        self._native_texture_size: Optional[int] = None

    def resolve_texture_name(self, model_data: Dict[str, Any], texture_ref: str) -> Optional[str]:
        if not texture_ref:
            return None

        if texture_ref.startswith("#"):
            key = texture_ref[1:]
            if "textures" in model_data and key in model_data["textures"]:
                return self.resolve_texture_name(model_data, model_data["textures"][key])
            return None

        if texture_ref.startswith("minecraft:"):
            texture_ref = texture_ref[10:]
        if texture_ref.startswith("block/"):
            texture_ref = texture_ref[6:]
        return texture_ref

    def resolve_block_texture_name(self, block_name: str, face: str = "side") -> Optional[str]:
        if ":" in block_name:
            block_name = block_name.split(":")[-1]

        candidates = [f"{block_name}_{face}"]
        if face == "side":
            candidates.append(f"{block_name}_all")
        elif face == "front":
            candidates.append(f"{block_name}_front")
            candidates.append(f"{block_name}_side")
        elif face == "bottom":
            candidates.append(f"{block_name}_bottom")
            candidates.append(f"{block_name}_down")
        elif face == "top":
            candidates.append(f"{block_name}_top")
            candidates.append(f"{block_name}_up")

        candidates.append(block_name)

        for name in candidates:
            if name in self.texture_manager.available_textures:
                return name

        return None

    def build_face_image(self, model_data: Dict[str, Any], face_data: Dict[str, Any],
                         block_id: str, properties: Dict[str, Any]) -> Optional[Image.Image]:
        texture_ref = face_data.get("texture")
        texture_name = self.resolve_texture_name(model_data, texture_ref)
        if not texture_name:
            return None

        texture = self.texture_manager.get_texture(texture_name)
        uv = face_data.get("uv", [0, 0, 16, 16])
        rotation = int(face_data.get("rotation", 0))
        tintindex = face_data.get("tintindex", None)

        face_image = self._crop_texture(texture, uv)
        if rotation:
            face_image = face_image.rotate(-rotation, expand=True)
        if not self.native_textures and face_image.size != (self.texture_size, self.texture_size):
            face_image = face_image.resize((self.texture_size, self.texture_size), Image.Resampling.NEAREST)

        tint_color = self._get_tint_color(block_id, properties, tintindex)
        if tint_color is not None:
            face_image = self._apply_tint(face_image, tint_color)

        return face_image

    def sample_face_color(self, model_data: Dict[str, Any], face_data: Dict[str, Any],
                          block_id: str, properties: Dict[str, Any]) -> Tuple[int, int, int]:
        texture_ref = face_data.get("texture")
        texture_name = self.resolve_texture_name(model_data, texture_ref)
        uv = face_data.get("uv", [0, 0, 16, 16])
        rotation = int(face_data.get("rotation", 0))
        tintindex = face_data.get("tintindex", None)
        tint_color = self._get_tint_color(block_id, properties, tintindex)

        cache_key = (texture_name, tuple(uv), rotation, tint_color)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        face_image = self.build_face_image(model_data, face_data, block_id, properties)
        if face_image is None:
            color = (200, 200, 200)
        else:
            color = self._average_color(face_image)

        self._color_cache[cache_key] = color
        return color

    def sample_texture_color(self, texture_name: str) -> Tuple[int, int, int]:
        cache_key = ("texture", texture_name)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        texture = self.texture_manager.get_texture(texture_name)
        color = self._average_color(texture)
        self._color_cache[cache_key] = color
        return color

    def sample_block_face_color(self, block_name: str, face: str) -> Tuple[int, int, int]:
        cache_key = ("block_face", block_name, face)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        if self.native_textures:
            texture_name = self.resolve_block_texture_name(block_name, face)
            if texture_name:
                texture = self._load_texture_by_name(texture_name)
            else:
                texture = self.texture_manager.default_texture.copy()
        else:
            texture = self.texture_manager.get_texture(block_name, face)
        color = self._average_color(texture)
        self._color_cache[cache_key] = color
        return color

    def get_texture_image(self, texture_name: str,
                          tint_color: Optional[Tuple[int, int, int]] = None) -> Image.Image:
        cache_key = (texture_name, tint_color)
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        image = self._load_texture_by_name(texture_name)
        if tint_color is not None:
            image = self._apply_tint(image, tint_color)

        if not self.native_textures and image.size != (self.texture_size, self.texture_size):
            image = image.resize((self.texture_size, self.texture_size), Image.Resampling.NEAREST)

        self._image_cache[cache_key] = image
        return image

    def get_tint_color(self, block_id: str, properties: Dict[str, Any],
                       tintindex: Optional[int]) -> Optional[Tuple[int, int, int]]:
        return self._get_tint_color(block_id, properties, tintindex)

    def get_native_texture_size(self) -> int:
        if self._native_texture_size is not None:
            return self._native_texture_size

        if not self.native_textures:
            self._native_texture_size = self.texture_size
            return self._native_texture_size

        size = self.texture_size
        for texture_path in self.texture_manager.available_textures.values():
            try:
                with Image.open(texture_path) as img:
                    size = max(img.size)
                break
            except Exception:
                continue

        self._native_texture_size = size
        return size

    def _crop_texture(self, texture: Image.Image, uv: List[float]) -> Image.Image:
        texture_size = texture.width
        u1 = (uv[0] / 16.0) * texture_size
        v1 = (uv[1] / 16.0) * texture_size
        u2 = (uv[2] / 16.0) * texture_size
        v2 = (uv[3] / 16.0) * texture_size

        u1, u2 = min(u1, u2), max(u1, u2)
        v1, v2 = min(v1, v2), max(v1, v2)

        u1 = max(0, min(texture_size - 1, u1))
        v1 = max(0, min(texture_size - 1, v1))
        u2 = max(0, min(texture_size, u2))
        v2 = max(0, min(texture_size, v2))

        if u2 <= u1 or v2 <= v1:
            return texture

        return texture.crop((int(u1), int(v1), int(u2), int(v2)))

    def _load_texture_by_name(self, texture_name: str) -> Image.Image:
        if texture_name in self.texture_manager.available_textures:
            texture_path = self.texture_manager.available_textures[texture_name]
            try:
                return Image.open(texture_path).convert("RGBA")
            except Exception:
                return self.texture_manager.default_texture.copy()

        return self.texture_manager.default_texture.copy()

    def _average_color(self, image: Image.Image) -> Tuple[int, int, int]:
        rgba = np.array(image.convert("RGBA"), dtype=np.float32)
        alpha = rgba[:, :, 3] / 255.0
        weight = alpha.sum()
        if weight <= 0:
            return (200, 200, 200)

        rgb = rgba[:, :, :3]
        weighted = (rgb * alpha[:, :, None]).sum(axis=(0, 1)) / weight
        return tuple(int(max(0, min(255, c))) for c in weighted)

    def _apply_tint(self, image: Image.Image, tint_color: Tuple[int, int, int]) -> Image.Image:
        rgba = np.array(image.convert("RGBA"), dtype=np.float32)
        rgba[:, :, :3] = (rgba[:, :, :3] * (np.array(tint_color, dtype=np.float32) / 255.0)).clip(0, 255)
        return Image.fromarray(rgba.astype(np.uint8), mode="RGBA")

    def _get_tint_color(self, block_id: str, properties: Dict[str, Any],
                        tintindex: Optional[int]) -> Optional[Tuple[int, int, int]]:
        if tintindex is None:
            return None

        name = block_id.split(":")[-1]
        if name != "redstone_wire":
            return None

        power_value = properties.get("power", 0)
        try:
            power = int(power_value)
        except (TypeError, ValueError):
            power = 0

        power = max(0, min(15, power))
        f = power / 15.0
        r = f * 0.6 + 0.4
        g = max(0.0, f * f * 0.7 - 0.5)
        b = max(0.0, f * f * 0.6 - 0.7)
        return (int(r * 255), int(g * 255), int(b * 255))
