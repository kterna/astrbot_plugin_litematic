from typing import Optional, List, Tuple, Dict, Any
from PIL import Image
import os

from .interfaces import IRenderer, IImageSaver, BoundsType
from .texture_manager import TextureManager
from .build_model import World, Block
from .projection import Projection

class TopViewRenderer:
    """顶视图渲染器，专门负责渲染俯视图"""
    
    def __init__(self, projection: Projection, texture_manager: TextureManager):
        """初始化顶视图渲染器
        
        Args:
            projection: 投影处理器
            texture_manager: 材质管理器
        """
        self.projection = projection
        self.texture_manager = texture_manager
    
    def render(self, min_x: int, max_x: int, min_z: int, max_z: int, scale: int = 1) -> Image.Image:
        """渲染俯视图
        
        Args:
            min_x: X轴最小坐标
            max_x: X轴最大坐标
            min_z: Z轴最小坐标
            max_z: Z轴最大坐标
            scale: 缩放比例
        
        Returns:
            Image.Image: 渲染后的图像
        """
        width = (max_x - min_x + 1) * self.texture_manager.texture_size
        height = (max_z - min_z + 1) * self.texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.projection.get_top_view_blocks(min_x, max_x, min_z, max_z)
        
        for x, z, block in visible_blocks:
            pos_x = (x - min_x) * self.texture_manager.texture_size
            pos_z = (z - min_z) * self.texture_manager.texture_size
            
            face = block.get_texture_face('top')
            texture = self.texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_x, pos_z), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class FrontViewRenderer:
    """正视图渲染器，专门负责渲染正视图"""
    
    def __init__(self, projection: Projection, texture_manager: TextureManager):
        """初始化正视图渲染器
        
        Args:
            projection: 投影处理器
            texture_manager: 材质管理器
        """
        self.projection = projection
        self.texture_manager = texture_manager
    
    def render(self, min_x: int, max_x: int, min_y: int, max_y: int, z: int, scale: int = 1) -> Image.Image:
        """渲染正视图
        
        Args:
            min_x: X轴最小坐标
            max_x: X轴最大坐标
            min_y: Y轴最小坐标
            max_y: Y轴最大坐标
            z: Z轴位置
            scale: 缩放比例
        
        Returns:
            Image.Image: 渲染后的图像
        """
        width = (max_x - min_x + 1) * self.texture_manager.texture_size
        height = (max_y - min_y + 1) * self.texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.projection.get_front_view_blocks(min_x, max_x, min_y, max_y, z)
        
        for x, y, block in visible_blocks:
            pos_x = (x - min_x) * self.texture_manager.texture_size
            pos_y = (max_y - y) * self.texture_manager.texture_size
            
            face = block.get_texture_face('front')
            texture = self.texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_x, pos_y), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class SideViewRenderer:
    """侧视图渲染器，专门负责渲染侧视图"""
    
    def __init__(self, projection: Projection, texture_manager: TextureManager):
        """初始化侧视图渲染器
        
        Args:
            projection: 投影处理器
            texture_manager: 材质管理器
        """
        self.projection = projection
        self.texture_manager = texture_manager
    
    def render(self, min_z: int, max_z: int, min_y: int, max_y: int, x: int, scale: int = 1) -> Image.Image:
        """渲染侧视图
        
        Args:
            min_z: Z轴最小坐标
            max_z: Z轴最大坐标
            min_y: Y轴最小坐标
            max_y: Y轴最大坐标
            x: X轴位置
            scale: 缩放比例
        
        Returns:
            Image.Image: 渲染后的图像
        """
        width = (max_z - min_z + 1) * self.texture_manager.texture_size
        height = (max_y - min_y + 1) * self.texture_manager.texture_size
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        visible_blocks = self.projection.get_side_view_blocks(min_z, max_z, min_y, max_y, x)
        
        for z, y, block in visible_blocks:
            pos_z = (z - min_z) * self.texture_manager.texture_size
            pos_y = (max_y - y) * self.texture_manager.texture_size
            
            face = block.get_texture_face('side')
            texture = self.texture_manager.get_texture(block.name, face)
            
            image.paste(texture, (pos_z, pos_y), texture)
        
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class ImageSaver(IImageSaver):
    """图像保存器，专门负责保存图像到文件"""
    
    def save_image(self, image: Image.Image, output_path: str, format: str = 'PNG') -> bool:
        """保存图像到文件
        
        Args:
            image: 图像对象
            output_path: 输出路径
            format: 图像格式，默认为PNG
        
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            image.save(output_path, format=format)
            return True
        except Exception:
            return False


class StructureRenderer(IRenderer):
    """结构渲染器，实现IRenderer接口，协调各个专门的渲染器"""
    
    def __init__(self, world: World, texture_manager: TextureManager):
        """初始化结构渲染器
        
        Args:
            world: 世界对象
            texture_manager: 材质管理器
        """
        self.world = world
        self.texture_manager = texture_manager
        self.projection = Projection(world)
        
        # 创建专门的渲染器
        self.top_renderer = TopViewRenderer(self.projection, texture_manager)
        self.front_renderer = FrontViewRenderer(self.projection, texture_manager)
        self.side_renderer = SideViewRenderer(self.projection, texture_manager)
        self.image_saver = ImageSaver()
    
    def render_top_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                      min_z: Optional[int] = None, max_z: Optional[int] = None, 
                      scale: int = 1) -> Image.Image:
        """渲染俯视图（从上向下看）"""
        if min_x is None or max_x is None or min_z is None or max_z is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self.get_structure_bounds()
        
        return self.top_renderer.render(min_x, max_x, min_z, max_z, scale)
    
    def render_front_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                         min_y: Optional[int] = None, max_y: Optional[int] = None, 
                         z: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染正视图（从前向后看）"""
        if min_x is None or max_x is None or min_y is None or max_y is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self.get_structure_bounds()
        
        if z is None:
            z = min_z
        
        return self.front_renderer.render(min_x, max_x, min_y, max_y, z, scale)
    
    def render_side_view(self, min_z: Optional[int] = None, max_z: Optional[int] = None, 
                        min_y: Optional[int] = None, max_y: Optional[int] = None, 
                        x: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染侧视图（从侧面看）"""
        if min_z is None or max_z is None or min_y is None or max_y is None:
            min_x, max_x, min_y, max_y, min_z, max_z = self.get_structure_bounds()
        
        if x is None:
            x = max_x
        
        return self.side_renderer.render(min_z, max_z, min_y, max_y, x, scale)
    
    def render_all_views(self, scale: int = 1) -> Image.Image:
        """渲染所有视图（俯视图、正视图、侧视图）并拼接成一个图像"""
        min_x, max_x, min_y, max_y, min_z, max_z = self.get_structure_bounds()
        
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
    
    def get_structure_bounds(self) -> BoundsType:
        """获取结构的边界坐标"""
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
    
    def save_image(self, image: Image.Image, output_path: str, format: str = 'PNG') -> bool:
        """保存图像到文件"""
        return self.image_saver.save_image(image, output_path, format) 