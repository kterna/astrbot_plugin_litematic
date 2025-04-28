import os
import numpy as np
from PIL import Image
from typing import Optional, Dict, Any, List, Tuple, Union
import re

from .texture_manager import TextureManager
from .config_loader import ConfigLoader
from .projection import Projection
from .build_model import World
from .interfaces import RenderContext
from .render_pipeline import RenderPipeline
from .render_processors import (
    BoundsCalculatorProcessor, 
    TextureLoaderProcessor, 
    TopViewProcessor, 
    FrontViewProcessor, 
    SideViewProcessor, 
    ViewCombinerProcessor,
    ModelRendererProcessor
)
from .view_combiner import ViewCombiner, LayoutType

class RenderOptions:
    """渲染选项类，用于配置渲染参数"""
    
    def __init__(self) -> None:
        """初始化渲染选项"""
        self.scale: int = 1                              # 缩放比例
        self.layout_type: str = "custom_combined"        # 布局类型
        self.spacing: int = 0                            # 视图间距
        self.add_labels: bool = False                    # 是否添加标签
        self.grid_rows: int = 2                          # 网格布局行数
        self.grid_cols: int = 2                          # 网格布局列数
        self.stack_x_offset: int = 20                    # 堆叠布局X偏移
        self.stack_y_offset: int = 20                    # 堆叠布局Y偏移
        self.export_format: str = 'PNG'                  # 导出格式
        self.use_block_models: bool = True               # 是否使用方块模型
        self.custom_options: Dict[str, Any] = {}         # 自定义选项
    
    def as_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'scale': self.scale,
            'layout_type': self.layout_type,
            'spacing': self.spacing,
            'add_labels': self.add_labels,
            'grid_rows': self.grid_rows,
            'grid_cols': self.grid_cols,
            'stack_x_offset': self.stack_x_offset,
            'stack_y_offset': self.stack_y_offset,
            'export_format': self.export_format,
            'use_block_models': self.use_block_models,
            'custom_options': self.custom_options
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'RenderOptions':
        """从字典创建"""
        options = RenderOptions()
        for key, value in data.items():
            if hasattr(options, key):
                setattr(options, key, value)
            elif key == 'custom_options' and isinstance(value, dict):
                options.custom_options.update(value)
        return options

class RenderEngine:
    """渲染引擎，协调各组件完成Minecraft结构的渲染工作"""
    
    def __init__(self, world: World, resource_base_path: str = "./resource", 
                 texture_path: Optional[str] = None, texture_size: Optional[int] = None) -> None:
        """初始化渲染引擎
        
        Args:
            world: 世界对象
            resource_base_path: 资源基础路径
            texture_path: 纹理路径
            texture_size: 纹理大小
        """
        self.world: World = world
        self.resource_base_path: str = resource_base_path
        
        # 加载配置
        self.config_loader: ConfigLoader = ConfigLoader.get_instance(resource_base_path)
        
        # 初始化纹理管理器
        self.texture_manager: TextureManager = TextureManager(resource_base_path, texture_path, texture_size)
        
        # 向后兼容性组件
        self.projection: Projection = Projection(world)
        self._debug_counter: int = 0
        
        # 创建基础上下文
        self.base_context = RenderContext()
        self.base_context.set("world", world)
        self.base_context.set("texture_manager", self.texture_manager)
        
        # 创建视图组合器
        self.view_combiner = ViewCombiner()
        
        # 创建渲染管道
        self._create_pipelines()
        
        # 默认渲染选项
        self.default_options = RenderOptions()
    
    def _create_pipelines(self) -> None:
        """创建各种渲染管道"""
        # 创建基础处理器
        self.bounds_processor = BoundsCalculatorProcessor()
        self.texture_processor = TextureLoaderProcessor(
            self.resource_base_path, 
            None, 
            None
        )
        self.model_processor = ModelRendererProcessor()
        self.top_view_processor = TopViewProcessor()
        self.front_view_processor = FrontViewProcessor()
        self.side_view_processor = SideViewProcessor()
        self.combiner_processor = ViewCombinerProcessor()
        
        # 创建顶视图管道
        self.top_view_pipeline = RenderPipeline[Image.Image]()
        self.top_view_pipeline.add_processor(self.bounds_processor)
        self.top_view_pipeline.add_processor(self.texture_processor)
        self.top_view_pipeline.add_processor(self.model_processor)
        self.top_view_pipeline.add_processor(self.top_view_processor)
        
        # 创建正视图管道
        self.front_view_pipeline = RenderPipeline[Image.Image]()
        self.front_view_pipeline.add_processor(self.bounds_processor)
        self.front_view_pipeline.add_processor(self.texture_processor)
        self.front_view_pipeline.add_processor(self.model_processor)
        self.front_view_pipeline.add_processor(self.front_view_processor)
        
        # 创建侧视图管道
        self.side_view_pipeline = RenderPipeline[Image.Image]()
        self.side_view_pipeline.add_processor(self.bounds_processor)
        self.side_view_pipeline.add_processor(self.texture_processor)
        self.side_view_pipeline.add_processor(self.model_processor)
        self.side_view_pipeline.add_processor(self.side_view_processor)
        
        # 创建组合视图管道
        self.combined_view_pipeline = RenderPipeline[Image.Image]()
        self.combined_view_pipeline.add_processor(self.bounds_processor)
        self.combined_view_pipeline.add_processor(self.texture_processor)
        self.combined_view_pipeline.add_processor(self.model_processor)
        self.combined_view_pipeline.add_processor(self.top_view_processor)
        self.combined_view_pipeline.add_processor(self.front_view_processor)
        self.combined_view_pipeline.add_processor(self.side_view_processor)
        self.combined_view_pipeline.add_processor(self.combiner_processor)
    
    def render_top_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                        min_z: Optional[int] = None, max_z: Optional[int] = None, 
                        scale: int = 1) -> Image.Image:
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
        # 创建上下文
        context = RenderContext()
        context.set("world", self.world)
        context.set("scale", scale)
        context.set("resource_dir", self.resource_base_path)
        
        # 如果提供了坐标，设置到上下文
        if min_x is not None and max_x is not None and min_z is not None and max_z is not None:
            # 获取完整边界
            _, _, min_y, max_y, _, _ = self._get_structure_bounds()
            context.set("bounds", (min_x, max_x, min_y, max_y, min_z, max_z))
        
        # 执行管道
        return self.top_view_pipeline.execute(context)
    
    def render_front_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                          min_y: Optional[int] = None, max_y: Optional[int] = None, 
                          z: Optional[int] = None, scale: int = 1) -> Image.Image:
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
        # 创建上下文
        context = RenderContext()
        context.set("world", self.world)
        context.set("scale", scale)
        context.set("front_z", z)
        context.set("resource_dir", self.resource_base_path)
        
        # 如果提供了坐标，设置到上下文
        if min_x is not None and max_x is not None and min_y is not None and max_y is not None:
            # 获取完整边界
            _, _, _, _, min_z, max_z = self._get_structure_bounds()
            context.set("bounds", (min_x, max_x, min_y, max_y, min_z, max_z))
        
        # 执行管道
        return self.front_view_pipeline.execute(context)
    
    def render_side_view(self, min_z: Optional[int] = None, max_z: Optional[int] = None, 
                         min_y: Optional[int] = None, max_y: Optional[int] = None, 
                         x: Optional[int] = None, scale: int = 1) -> Image.Image:
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
        # 创建上下文
        context = RenderContext()
        context.set("world", self.world)
        context.set("scale", scale)
        context.set("side_x", x)
        context.set("resource_dir", self.resource_base_path)
        
        # 如果提供了坐标，设置到上下文
        if min_z is not None and max_z is not None and min_y is not None and max_y is not None:
            # 获取完整边界
            min_x, max_x, _, _, _, _ = self._get_structure_bounds()
            context.set("bounds", (min_x, max_x, min_y, max_y, min_z, max_z))
        
        # 执行管道
        return self.side_view_pipeline.execute(context)
    
    def render_all_views(self, scale: int = 1) -> Image.Image:
        """渲染所有视图并拼接
        
        Args:
            scale: 缩放比例
            
        Returns:
            Image.Image: 渲染后的图像
        """
        # 创建上下文
        context = RenderContext()
        context.set("world", self.world)
        context.set("scale", scale)
        context.set("resource_dir", self.resource_base_path)
        
        # 执行管道
        return self.combined_view_pipeline.execute(context)
    
    def render_with_layout(self, layout_type: str = "custom_combined", options: Optional[RenderOptions] = None) -> Image.Image:
        """使用指定布局渲染视图
        
        Args:
            layout_type: 布局类型，可选值见LayoutType枚举
            options: 渲染选项
            
        Returns:
            Image.Image: 渲染后的图像
        """
        # 使用默认选项或提供的选项
        if options is None:
            options = self.default_options
            options.layout_type = layout_type
        
        # 创建上下文
        context = RenderContext()
        context.set("world", self.world)
        context.set("scale", options.scale)
        context.set("render_options", options)
        context.set("resource_dir", self.resource_base_path)
        
        # 渲染各个视图
        top_view = self.render_top_view(
            scale=options.scale
        )
        front_view = self.render_front_view(
            scale=options.scale
        )
        side_view = self.render_side_view(
            scale=options.scale
        )
        
        # 使用简化后的视图组合器组合视图
        views = [top_view, front_view, side_view]
        
        # 使用新的combine_views方法
        return self.view_combiner.combine_views(
            views, 
            layout_type=layout_type, 
            spacing=options.spacing
        )
    
    def _get_structure_bounds(self) -> Tuple[int, int, int, int, int, int]:
        """获取结构边界坐标
        
        Returns:
            Tuple[int, int, int, int, int, int]: (min_x, max_x, min_y, max_y, min_z, max_z)
        """
        # 使用边界处理器计算
        context = RenderContext()
        context.set("world", self.world)
        return self.bounds_processor.process(context)
    
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
    
    def clear_cache(self) -> None:
        """清除材质缓存"""
        self.texture_manager.clear_cache() 