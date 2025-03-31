import numpy as np
from PIL import Image

class Projection:
    """投影处理器，负责从不同角度对Minecraft结构进行投影"""
    
    def __init__(self, world):
        self.world = world
    
    def get_top_view_blocks(self, min_x, max_x, min_z, max_z):
        """获取俯视图中可见的方块列表"""
        visible_blocks = []
        
        for x in range(min_x, max_x + 1):
            for z in range(min_z, max_z + 1):
                block = self.world.get_max_y_at(x, z)
                if block:
                    visible_blocks.append((x, z, block))
        
        return visible_blocks
    
    def get_front_view_blocks(self, min_x, max_x, min_y, max_y, z):
        """获取正视图中可见的方块列表"""
        visible_blocks = []
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                block = self.world.get_min_z_at(x, y)
                if block:
                    visible_blocks.append((x, y, block))
        
        return visible_blocks
    
    def get_side_view_blocks(self, min_z, max_z, min_y, max_y, x):
        """获取侧视图中可见的方块列表"""
        visible_blocks = []
        
        for z in range(min_z, max_z + 1):
            for y in range(min_y, max_y + 1):
                block = self.world.get_max_x_at(y, z)
                if block:
                    visible_blocks.append((z, y, block))
        
        return visible_blocks
    
    def render_top_view(self, texture_manager, min_x, max_x, min_z, max_z, scale=1):
        """渲染俯视图"""
        width = (max_x - min_x + 1) * texture_manager.texture_size
        height = (max_z - min_z + 1) * texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.get_top_view_blocks(min_x, max_x, min_z, max_z)
        
        for x, z, block in visible_blocks:
            pos_x = (x - min_x) * texture_manager.texture_size
            pos_z = (z - min_z) * texture_manager.texture_size
            
            face = block.get_texture_face('top')
            texture = texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_x, pos_z), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image
    
    def render_front_view(self, texture_manager, min_x, max_x, min_y, max_y, z, scale=1):
        """渲染正视图"""
        width = (max_x - min_x + 1) * texture_manager.texture_size
        height = (max_y - min_y + 1) * texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.get_front_view_blocks(min_x, max_x, min_y, max_y, z)
        
        for x, y, block in visible_blocks:
            pos_x = (x - min_x) * texture_manager.texture_size
            pos_y = (max_y - y) * texture_manager.texture_size
            
            face = block.get_texture_face('front')
            texture = texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_x, pos_y), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image
    
    def render_side_view(self, texture_manager, min_z, max_z, min_y, max_y, x, scale=1):
        """渲染侧视图"""
        width = (max_z - min_z + 1) * texture_manager.texture_size
        height = (max_y - min_y + 1) * texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.get_side_view_blocks(min_z, max_z, min_y, max_y, x)
        
        for z, y, block in visible_blocks:
            pos_z = (z - min_z) * texture_manager.texture_size
            pos_y = (max_y - y) * texture_manager.texture_size
            
            face = block.get_texture_face('side')
            texture = texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_z, pos_y), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image 