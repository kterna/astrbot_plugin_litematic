import os
import asyncio
import tempfile
from typing import Dict, Any, Optional, List, Tuple

from litemapy import Schematic
from astrbot import logger

from ..core.model_3d.model_builder import ModelBuilder
from ..core.model_3d.color_mapper import ColorMapper
from ..core.render_3d.pyvista_renderer import PyVistaRenderer
from ..core.render_3d.surface_builder import SurfaceBuilder
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
                                     elevation: float = 30.0, optimize: bool = True,
                                     window_size: Optional[Tuple[int, int]] = None,
                                     native_textures: bool = False,
                                     native_max_size: Optional[Tuple[int, int]] = None) -> str:
        """
        异步渲染litematic文件并生成3D动画GIF
        
        Args:
            file_path: litematic文件路径
            animation_type: 动画类型 (rotation/orbit/zoom)
            frames: 帧数
            duration: 每帧持续时间(毫秒)
            elevation: 相机仰角(度)
            optimize: 是否优化GIF大小
            window_size: 输出分辨率(width, height)，None表示默认；native_textures为True时会自动估算
            native_textures: 是否使用贴图原生分辨率
            native_max_size: 原生分辨率自动估算的最大尺寸(width, height)
            
        Returns:
            str: 输出文件路径
            
        Raises:
            RenderError: 渲染失败时
        """
        # 使用asyncio.to_thread将同步操作包装成异步
        return await asyncio.to_thread(
            self.render_litematic_3d,
            file_path, animation_type, frames, duration, elevation, optimize,
            window_size, native_textures, native_max_size
        )
    
    def render_litematic_3d(self, file_path: str, animation_type: str = "rotation",
                         frames: int = 36, duration: int = 100, 
                         elevation: float = 30.0, optimize: bool = True,
                         window_size: Optional[Tuple[int, int]] = None,
                         native_textures: bool = False,
                         native_max_size: Optional[Tuple[int, int]] = None) -> str:
        """
        渲染litematic文件并生成3D动画GIF
        
        Args:
            file_path: litematic文件路径
            animation_type: 动画类型 (rotation/orbit/zoom)
            frames: 帧数
            duration: 每帧持续时间(毫秒)
            elevation: 相机仰角(度)
            optimize: 是否优化GIF大小
            window_size: 输出分辨率(width, height)，None表示默认；native_textures为True时会自动估算
            native_textures: 是否使用贴图原生分辨率
            native_max_size: 原生分辨率自动估算的最大尺寸(width, height)
            
        Returns:
            str: 输出文件路径
            
        Raises:
            RenderError: 渲染失败时
        """
        try:
            # 1. 加载litematic文件
            logger.info(f"开始加载Litematic文件: {file_path}")
            schematic = Schematic.load(file_path)
            logger.info(f"Litematic文件加载成功: {schematic.name}")
            
            # 2. 构建3D模型
            logger.info("构建3D模型...")
            model_builder = ModelBuilder()
            if not model_builder.build_from_litematic(schematic):
                raise RenderError("构建3D模型失败", code=2001)
                
            model_data = model_builder.get_model_data()
            logger.info(f"模型构建完成，包含 {model_builder.get_block_count()} 个方块")
            
            # 3. 构建渲染表面（包含纹理采样）
            logger.info("构建渲染表面...")
            surface_builder = SurfaceBuilder(model_data, self.resource_dir, native_textures=native_textures)
            surface_data = surface_builder.build_surfaces()
            logger.info(f"生成 {len(surface_data)} 个渲染表面")

            if window_size is None and native_textures:
                texture_size = surface_builder.texture_sampler.get_native_texture_size()
                window_size = self._calculate_native_window_size(
                    model_data, texture_size, native_max_size
                )
            
            # 4. 创建颜色映射器（作为兜底）
            logger.info("创建颜色映射...")
            color_mapper = ColorMapper(self.resource_dir)
            
            # 5. 创建渲染器
            logger.info("创建渲染器...")
            renderer = PyVistaRenderer(
                model_data,
                surface_data,
                color_mapper,
                resource_dir=self.resource_dir,
                native_textures=native_textures
            )
            
            # 6. 创建网格
            logger.info("创建网格...")
            if not renderer.create_mesh():
                raise RenderError("创建网格失败", code=2002)
            
            # 7. 生成动画
            logger.info(f"生成{animation_type}动画...")
            animation_generator = AnimationGenerator(renderer)

            # 8. 导出GIF（流式写入，降低内存占用）
            logger.info("导出GIF...")
            gif_exporter = GifExporter()

            resize_to = None
            max_size_bytes = self.config.get_config_value("max_gif_size_bytes", 5 * 1024 * 1024)
            if optimize:
                window_size_for_estimate = window_size
                if window_size_for_estimate is None:
                    window_size_for_estimate = renderer.config.get("window_size", [800, 600])
                if window_size_for_estimate:
                    resize_to = gif_exporter.estimate_scaled_size(
                        int(window_size_for_estimate[0]),
                        int(window_size_for_estimate[1]),
                        frames,
                        max_size_bytes
                    )

            frame_iter = None
            if animation_type == "rotation":
                frame_iter = animation_generator.iter_rotation_frames(
                    n_frames=frames,
                    elevation=elevation,
                    window_size=window_size
                )
            elif animation_type == "orbit":
                frame_iter = animation_generator.iter_orbit_frames(
                    n_frames=frames,
                    start_elevation=0,
                    end_elevation=90,
                    window_size=window_size
                )
            elif animation_type == "zoom":
                frame_iter = animation_generator.iter_zoom_frames(
                    n_frames=frames,
                    window_size=window_size
                )
            else:
                frame_iter = animation_generator.iter_rotation_frames(
                    n_frames=frames,
                    elevation=elevation,
                    window_size=window_size
                )

            temp_gif_path = gif_exporter.export_gif_with_temp_stream(
                frame_iter,
                duration=duration,
                resize_to=resize_to
            )

            if temp_gif_path:
                logger.info(f"动画生成完成，共 {frames} 帧")
            else:
                # 流式导出失败时回退到内存模式
                success = False
                if animation_type == "rotation":
                    success = animation_generator.generate_rotation_frames(
                        n_frames=frames,
                        elevation=elevation,
                        window_size=window_size
                    )
                elif animation_type == "orbit":
                    success = animation_generator.generate_orbit_frames(
                        n_frames=frames,
                        start_elevation=0,
                        end_elevation=90,
                        window_size=window_size
                    )
                elif animation_type == "zoom":
                    success = animation_generator.generate_zoom_frames(
                        n_frames=frames,
                        window_size=window_size
                    )
                else:
                    success = animation_generator.generate_rotation_frames(
                        n_frames=frames,
                        elevation=elevation,
                        window_size=window_size
                    )

                if not success:
                    raise RenderError(f"生成{animation_type}动画失败", code=2003)

                frames_list = animation_generator.get_frames()
                logger.info(f"动画生成完成，共 {len(frames_list)} 帧")

                if optimize:
                    frames_list = gif_exporter.optimize_gif_size(frames_list, max_size_bytes)

                temp_gif_path = gif_exporter.export_gif_with_temp(frames_list, duration=duration)

            if not temp_gif_path:
                raise RenderError("导出GIF失败", code=2004)

            logger.info(f"GIF导出完成: {temp_gif_path}")

            return temp_gif_path
            
        except RenderError:
            # 重新抛出渲染错误
            raise
        except Exception as e:
            # 捕获并转换为渲染错误
            logger.error(f"3D渲染过程中出现未知错误: {e}")
            raise RenderError(f"3D渲染失败: {str(e)}", code=2000)
            
    def render_single_view(self, file_path: str, view_angle: Tuple[float, float, float] = None,
                           window_size: Optional[Tuple[int, int]] = None,
                           native_textures: bool = False,
                           native_max_size: Optional[Tuple[int, int]] = None) -> str:
        """
        渲染litematic文件的单一视图
        
        Args:
            file_path: litematic文件路径
            view_angle: 视角(x, y, z)，如果为None则使用默认等距视角
            window_size: 输出分辨率(width, height)，None表示默认；native_textures为True时会自动估算
            native_textures: 是否使用贴图原生分辨率
            native_max_size: 原生分辨率自动估算的最大尺寸(width, height)
            
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
            
            # 2. 构建渲染表面
            surface_builder = SurfaceBuilder(model_data, self.resource_dir, native_textures=native_textures)
            surface_data = surface_builder.build_surfaces()

            if window_size is None and native_textures:
                texture_size = surface_builder.texture_sampler.get_native_texture_size()
                window_size = self._calculate_native_window_size(
                    model_data, texture_size, native_max_size
                )
            
            # 3. 创建颜色映射器和渲染器
            color_mapper = ColorMapper(self.resource_dir)
            renderer = PyVistaRenderer(
                model_data,
                surface_data,
                color_mapper,
                resource_dir=self.resource_dir,
                native_textures=native_textures
            )
            
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
                                   (0, 1, 0)],
                    window_size=window_size
                )
            else:
                # 使用默认视角
                image = renderer.render_scene(window_size=window_size)
            
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

    def _calculate_native_window_size(self, model_data: Dict[str, Any],
                                      texture_size: int,
                                      max_size: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
        dimensions = model_data.get("dimensions", {})
        width_blocks = dimensions.get("width", 1)
        length_blocks = dimensions.get("length", 1)
        height_blocks = dimensions.get("height", 1)

        width_blocks = max(1, int(width_blocks))
        length_blocks = max(1, int(length_blocks))
        height_blocks = max(1, int(height_blocks))

        projected_width = width_blocks + length_blocks
        projected_height = height_blocks + max(width_blocks, length_blocks) * 0.5

        width = int(projected_width * texture_size)
        height = int(projected_height * texture_size)

        min_width, min_height = 800, 600
        default_max_size = 16384
        max_width, max_height = max_size if max_size else (default_max_size, default_max_size)
        max_width = max(min_width, max_width)
        max_height = max(min_height, max_height)
        width = max(min_width, min(width, max_width))
        height = max(min_height, min(height, max_height))

        return (width, height)
