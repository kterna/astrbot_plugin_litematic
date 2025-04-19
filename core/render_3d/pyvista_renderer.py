import os
import numpy as np
import pyvista as pv
from typing import Dict, List, Tuple, Any, Optional
from PIL import Image

class PyVistaRenderer:
    """
    使用PyVista进行3D渲染的渲染器
    """
    
    def __init__(self, model_data: Dict[str, Any], surface_data: List[Dict[str, Any]], color_mapper: Any) -> None:
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
        self.mesh = None
        
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
            
            # 创建空网格
            self.mesh = pv.PolyData()
            
            # 为每个面创建一个正方形面片
            all_verts = []  # 所有顶点
            all_faces = []  # 所有面片
            all_colors = []  # 所有颜色
            
            vert_count = 0
            
            # 每个面有4个顶点和1个面片定义
            for surface in self.surface_data:
                position = surface['position']
                face = surface['face']
                block_id = surface['block_id']
                
                # 获取面的颜色
                color = self.color_mapper.get_face_color(block_id, face)
                color_normalized = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
                
                # 根据面的方向创建顶点
                x, y, z = position
                vertices = []
                
                # 根据面朝向定义四个顶点
                if face == 'top':  # +Y
                    vertices = [
                        [x, y + 1, z],
                        [x + 1, y + 1, z],
                        [x + 1, y + 1, z + 1],
                        [x, y + 1, z + 1]
                    ]
                elif face == 'bottom':  # -Y
                    vertices = [
                        [x, y, z],
                        [x, y, z + 1],
                        [x + 1, y, z + 1],
                        [x + 1, y, z]
                    ]
                elif face == 'north':  # -Z
                    vertices = [
                        [x, y, z],
                        [x + 1, y, z],
                        [x + 1, y + 1, z],
                        [x, y + 1, z]
                    ]
                elif face == 'south':  # +Z
                    vertices = [
                        [x, y, z + 1],
                        [x, y + 1, z + 1],
                        [x + 1, y + 1, z + 1],
                        [x + 1, y, z + 1]
                    ]
                elif face == 'east':  # +X
                    vertices = [
                        [x + 1, y, z],
                        [x + 1, y, z + 1],
                        [x + 1, y + 1, z + 1],
                        [x + 1, y + 1, z]
                    ]
                elif face == 'west':  # -X
                    vertices = [
                        [x, y, z],
                        [x, y + 1, z],
                        [x, y + 1, z + 1],
                        [x, y, z + 1]
                    ]
                
                # 添加顶点
                for vertex in vertices:
                    all_verts.append(vertex)
                    all_colors.append(color_normalized)
                
                # 添加面片 (四边形，需要5个整数：4个顶点索引)
                face_indices = [4]  # 第一个数字是面的顶点数
                for i in range(4):
                    face_indices.append(vert_count + i)
                all_faces.extend(face_indices)
                
                # 更新顶点计数
                vert_count += 4
            
            # 创建几何体
            self.mesh = pv.PolyData(np.array(all_verts), np.array(all_faces))
            
            # 添加颜色
            self.mesh.point_data['colors'] = np.array(all_colors)
            
            return True
            
        except Exception as e:
            print(f"创建网格时出错: {e}")
            return False
    
    def render_scene(self, camera_position: Optional[Tuple[float, float, float]] = None,
                    background_color: Optional[Tuple[float, float, float]] = None,
                    window_size: Optional[List[int]] = None) -> Optional[Image.Image]:
        """
        渲染3D场景并返回图像
        
        Args:
            camera_position: 相机位置，如果为None则使用配置值
            background_color: 背景颜色，如果为None则使用配置值
            window_size: 窗口大小，如果为None则使用配置值
            
        Returns:
            Optional[Image.Image]: 渲染的图像，如果失败则返回None
        """
        try:
            if self.mesh is None:
                if not self.create_mesh():
                    return None
            
            # 更新配置
            if camera_position is not None:
                self.config['camera_position'] = camera_position
            if background_color is not None:
                self.config['background_color'] = background_color
            if window_size is not None:
                self.config['window_size'] = window_size
            
            # 创建Plotter对象（用于离屏渲染）
            plotter = pv.Plotter(off_screen=True, window_size=self.config['window_size'])
            
            # 设置背景
            plotter.set_background(self.config['background_color'])
            
            # 添加网格到场景
            plotter.add_mesh(
                self.mesh,
                scalars='colors',
                rgb=True,
                show_edges=False,
                smooth_shading=self.config['smooth_shading'],
                render_points_as_spheres=self.config['render_points_as_spheres'],
                lighting=self.config['lighting']
            )
            
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
            
            # 设置视图选项
            if self.config['show_axes']:
                plotter.add_axes()
            
            # 渲染场景
            img = plotter.screenshot(return_img=True)
            plotter.close()
            
            # 转换为PIL图像
            pil_img = Image.fromarray(img)
            
            return pil_img
            
        except Exception as e:
            print(f"渲染场景时出错: {e}")
            return None
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        更新渲染配置
        
        Args:
            config: 新的配置字典
        """
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value 