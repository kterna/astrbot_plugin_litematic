import numpy as np
from PIL import Image
import os
import re
import json

from .build_model import World, Block
from .render_engine import RenderEngine

class Render2D:
    """2D渲染器，用于从World对象中提取信息并渲染Minecraft结构的2D投影预览图像"""
    
    def __init__(self, world: World, resource_base_path: str = "./resource", 
                 texture_path: str = None, texture_size=None, 
                 special_blocks_config="./core/image_render/Special_blocks.json"):
        """初始化2D渲染器"""
        self.world = world
        self.resource_base_path = resource_base_path
        
        # 初始化渲染引擎
        self.engine = RenderEngine(
            world=world,
            resource_base_path=resource_base_path,
            texture_path=texture_path,
            texture_size=texture_size,
            special_blocks_config=special_blocks_config
        )
        
        # 保存其他属性，保持向后兼容性
        self.texture_path = self.engine.texture_manager.texture_path
        self.texture_size = self.engine.texture_manager.texture_size
        self.texture_paths = self.engine.texture_manager.texture_paths
        self.texture_cache = self.engine.texture_manager.texture_cache
        self.default_texture = self.engine.texture_manager.default_texture
        self.available_textures = self.engine.texture_manager.available_textures
        self.special_blocks_config = self.engine.special_blocks_config
        
    def render_top_view(self, min_x=None, max_x=None, min_z=None, max_z=None, scale=1):
        """渲染俯视图（从上向下看）"""
        return self.engine.render_top_view(min_x, max_x, min_z, max_z, scale)
    
    def render_front_view(self, min_x=None, max_x=None, min_y=None, max_y=None, z=None, scale=1):
        """渲染正视图（从前向后看）"""
        return self.engine.render_front_view(min_x, max_x, min_y, max_y, z, scale)
    
    def render_side_view(self, min_z=None, max_z=None, min_y=None, max_y=None, x=None, scale=1):
        """渲染侧视图（从侧面看）"""
        return self.engine.render_side_view(min_z, max_z, min_y, max_y, x, scale)
    
    def render_all_views(self, scale=1):
        """渲染所有视图（俯视图、正视图、侧视图）并拼接成一个图像"""
        return self.engine.render_all_views(scale)
    
    def save_image(self, image, output_path, format='PNG'):
        """保存图像到文件"""
        return self.engine.save_image(image, output_path, format)
    
    def get_texture(self, block_name, face="side"):
        """获取指定方块和面的材质"""
        return self.engine.texture_manager.get_texture(block_name, face)
    
    def clear_cache(self):
        """清除材质缓存"""
        self.engine.clear_cache()
        # 更新本地引用
        self.texture_cache = self.engine.texture_manager.texture_cache
