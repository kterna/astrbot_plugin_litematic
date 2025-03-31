import os
import numpy as np
from PIL import Image
import re

from .texture_manager import TextureManager
from .config_loader import ConfigLoader
from .projection import Projection
from .build_model import World
from .render_special_blocks2D import SpecialBlockRenderer

class RenderEngine:
    """渲染引擎，协调各组件完成Minecraft结构的渲染工作"""
    
    def __init__(self, world: World, resource_base_path: str = "./resource", 
                 texture_path: str = None, texture_size=None, 
                 special_blocks_config="./core/image_render/Special_blocks.json"):
        self.world = world
        self.resource_base_path = resource_base_path
        
        self.config_loader = ConfigLoader.get_instance(resource_base_path)
        self.special_blocks_config = self.config_loader.load_special_blocks_config(special_blocks_config)
        self.texture_manager = TextureManager(resource_base_path, texture_path, texture_size)
        self.projection = Projection(world)
        self.special_renderer = SpecialBlockRenderer()
        self._debug_counter = 0
    
    def render_top_view(self, min_x=None, max_x=None, min_z=None, max_z=None, scale=1):
        """渲染俯视图"""
        if min_x is None or max_x is None or min_z is None or max_z is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self._get_structure_bounds()
        
        return self.projection.render_top_view(self.texture_manager, min_x, max_x, min_z, max_z, scale)
    
    def render_front_view(self, min_x=None, max_x=None, min_y=None, max_y=None, z=None, scale=1):
        """渲染正视图"""
        if min_x is None or max_x is None or min_y is None or max_y is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self._get_structure_bounds()
        
        if z is None:
            z = min_z
        
        return self.projection.render_front_view(self.texture_manager, min_x, max_x, min_y, max_y, z, scale)
    
    def render_side_view(self, min_z=None, max_z=None, min_y=None, max_y=None, x=None, scale=1):
        """渲染侧视图"""
        if min_z is None or max_z is None or min_y is None or max_y is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self._get_structure_bounds()
        
        if x is None:
            x = max_x
        
        return self.projection.render_side_view(self.texture_manager, min_z, max_z, min_y, max_y, x, scale)
    
    def render_all_views(self, scale=1):
        """渲染所有视图并拼接"""
        min_x, max_x, min_y, max_y, min_z, max_z = self._get_structure_bounds()
        
        top_view = self.render_top_view(min_x, max_x, min_z, max_z, scale)
        front_view = self.render_front_view(min_x, max_x, min_y, max_y, min_z, scale)
        side_view = self.render_side_view(min_z, max_z, min_y, max_y, max_x, scale)
        
        max_width = max(top_view.width, front_view.width + side_view.width)
        height = top_view.height + max(front_view.height, side_view.height)
        
        combined = Image.new('RGBA', (max_width, height), (0, 0, 0, 0))
        
        combined.paste(top_view, (0, 0), top_view)
        combined.paste(front_view, (0, top_view.height), front_view)
        combined.paste(side_view, (front_view.width, top_view.height), side_view)
        
        return combined
    
    def _get_structure_bounds(self):
        """计算结构的边界坐标"""
        if not self.world.blocks:
            return (0, 0, 0, 0, 0, 0)
        
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        for block in self.world.blocks:
            x, y, z = block.position
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            min_z = min(min_z, z)
            max_z = max(max_z, z)
        
        return (int(min_x), int(max_x), int(min_y), int(max_y), int(min_z), int(max_z))
    
    def process_special_block(self, block_name, texture_name, face, source_texture):
        """处理特殊方块的材质变换"""
        if texture_name.startswith("transformed:"):
            parts = texture_name.split(":")
            if len(parts) >= 3:
                transform_source = parts[1]
                transform_face = parts[2] if len(parts) > 2 else None
                
                transform_key = f"{transform_source}:{transform_face}"
                if 'texture_transforms' in self.special_blocks_config:
                    transform_config = self.special_blocks_config['texture_transforms'].get(transform_key)
                    
                    if transform_config:
                        method_name = transform_config.get('method')
                        if method_name:
                            transform_method = self.special_renderer.get_transform_method(method_name)
                            if transform_method:
                                return transform_method(source_texture)
        
        return source_texture
    
    def save_image(self, image, output_path, format='PNG'):
        """保存图像到文件"""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            image.save(output_path, format=format)
            return True
        except Exception:
            return False
    
    def clear_cache(self):
        """清除材质缓存"""
        self.texture_manager.clear_cache() 