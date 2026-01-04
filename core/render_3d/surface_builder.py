import math
from typing import Any, Dict, List, Tuple

from .model_resolver import ModelResolver
from .texture_sampler import TextureSampler


class SurfaceBuilder:
    """基于模型和纹理采样生成3D表面数据"""

    FACE_DIRS = {
        "north": (0, 0, -1),
        "south": (0, 0, 1),
        "east": (1, 0, 0),
        "west": (-1, 0, 0),
        "up": (0, 1, 0),
        "down": (0, -1, 0),
    }

    CUBE_FACE_DIRS = {
        "top": (0, 1, 0),
        "bottom": (0, -1, 0),
        "north": (0, 0, -1),
        "south": (0, 0, 1),
        "east": (1, 0, 0),
        "west": (-1, 0, 0),
    }

    FACE_SHADE = {
        "up": 1.2,
        "down": 0.7,
        "north": 0.9,
        "south": 0.9,
        "east": 0.8,
        "west": 0.8,
        "top": 1.2,
        "bottom": 0.7,
    }

    def __init__(self, model_data: Dict[str, Any], resource_dir: str,
                 native_textures: bool = False) -> None:
        self.model_data = model_data
        self.blocks = model_data.get("blocks", {})
        self.texture_sampler = TextureSampler(resource_dir, native_textures=native_textures)
        self.model_resolver = ModelResolver(resource_dir)

        self._cube_face_cache: Dict[Tuple[str, str], Tuple[Any, ...]] = {}

    def build_surfaces(self) -> List[Dict[str, Any]]:
        surfaces: List[Dict[str, Any]] = []
        cube_blocks: Dict[Tuple[int, int, int], str] = {}

        for position, block_data in self.blocks.items():
            block_id = block_data.get("id", "")
            properties = block_data.get("properties", {})

            model_instances = self._get_special_models(block_id, properties)
            if model_instances:
                for instance in model_instances:
                    surfaces.extend(
                        self._build_model_surfaces(
                            position,
                            block_id,
                            properties,
                            instance["model"],
                            instance.get("rotation", (0, 0, 0)),
                        )
                    )
                continue

            cube_blocks[position] = block_id

        if cube_blocks:
            surfaces.extend(self._build_greedy_cube_surfaces(cube_blocks))

        return surfaces

    def _get_special_models(self, block_id: str, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        name = block_id.split(":")[-1]

        if name == "redstone_wire":
            return self._get_redstone_models(properties)

        if name == "hopper":
            return self._get_hopper_models(properties)

        if name in ("piston", "sticky_piston", "piston_head"):
            return self._get_piston_models(block_id, properties)

        if name.endswith("glass_pane"):
            return self._get_glass_pane_models(name, properties)

        return []

    def _get_redstone_models(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        connections = {
            "north": properties.get("north", "none"),
            "south": properties.get("south", "none"),
            "east": properties.get("east", "none"),
            "west": properties.get("west", "none"),
        }

        has_connection = any(value != "none" for value in connections.values())
        models: List[Dict[str, Any]] = []

        if not has_connection:
            model = self.model_resolver.load("redstone_dust_dot")
            if model:
                models.append({"model": model, "rotation": (0, 0, 0)})
            return models

        side_model = self.model_resolver.load("redstone_dust_side0")
        up_model = self.model_resolver.load("redstone_dust_up")

        if not side_model:
            return models

        for direction in ("north", "east", "south", "west"):
            state = connections.get(direction, "none")
            if state == "none":
                continue

            rotation = self._rotation_for_facing(direction)
            models.append({"model": side_model, "rotation": rotation})

            if state == "up" and up_model:
                models.append({"model": up_model, "rotation": rotation})

        return models

    def _get_hopper_models(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        facing = properties.get("facing", "down")
        if facing == "down":
            model = self.model_resolver.load("hopper")
            return [{"model": model, "rotation": (0, 0, 0)}] if model else []

        model = self.model_resolver.load("hopper_side")
        rotation = self._rotation_for_facing(facing)
        return [{"model": model, "rotation": rotation}] if model else []

    def _get_piston_models(self, block_id: str, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        name = block_id.split(":")[-1]
        facing = properties.get("facing", "north")
        rotation = self._rotation_for_facing(facing)

        if name == "piston":
            model = self.model_resolver.load("piston")
            return [{"model": model, "rotation": rotation}] if model else []

        if name == "sticky_piston":
            model = self.model_resolver.load("sticky_piston")
            return [{"model": model, "rotation": rotation}] if model else []

        if name == "piston_head":
            is_sticky = properties.get("type", "normal") == "sticky"
            is_short = self._is_true(properties.get("short", False))

            if is_short:
                model_name = "piston_head_short_sticky" if is_sticky else "piston_head_short"
            else:
                model_name = "piston_head_sticky" if is_sticky else "piston_head"

            model = self.model_resolver.load(model_name)
            return [{"model": model, "rotation": rotation}] if model else []

        return []

    def _get_glass_pane_models(self, base_name: str, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        connections = {
            "north": self._is_true(properties.get("north", False)),
            "south": self._is_true(properties.get("south", False)),
            "east": self._is_true(properties.get("east", False)),
            "west": self._is_true(properties.get("west", False)),
        }

        has_connection = any(connections.values())
        models: List[Dict[str, Any]] = []

        post_model = self.model_resolver.load(f"{base_name}_post")
        if post_model:
            models.append({"model": post_model, "rotation": (0, 0, 0)})

        if not has_connection:
            noside = self.model_resolver.load(f"{base_name}_noside")
            noside_alt = self.model_resolver.load(f"{base_name}_noside_alt")
            if noside:
                models.append({"model": noside, "rotation": (0, 0, 0)})
            if noside_alt:
                models.append({"model": noside_alt, "rotation": (0, 0, 0)})
            return models

        side_model = self.model_resolver.load(f"{base_name}_side")
        if not side_model:
            return models

        for direction, enabled in connections.items():
            if not enabled:
                continue
            rotation = self._rotation_for_facing(direction)
            models.append({"model": side_model, "rotation": rotation})

        return models

    def _build_model_surfaces(self, position: Tuple[int, int, int], block_id: str,
                              properties: Dict[str, Any], model_data: Dict[str, Any],
                              rotation: Tuple[float, float, float]) -> List[Dict[str, Any]]:
        if not model_data or "elements" not in model_data:
            return []

        surfaces: List[Dict[str, Any]] = []

        for element in model_data["elements"]:
            from_coords = element.get("from", [0, 0, 0])
            to_coords = element.get("to", [16, 16, 16])
            faces = element.get("faces", {})

            for face_name, face_data in faces.items():
                cullface = face_data.get("cullface")
                if cullface and self._has_neighbor(position, cullface):
                    continue

                texture_name = self.texture_sampler.resolve_texture_name(
                    model_data, face_data.get("texture", "")
                )
                if block_id.endswith("redstone_wire") and texture_name and "overlay" in texture_name:
                    continue

                local_vertices = self._get_face_vertices(face_name, from_coords, to_coords)
                uv_rect = self._get_uv_rect(face_name, from_coords, to_coords, face_data)
                uvs = self._get_vertex_uvs(face_name, local_vertices, from_coords, to_coords, uv_rect)
                rotation_uv = int(face_data.get("rotation", 0))
                if rotation_uv:
                    uvs = self._apply_uv_rotation(uvs, uv_rect, rotation_uv)
                uvs = self._normalize_uvs(uvs)

                vertices = [(v[0] / 16.0, v[1] / 16.0, v[2] / 16.0) for v in local_vertices]
                vertices = self._apply_rotation(vertices, rotation)
                vertices = [(v[0] + position[0], v[1] + position[1], v[2] + position[2]) for v in vertices]

                tint_color = self.texture_sampler.get_tint_color(
                    block_id, properties, face_data.get("tintindex")
                )

                if texture_name:
                    surfaces.append({
                        "vertices": vertices,
                        "uvs": uvs,
                        "texture": texture_name,
                        "tint": tint_color,
                        "face": face_name,
                        "block_id": block_id,
                    })
                else:
                    color = self.texture_sampler.sample_face_color(model_data, face_data, block_id, properties)
                    color = self._apply_shading(color, face_name)
                    surfaces.append({
                        "vertices": vertices,
                        "color": color,
                        "face": face_name,
                        "block_id": block_id,
                    })

        return surfaces

    def _build_cube_surfaces(self, position: Tuple[int, int, int], block_id: str) -> List[Dict[str, Any]]:
        block_name = block_id.split(":")[-1]
        surfaces: List[Dict[str, Any]] = []

        for face_name, direction in self.CUBE_FACE_DIRS.items():
            dx, dy, dz = direction
            neighbor = (position[0] + dx, position[1] + dy, position[2] + dz)
            if neighbor in self.blocks:
                continue

            vertices = self._get_cube_vertices(position, face_name)
            texture_face = self._map_cube_face(face_name)
            texture_name = self.texture_sampler.resolve_block_texture_name(block_name, texture_face)
            uv_face = "up" if face_name == "top" else "down" if face_name == "bottom" else face_name
            local_vertices = self._get_face_vertices(uv_face, [0, 0, 0], [16, 16, 16])
            uvs = self._normalize_uvs(
                self._get_vertex_uvs(uv_face, local_vertices, [0, 0, 0], [16, 16, 16], [0, 0, 16, 16])
            )

            if texture_name:
                surfaces.append({
                    "vertices": vertices,
                    "uvs": uvs,
                    "texture": texture_name,
                    "tint": None,
                    "face": face_name,
                    "block_id": block_id,
                })
            else:
                color = self.texture_sampler.sample_block_face_color(block_name, texture_face)
                color = self._apply_shading(color, face_name)
                surfaces.append({
                    "vertices": vertices,
                    "color": color,
                    "face": face_name,
                    "block_id": block_id,
                })

        return surfaces

    def _build_greedy_cube_surfaces(self,
                                   cube_blocks: Dict[Tuple[int, int, int], str]) -> List[Dict[str, Any]]:
        surfaces: List[Dict[str, Any]] = []
        if not cube_blocks:
            return surfaces

        self._cube_face_cache.clear()

        for face_name in ("top", "bottom", "north", "south", "east", "west"):
            surfaces.extend(self._merge_face_planes(face_name, cube_blocks))

        return surfaces

    def _merge_face_planes(self, face_name: str,
                           cube_blocks: Dict[Tuple[int, int, int], str]) -> List[Dict[str, Any]]:
        dx, dy, dz = self.CUBE_FACE_DIRS[face_name]
        planes: Dict[int, Dict[Tuple[int, int], Tuple[Tuple[Any, ...], str]]] = {}

        for (x, y, z), block_id in cube_blocks.items():
            neighbor = (x + dx, y + dy, z + dz)
            if neighbor in self.blocks:
                continue

            key = self._get_cube_face_key(block_id, face_name)
            if not key:
                continue

            if face_name in ("top", "bottom"):
                plane = y
                cell = (x, z)
            elif face_name in ("north", "south"):
                plane = z
                cell = (x, y)
            else:
                plane = x
                cell = (z, y)

            planes.setdefault(plane, {})[cell] = (key, block_id)

        surfaces: List[Dict[str, Any]] = []
        for plane, cells in planes.items():
            surfaces.extend(self._greedy_merge_plane(face_name, plane, cells))

        return surfaces

    def _get_cube_face_key(self, block_id: str, face_name: str) -> Tuple[Any, ...]:
        cache_key = (block_id, face_name)
        if cache_key in self._cube_face_cache:
            return self._cube_face_cache[cache_key]

        block_name = block_id.split(":")[-1]
        texture_face = self._map_cube_face(face_name)
        texture_name = self.texture_sampler.resolve_block_texture_name(block_name, texture_face)
        if texture_name:
            key = ("tex", texture_name)
        else:
            color = self.texture_sampler.sample_block_face_color(block_name, texture_face)
            color = self._apply_shading(color, face_name)
            key = ("color", color)

        self._cube_face_cache[cache_key] = key
        return key

    def _greedy_merge_plane(self, face_name: str, plane: int,
                            cells: Dict[Tuple[int, int], Tuple[Tuple[Any, ...], str]]) -> List[Dict[str, Any]]:
        u_values = [coord[0] for coord in cells.keys()]
        v_values = [coord[1] for coord in cells.keys()]
        u_min, u_max = min(u_values), max(u_values)
        v_min, v_max = min(v_values), max(v_values)

        rows = v_max - v_min + 1
        cols = u_max - u_min + 1
        mask: List[List[Any]] = [[None for _ in range(cols)] for _ in range(rows)]

        for (u, v), cell in cells.items():
            mask[v - v_min][u - u_min] = cell

        visited = [[False for _ in range(cols)] for _ in range(rows)]
        surfaces: List[Dict[str, Any]] = []

        for row in range(rows):
            for col in range(cols):
                cell = mask[row][col]
                if cell is None or visited[row][col]:
                    continue

                key, block_id = cell
                width = 1
                while col + width < cols:
                    other = mask[row][col + width]
                    if (other is None or visited[row][col + width]
                            or other[0] != key):
                        break
                    width += 1

                height = 1
                while row + height < rows:
                    can_expand = True
                    for offset in range(width):
                        other = mask[row + height][col + offset]
                        if (other is None or visited[row + height][col + offset]
                                or other[0] != key):
                            can_expand = False
                            break
                    if not can_expand:
                        break
                    height += 1

                for r in range(row, row + height):
                    for c in range(col, col + width):
                        visited[r][c] = True

                u0 = u_min + col
                v0 = v_min + row

                if face_name in ("top", "bottom"):
                    origin = (u0, plane, v0)
                    size_x = width
                    size_y = 1
                    size_z = height
                    uv_face = "up" if face_name == "top" else "down"
                    uv_rect = [0, 0, 16 * size_x, 16 * size_z]
                elif face_name in ("north", "south"):
                    origin = (u0, v0, plane)
                    size_x = width
                    size_y = height
                    size_z = 1
                    uv_face = face_name
                    uv_rect = [0, 0, 16 * size_x, 16 * size_y]
                else:
                    origin = (plane, v0, u0)
                    size_x = 1
                    size_y = height
                    size_z = width
                    uv_face = face_name
                    uv_rect = [0, 0, 16 * size_z, 16 * size_y]

                vertices, uvs = self._build_merged_surface(
                    uv_face, origin, size_x, size_y, size_z, uv_rect
                )

                if key[0] == "tex":
                    surfaces.append({
                        "vertices": vertices,
                        "uvs": uvs,
                        "texture": key[1],
                        "tint": None,
                        "face": face_name,
                        "block_id": block_id,
                    })
                else:
                    surfaces.append({
                        "vertices": vertices,
                        "color": key[1],
                        "face": face_name,
                        "block_id": block_id,
                    })

        return surfaces

    def _build_merged_surface(self, uv_face: str, origin: Tuple[int, int, int],
                              size_x: int, size_y: int, size_z: int,
                              uv_rect: List[float]) -> Tuple[List[Tuple[float, float, float]],
                                                          List[Tuple[float, float]]]:
        from_coords = [0.0, 0.0, 0.0]
        to_coords = [float(size_x), float(size_y), float(size_z)]
        local_vertices = self._get_face_vertices(uv_face, from_coords, to_coords)
        uvs = self._normalize_uvs(
            self._get_vertex_uvs(uv_face, local_vertices, from_coords, to_coords, uv_rect)
        )
        vertices = [
            (vertex[0] + origin[0], vertex[1] + origin[1], vertex[2] + origin[2])
            for vertex in local_vertices
        ]
        return vertices, uvs

    def _has_neighbor(self, position: Tuple[int, int, int], face_name: str) -> bool:
        direction = self.FACE_DIRS.get(face_name)
        if not direction:
            return False
        dx, dy, dz = direction
        neighbor = (position[0] + dx, position[1] + dy, position[2] + dz)
        return neighbor in self.blocks

    def _get_face_vertices(self, face_name: str, from_coords: List[float],
                           to_coords: List[float]) -> List[Tuple[float, float, float]]:
        x1, y1, z1 = from_coords
        x2, y2, z2 = to_coords

        if face_name == "north":
            return [(x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1)]
        if face_name == "south":
            return [(x1, y1, z2), (x1, y2, z2), (x2, y2, z2), (x2, y1, z2)]
        if face_name == "east":
            return [(x2, y1, z1), (x2, y1, z2), (x2, y2, z2), (x2, y2, z1)]
        if face_name == "west":
            return [(x1, y1, z1), (x1, y2, z1), (x1, y2, z2), (x1, y1, z2)]
        if face_name == "up":
            return [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)]
        if face_name == "down":
            return [(x1, y1, z1), (x1, y1, z2), (x2, y1, z2), (x2, y1, z1)]

        return [(x1, y1, z1), (x2, y1, z1), (x2, y2, z1), (x1, y2, z1)]

    def _get_uv_rect(self, face_name: str, from_coords: List[float],
                     to_coords: List[float], face_data: Dict[str, Any]) -> List[float]:
        if "uv" in face_data:
            return face_data["uv"]

        x1, y1, z1 = from_coords
        x2, y2, z2 = to_coords

        if face_name in ("north", "south"):
            return [x1, 16 - y2, x2, 16 - y1]
        if face_name in ("east", "west"):
            return [z1, 16 - y2, z2, 16 - y1]
        if face_name == "up":
            return [x1, z1, x2, z2]
        if face_name == "down":
            return [x1, 16 - z2, x2, 16 - z1]

        return [0, 0, 16, 16]

    def _get_vertex_uvs(self, face_name: str, vertices: List[Tuple[float, float, float]],
                        from_coords: List[float], to_coords: List[float],
                        uv_rect: List[float]) -> List[Tuple[float, float]]:
        x1, y1, z1 = from_coords
        x2, y2, z2 = to_coords
        u1, v1, u2, v2 = uv_rect
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1

        uvs: List[Tuple[float, float]] = []
        for vx, vy, vz in vertices:
            if face_name == "north":
                u_factor = (vx - x1) / dx if dx else 0.0
                v_factor = (y2 - vy) / dy if dy else 0.0
            elif face_name == "south":
                u_factor = (x2 - vx) / dx if dx else 0.0
                v_factor = (y2 - vy) / dy if dy else 0.0
            elif face_name == "east":
                u_factor = (vz - z1) / dz if dz else 0.0
                v_factor = (y2 - vy) / dy if dy else 0.0
            elif face_name == "west":
                u_factor = (z2 - vz) / dz if dz else 0.0
                v_factor = (y2 - vy) / dy if dy else 0.0
            elif face_name == "up":
                u_factor = (vx - x1) / dx if dx else 0.0
                v_factor = (vz - z1) / dz if dz else 0.0
            elif face_name == "down":
                u_factor = (vx - x1) / dx if dx else 0.0
                v_factor = (z2 - vz) / dz if dz else 0.0
            else:
                u_factor = (vx - x1) / dx if dx else 0.0
                v_factor = (y2 - vy) / dy if dy else 0.0

            u = u1 + u_factor * (u2 - u1)
            v = v1 + v_factor * (v2 - v1)
            uvs.append((u, v))

        return uvs

    def _apply_uv_rotation(self, uvs: List[Tuple[float, float]], uv_rect: List[float],
                           rotation: int) -> List[Tuple[float, float]]:
        rotation = rotation % 360
        if rotation == 0:
            return uvs

        u1, v1, u2, v2 = uv_rect
        width = u2 - u1
        height = v2 - v1
        if width == 0 or height == 0:
            return uvs

        rotated: List[Tuple[float, float]] = []
        for u, v in uvs:
            s = (u - u1) / width
            t = (v - v1) / height

            if rotation == 90:
                s, t = t, 1 - s
            elif rotation == 180:
                s, t = 1 - s, 1 - t
            elif rotation == 270:
                s, t = 1 - t, s

            rotated.append((u1 + s * width, v1 + t * height))

        return rotated

    def _normalize_uvs(self, uvs: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        normalized = []
        for u, v in uvs:
            normalized.append((u / 16.0, v / 16.0))
        return normalized

    def _get_cube_vertices(self, position: Tuple[int, int, int], face_name: str) -> List[Tuple[float, float, float]]:
        x, y, z = position
        if face_name == "top":
            return [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
        if face_name == "bottom":
            return [(x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z)]
        if face_name == "north":
            return [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]
        if face_name == "south":
            return [(x, y, z + 1), (x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)]
        if face_name == "east":
            return [(x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z)]
        if face_name == "west":
            return [(x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1)]

        return [(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)]

    def _map_cube_face(self, face_name: str) -> str:
        if face_name == "top":
            return "top"
        if face_name == "bottom":
            return "bottom"
        return "side"

    def _apply_rotation(self, vertices: List[Tuple[float, float, float]],
                        rotation: Tuple[float, float, float]) -> List[Tuple[float, float, float]]:
        rot_x, rot_y, rot_z = rotation
        if rot_x == 0 and rot_y == 0 and rot_z == 0:
            return vertices

        center = (0.5, 0.5, 0.5)
        rotated = []
        for x, y, z in vertices:
            px, py, pz = x - center[0], y - center[1], z - center[2]
            if rot_x:
                rad = math.radians(rot_x)
                py, pz = py * math.cos(rad) - pz * math.sin(rad), py * math.sin(rad) + pz * math.cos(rad)
            if rot_y:
                rad = math.radians(rot_y)
                px, pz = px * math.cos(rad) + pz * math.sin(rad), -px * math.sin(rad) + pz * math.cos(rad)
            if rot_z:
                rad = math.radians(rot_z)
                px, py = px * math.cos(rad) - py * math.sin(rad), px * math.sin(rad) + py * math.cos(rad)
            rotated.append((px + center[0], py + center[1], pz + center[2]))

        return rotated

    def _apply_shading(self, color: Tuple[int, int, int], face_name: str) -> Tuple[int, int, int]:
        factor = self.FACE_SHADE.get(face_name, 1.0)
        return (
            min(255, int(color[0] * factor)),
            min(255, int(color[1] * factor)),
            min(255, int(color[2] * factor)),
        )

    def _rotation_for_facing(self, direction: str) -> Tuple[float, float, float]:
        if direction == "north":
            return (0, 0, 0)
        if direction == "east":
            return (0, 90, 0)
        if direction == "south":
            return (0, 180, 0)
        if direction == "west":
            return (0, 270, 0)
        if direction == "up":
            return (90, 0, 0)
        if direction == "down":
            return (270, 0, 0)
        return (0, 0, 0)

    def _is_true(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"
