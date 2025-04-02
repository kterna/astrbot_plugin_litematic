import os
import tempfile
from typing import Callable, Dict, Optional, Union, Any
from PIL import Image as PILImage
from astrbot import logger
from ..core.image_render.build_model import World
from ..core.image_render.render2D import Render2D
from litemapy import Schematic
from ..utils.config import Config

class RenderManager:
    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.resource_dir: str = config.get_resource_dir()
    
    def render_litematic(self, file_path: str, view_type: str = "combined", scale: int = 1) -> str:
        """
        渲染litematic文件
        
        Args:
            file_path: litematic文件路径
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            scale: 缩放比例
            
        Returns:
            str: 临时图像文件路径
        """
        try:
            # 加载litematic文件
            schem = Schematic.load(file_path)
            
            # 创建3D模型
            world = World()
            world.add_blocks(schem)
            
            # 创建渲染器
            renderer = Render2D(
                world=world,
                resource_base_path=self.resource_dir
            )
            
            # 根据视图类型选择渲染方法
            image = self._render_view(renderer, view_type, scale)
            
            # 创建临时文件并保存
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_file = tmp.name
                
            # 保存图像
            renderer.save_image(image, temp_file)
            
            return temp_file
            
        except Exception as e:
            logger.error(f"渲染litematic文件失败: {e}")
            raise
    
    def _render_view(self, renderer: Render2D, view_type: str, scale: int) -> PILImage.Image:
        """根据视图类型选择渲染方法
        
        Args:
            renderer: 渲染器实例
            view_type: 视图类型
            scale: 缩放比例
            
        Returns:
            PILImage.Image: 渲染后的图像
        """
        view_type = view_type.lower()
        
        # 视图映射
        view_renderers: Dict[str, Callable] = {
            "top": renderer.render_top_view,
            "front": renderer.render_front_view,
            "north": renderer.render_front_view,
            "side": renderer.render_side_view,
            "east": renderer.render_side_view,
            "south": lambda scale=scale: renderer.render_front_view(z=0, scale=scale),
            "west": lambda scale=scale: renderer.render_side_view(x=0, scale=scale),
            "combined": renderer.render_all_views
        }
        
        # 默认使用综合视图
        render_func = view_renderers.get(view_type, renderer.render_all_views)
        
        # 调用渲染函数
        return render_func(scale=scale) 