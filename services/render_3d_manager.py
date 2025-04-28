import os
import asyncio
import tempfile
from typing import Dict, Any, Optional, List, Tuple

from litemapy import Schematic
from astrbot import logger

from ..core.model_3d.model_builder import ModelBuilder
from ..core.model_3d.surface_detector import SurfaceDetector
from ..core.model_3d.color_mapper import ColorMapper
from ..core.render_3d.pyvista_renderer import PyVistaRenderer
from ..core.render_3d.animation_generator import AnimationGenerator
from ..core.render_3d.gif_exporter import GifExporter
from ..utils.config import Config
from ..utils.exceptions import RenderError

class Render3DManager:
    """
    3D渲染管理器，协调各组件进行3D渲染工作
    """
    
    def __init__(self, config: Config) -> None:
        """
        初始化3D渲染管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.resource_dir = config.get_resource_dir()
    
    async def render_litematic_3d_async(self, file_path: str, animation_type: str = "rotation",
                                     frames: int = 36, duration: int = 100, 
                                     elevation: float = 30.0, optimize: bool = True) -> str:
        """
        异步渲染litematic文件并生成3D动画GIF
        
        Args:
            file_path: litematic文件路径
            animation_type: 动画类型 (rotation/orbit/zoom)
            frames: 帧数
            duration: 每帧持续时间(毫秒)
            elevation: 相机仰角(度)
            optimize: 是否优化GIF大小
            
        Returns:
            str: 输出文件路径
            
        Raises:
            RenderError: 渲染失败时
        """
        # 使用asyncio.to_thread将同步操作包装成异步
        return await asyncio.to_thread(
            self.render_litematic_3d,
            file_path, animation_type, frames, duration, elevation, optimize
        )
    
    def render_litematic_3d(self, file_path: str, animation_type: str = "rotation",
                         frames: int = 36, duration: int = 100, 
                         elevation: float = 30.0, optimize: bool = True) -> str:
        """
        渲染litematic文件并生成3D动画GIF
        
        Args:
            file_path: litematic文件路径
            animation_type: 动画类型 (rotation/orbit/zoom)
            frames: 帧数
            duration: 每帧持续时间(毫秒)
            elevation: 相机仰角(度)
            optimize: 是否优化GIF大小
            
        Returns:
            str: 输出文件路径
            
        Raises:
            RenderError: 渲染失败时
        """
        try:
            # 1. 加载litematic文件
            schematic = Schematic.load(file_path)
            
            # 2. 构建3D模型
            model_builder = ModelBuilder()
            if not model_builder.build_from_litematic(schematic):
                raise RenderError("构建3D模型失败", code=2001)
                
            model_data = model_builder.get_model_data()
            
            # 3. 检测可见表面
            surface_detector = SurfaceDetector(model_data)
            surface_detector.detect_visible_surfaces()
            surface_data = surface_detector.get_surface_data_for_rendering()
            
            # 4. 创建颜色映射器
            color_mapper = ColorMapper(self.resource_dir)
            
            # 5. 创建渲染器
            renderer = PyVistaRenderer(model_data, surface_data, color_mapper)
            
            # 6. 创建网格
            if not renderer.create_mesh():
                raise RenderError("创建网格失败", code=2002)
            
            # 7. 生成动画
            animation_generator = AnimationGenerator(renderer)
            
            # 根据动画类型选择不同的生成方法
            success = False
            if animation_type == "rotation":
                success = animation_generator.generate_rotation_frames(
                    n_frames=frames, 
                    elevation=elevation
                )
            elif animation_type == "orbit":
                success = animation_generator.generate_orbit_frames(
                    n_frames=frames,
                    start_elevation=0,
                    end_elevation=90
                )
            elif animation_type == "zoom":
                success = animation_generator.generate_zoom_frames(
                    n_frames=frames
                )
            else:
                # 默认为旋转动画
                success = animation_generator.generate_rotation_frames(
                    n_frames=frames, 
                    elevation=elevation
                )
            
            if not success:
                raise RenderError(f"生成{animation_type}动画失败", code=2003)
                
            frames_list = animation_generator.get_frames()
            
            # 8. 导出GIF
            gif_exporter = GifExporter()
            
            # 如果需要优化大小
            if optimize:
                # 限制GIF大小为5MB
                frames_list = gif_exporter.optimize_gif_size(frames_list, 5 * 1024 * 1024)
            
            # 创建临时文件
            temp_gif_path = gif_exporter.export_gif_with_temp(frames_list, duration=duration)
            
            if not temp_gif_path:
                raise RenderError("导出GIF失败", code=2004)
            
            return temp_gif_path
            
        except RenderError:
            # 重新抛出渲染错误
            raise
        except Exception as e:
            # 捕获并转换为渲染错误
            logger.error(f"3D渲染过程中出现未知错误: {e}")
            raise RenderError(f"3D渲染失败: {str(e)}", code=2000)
            
    def render_single_view(self, file_path: str, view_angle: Tuple[float, float, float] = None) -> str:
        """
        渲染litematic文件的单一视图
        
        Args:
            file_path: litematic文件路径
            view_angle: 视角(x, y, z)，如果为None则使用默认等距视角
            
        Returns:
            str: 输出图像文件路径
            
        Raises:
            RenderError: 渲染失败时
        """
        try:
            # 1. 加载和构建模型
            schematic = Schematic.load(file_path)
            model_builder = ModelBuilder()
            if not model_builder.build_from_litematic(schematic):
                raise RenderError("构建3D模型失败", code=2001)
                
            model_data = model_builder.get_model_data()
            
            # 2. 检测可见表面
            surface_detector = SurfaceDetector(model_data)
            surface_detector.detect_visible_surfaces()
            surface_data = surface_detector.get_surface_data_for_rendering()
            
            # 3. 创建颜色映射器和渲染器
            color_mapper = ColorMapper(self.resource_dir)
            renderer = PyVistaRenderer(model_data, surface_data, color_mapper)
            
            # 4. 创建网格
            if not renderer.create_mesh():
                raise RenderError("创建网格失败", code=2002)
            
            # 5. 渲染单个视图
            if view_angle:
                # 使用传入的视角
                bounds = model_data['bounds']
                center_x = (bounds['min_x'] + bounds['max_x']) / 2
                center_y = (bounds['min_y'] + bounds['max_y']) / 2
                center_z = (bounds['min_z'] + bounds['max_z']) / 2
                
                image = renderer.render_scene(
                    camera_position=[(view_angle[0], view_angle[1], view_angle[2]), 
                                   (center_x, center_y, center_z), 
                                   (0, 1, 0)]
                )
            else:
                # 使用默认视角
                image = renderer.render_scene()
            
            if image is None:
                raise RenderError("渲染图像失败", code=2005)
            
            # 6. 保存图像
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_img_path = tmp.name
            
            image.save(temp_img_path)
            
            return temp_img_path
            
        except RenderError:
            # 重新抛出渲染错误
            raise
        except Exception as e:
            # 捕获并转换为渲染错误
            logger.error(f"3D渲染单视图时出现未知错误: {e}")
            raise RenderError(f"3D渲染失败: {str(e)}", code=2000) 