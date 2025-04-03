import numpy as np
from PIL import Image
from typing import Optional, Dict, Any, List, Union
import os
import re
import json

from .build_model import World, Block
from .render_engine import RenderEngine
from .interfaces import IRenderer, IImageSaver

class Render2D:
    """2D渲染器，用于从World对象中提取信息并渲染Minecraft结构的2D投影预览图像"""
    
    def __init__(self, world: World, resource_base_path: str = "./resource", 
                 texture_path: Optional[str] = None, texture_size: Optional[int] = None) -> None:
        """初始化2D渲染器"""
        self.world: World = world
        self.resource_base_path: str = resource_base_path
        
        # 初始化渲染引擎
        self.engine: RenderEngine = RenderEngine(
            world=world,
            resource_base_path=resource_base_path,
            texture_path=texture_path,
            texture_size=texture_size,
        )
        
        # 保存其他属性，保持向后兼容性
        self.texture_path: str = self.engine.texture_manager.texture_path
        self.texture_size: int = self.engine.texture_manager.texture_size
        self.texture_paths: Dict[str, str] = self.engine.texture_manager.texture_paths
        self.texture_cache: Dict[str, Image.Image] = self.engine.texture_manager.texture_cache
        self.default_texture: Image.Image = self.engine.texture_manager.default_texture
        self.available_textures: List[str] = self.engine.texture_manager.available_textures
        
    def render_top_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                        min_z: Optional[int] = None, max_z: Optional[int] = None, 
                        scale: int = 1) -> Image.Image:
        """渲染俯视图（从上向下看）"""
        return self.engine.render_top_view(min_x, max_x, min_z, max_z, scale)
    
    def render_front_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                          min_y: Optional[int] = None, max_y: Optional[int] = None, 
                          z: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染正视图（从前向后看）"""
        return self.engine.render_front_view(min_x, max_x, min_y, max_y, z, scale)
    
    def render_side_view(self, min_z: Optional[int] = None, max_z: Optional[int] = None, 
                         min_y: Optional[int] = None, max_y: Optional[int] = None, 
                         x: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染侧视图（从侧面看）"""
        return self.engine.render_side_view(min_z, max_z, min_y, max_y, x, scale)
    
    def render_all_views(self, scale: int = 1) -> Image.Image:
        """渲染所有视图（俯视图、正视图、侧视图）并拼接成一个图像"""
        return self.engine.render_all_views(scale)
    
    def save_image(self, image: Image.Image, output_path: str, format: str = 'PNG') -> bool:
        """保存图像到文件"""
        return self.engine.save_image(image, output_path, format)
    
    def get_texture(self, block_name: str, face: str = "side") -> Optional[Image.Image]:
        """获取指定方块和面的材质"""
        return self.engine.texture_manager.get_texture(block_name, face)
    
    def clear_cache(self) -> None:
        """清除材质缓存"""
        self.engine.clear_cache()
        # 更新本地引用
        self.texture_cache = self.engine.texture_manager.texture_cache
