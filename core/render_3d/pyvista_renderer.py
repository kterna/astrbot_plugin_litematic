import os
import numpy as np
import pyvista as pv
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image

from .texture_sampler import TextureSampler

class PyVistaRenderer:
    """
    使用PyVista进行3D渲染的渲染器
    """
    
    def __init__(self, model_data: Dict[str, Any], surface_data: List[Dict[str, Any]],
                 color_mapper: Any, resource_dir: Optional[str] = None,
                 native_textures: bool = False) -> None:
        """
        初始化PyVista渲染器
        
        Args:
            model_data: 3D模型数据，包含方块和边界信息
            surface_data: 可见表面数据列表
            color_mapper: 颜色映射器对象
        """
        self.model_data = model_data
        self.surface_data = surface_data
        self.color_mapper = color_mapper
        self.plotter = None
        self._plotter_window_size = None
        self._plotter_background = None
        self.mesh = None
        self.textured_meshes: List[Tuple[pv.PolyData, pv.Texture]] = []
        self.texture_sampler = (
            TextureSampler(resource_dir, native_textures=native_textures)
            if resource_dir else None
        )
        
        # 渲染配置
        self.config = {
            'background_color': (0.95, 0.95, 0.95),  # 浅灰色背景
            'window_size': [800, 600],             # 窗口大小
            'camera_position': 'iso',              # 默认相机位置
            'show_axes': True,                     # 显示坐标轴
            'lighting': True,                      # 启用光照
            'smooth_shading': False,               # 不使用平滑着色
            'render_points_as_spheres': False,     # 不将点渲染为球体
            'anti_aliasing': True                  # 启用抗锯齿
        }
    
    def create_mesh(self) -> bool:
        """
        根据表面数据创建3D网格
        
        Returns:
            bool: 是否成功创建网格
        """
        try:
            # 如果没有表面数据，返回失败
            if not self.surface_data or len(self.surface_data) == 0:
                print("没有表面数据，无法创建网格")
                return False
            
            self.mesh = None
            self.textured_meshes = []

            textured_surfaces = [
                surface for surface in self.surface_data
                if "texture" in surface and "uvs" in surface and self.texture_sampler
            ]
            colored_surfaces = [
                surface for surface in self.surface_data
                if "texture" not in surface or "uvs" not in surface
            ]
            
            if textured_surfaces and self.texture_sampler:
                self.textured_meshes = self._build_textured_meshes(textured_surfaces)

            if colored_surfaces:
                self.mesh = self._build_color_mesh(colored_surfaces)

            return bool(self.mesh or self.textured_meshes)
            
        except Exception as e:
            print(f"创建网格时出错: {e}")
            return False
    
    def render_scene(self, camera_position: Optional[Tuple[float, float, float]] = None,
                    background_color: Optional[Tuple[float, float, float]] = None,
                    window_size: Optional[List[int]] = None,
                    reuse_plotter: bool = False) -> Optional[Image.Image]:
        """
        渲染3D场景并返回图像

        Args:
            camera_position: 相机位置，如果为None则使用配置值
            background_color: 背景颜色，如果为None则使用配置值
            window_size: 窗口大小，如果为None则使用配置值
            reuse_plotter: 是否复用渲染管线

        Returns:
            Optional[Image.Image]: 渲染的图像，如果失败则返回None
        """
        try:
            if self.mesh is None and not self.textured_meshes:
                if not self.create_mesh():
                    return None

            # 更新配置
            if camera_position is not None:
                self.config['camera_position'] = camera_position
            if background_color is not None:
                self.config['background_color'] = background_color
            if window_size is not None:
                self.config['window_size'] = window_size

            if reuse_plotter:
                plotter = self._get_or_create_plotter(
                    self.config['window_size'],
                    self.config['background_color']
                )
            else:
                plotter = pv.Plotter(off_screen=True, window_size=self.config['window_size'])
                plotter.set_background(self.config['background_color'])
                self._add_meshes(plotter)

            # 设置相机位置
            if self.config['camera_position'] == 'iso':
                # 根据模型尺寸计算合适的相机位置
                bounds = self.model_data['bounds']
                center_x = (bounds['min_x'] + bounds['max_x']) / 2
                center_y = (bounds['min_y'] + bounds['max_y']) / 2
                center_z = (bounds['min_z'] + bounds['max_z']) / 2

                # 计算模型尺寸的最大值
                size_x = bounds['max_x'] - bounds['min_x'] + 1
                size_y = bounds['max_y'] - bounds['min_y'] + 1
                size_z = bounds['max_z'] - bounds['min_z'] + 1
                max_size = max(size_x, size_y, size_z)

                # 设置相机位置为中心点的等距视角，距离为模型尺寸的2倍
                distance = max_size * 2
                camera_pos = (
                    center_x + distance,
                    center_y + distance,
                    center_z + distance
                )

                plotter.camera_position = [
                    camera_pos,
                    (center_x, center_y, center_z),
                    (0, 1, 0)  # 向上方向
                ]
            else:
                plotter.camera_position = self.config['camera_position']

            # 渲染场景
            if reuse_plotter:
                plotter.render()
            img = plotter.screenshot(return_img=True)
            if not reuse_plotter:
                plotter.close()

            # 转换为PIL图像
            img = np.array(img, copy=True)
            pil_img = Image.fromarray(img)

            return pil_img

        except Exception as e:
            print(f"渲染场景时出错: {e}")
            return None

    def _add_meshes(self, plotter: pv.Plotter) -> None:
        for mesh, texture in self.textured_meshes:
            plotter.add_mesh(
                mesh,
                texture=texture,
                show_edges=False,
                smooth_shading=self.config['smooth_shading'],
                render_points_as_spheres=self.config['render_points_as_spheres'],
                lighting=self.config['lighting'],
            )

        if self.mesh is not None:
            plotter.add_mesh(
                self.mesh,
                scalars='colors',
                rgb=True,
                show_edges=False,
                smooth_shading=self.config['smooth_shading'],
                render_points_as_spheres=self.config['render_points_as_spheres'],
                lighting=self.config['lighting'],
            )

        if self.config['show_axes']:
            plotter.add_axes()

    def _get_or_create_plotter(self, window_size: List[int],
                               background_color: Tuple[float, float, float]) -> pv.Plotter:
        window_size_key = tuple(window_size)
        background_key = tuple(background_color)
        if self.plotter is not None:
            if (self._plotter_window_size == window_size_key
                    and self._plotter_background == background_key):
                return self.plotter
            try:
                self.plotter.close()
            except Exception:
                pass

        self.plotter = pv.Plotter(off_screen=True, window_size=list(window_size))
        self.plotter.set_background(background_color)
        self._add_meshes(self.plotter)
        self._plotter_window_size = window_size_key
        self._plotter_background = background_key
        return self.plotter

    def _enable_texture_repeat(self, texture: pv.Texture) -> None:
        try:
            if hasattr(texture, "repeat"):
                texture.repeat = True
                return
            if hasattr(texture, "SetRepeat"):
                texture.SetRepeat(True)
                return
            if hasattr(texture, "RepeatOn"):
                texture.RepeatOn()
        except Exception:
            return

    def close(self) -> None:
        if self.plotter is None:
            return
        try:
            self.plotter.close()
        except Exception:
            pass
        self.plotter = None
        self._plotter_window_size = None
        self._plotter_background = None

    def set_config(self, config: Dict[str, Any]) -> None:
        """
        更新渲染配置
        
        Args:
            config: 新的配置字典
        """
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value

    def _build_color_mesh(self, surfaces: List[Dict[str, Any]]) -> pv.PolyData:
        all_verts: List[List[float]] = []
        all_faces: List[int] = []
        all_colors: List[Tuple[float, float, float]] = []
        vert_count = 0

        for surface in surfaces:
            face = surface.get('face')
            block_id = surface.get('block_id', '')

            if 'color' in surface:
                color = surface['color']
            else:
                color = self.color_mapper.get_face_color(block_id, face)
            color_normalized = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

            if 'vertices' in surface:
                vertices = surface['vertices']
            else:
                position = surface['position']
                x, y, z = position
                vertices = []

                if face == 'top':
                    vertices = [
                        [x, y + 1, z],
                        [x + 1, y + 1, z],
                        [x + 1, y + 1, z + 1],
                        [x, y + 1, z + 1]
                    ]
                elif face == 'bottom':
                    vertices = [
                        [x, y, z],
                        [x, y, z + 1],
                        [x + 1, y, z + 1],
                        [x + 1, y, z]
                    ]
                elif face == 'north':
                    vertices = [
                        [x, y, z],
                        [x + 1, y, z],
                        [x + 1, y + 1, z],
                        [x, y + 1, z]
                    ]
                elif face == 'south':
                    vertices = [
                        [x, y, z + 1],
                        [x, y + 1, z + 1],
                        [x + 1, y + 1, z + 1],
                        [x + 1, y, z + 1]
                    ]
                elif face == 'east':
                    vertices = [
                        [x + 1, y, z],
                        [x + 1, y, z + 1],
                        [x + 1, y + 1, z + 1],
                        [x + 1, y + 1, z]
                    ]
                elif face == 'west':
                    vertices = [
                        [x, y, z],
                        [x, y + 1, z],
                        [x, y + 1, z + 1],
                        [x, y, z + 1]
                    ]

            for vertex in vertices:
                all_verts.append(vertex)
                all_colors.append(color_normalized)

            all_faces.extend([4, vert_count, vert_count + 1, vert_count + 2, vert_count + 3])
            vert_count += 4

        mesh = pv.PolyData(np.array(all_verts, dtype=np.float32), np.array(all_faces))
        mesh.point_data['colors'] = np.array(all_colors, dtype=np.float32)
        return mesh

    def _build_textured_meshes(self, surfaces: List[Dict[str, Any]]) -> List[Tuple[pv.PolyData, pv.Texture]]:
        if not self.texture_sampler:
            return []

        grouped: Dict[Tuple[str, Optional[Tuple[int, int, int]]], List[Dict[str, Any]]] = {}
        for surface in surfaces:
            texture_name = surface.get("texture")
            tint = surface.get("tint")
            if not texture_name:
                continue
            grouped.setdefault((texture_name, tint), []).append(surface)

        textured_meshes: List[Tuple[pv.PolyData, pv.Texture]] = []

        for (texture_name, tint), group_surfaces in grouped.items():
            all_verts: List[List[float]] = []
            all_faces: List[int] = []
            all_tcoords: List[Tuple[float, float]] = []
            vert_count = 0

            for surface in group_surfaces:
                vertices = surface.get("vertices", [])
                uvs = surface.get("uvs", [])
                if len(vertices) != len(uvs):
                    continue

                for vertex, uv in zip(vertices, uvs):
                    all_verts.append(vertex)
                    all_tcoords.append(uv)

                all_faces.extend([4, vert_count, vert_count + 1, vert_count + 2, vert_count + 3])
                vert_count += 4

            if not all_verts:
                continue

            mesh = pv.PolyData(np.array(all_verts, dtype=np.float32), np.array(all_faces))
            mesh.active_texture_coordinates = np.array(all_tcoords, dtype=np.float32)

            texture_image = self.texture_sampler.get_texture_image(texture_name, tint)
            texture_image = texture_image.transpose(Image.FLIP_TOP_BOTTOM)
            texture = pv.Texture(np.array(texture_image))

            self._enable_texture_repeat(texture)

            textured_meshes.append((mesh, texture))

        return textured_meshes
