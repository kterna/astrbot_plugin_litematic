import os
from typing import Optional, Dict, Any, Union, Tuple
from PIL import Image

from .render_engine import RenderEngine, RenderOptions
from .build_model import World
from .texture_manager import TextureManager
from ...utils.types import FilePath, ViewType, LayoutType

class RenderFacade:
    """
    渲染门面类 - 提供一个简单统一的API来访问复杂的渲染功能
    
    这个类隐藏了内部渲染逻辑的复杂性，为使用者提供简单清晰的API
    """
    
    def __init__(self, resource_dir: str) -> None:
        """
        初始化渲染门面
        
        Args:
            resource_dir: 资源目录路径
        """
        self.resource_dir = resource_dir
        self.texture_manager = None
        self._current_world = None
        self._current_engine = None
    
    def load_litematic(self, file_path: str) -> bool:
        """
        加载Litematic文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            from litemapy import Schematic
            schem = Schematic.load(file_path)
            
            # 创建世界模型
            world = World()
            world.add_blocks(schem)
            
            # 保存当前世界和创建渲染引擎
            self._current_world = world
            self._current_engine = RenderEngine(
                world=world,
                resource_base_path=self.resource_dir
            )
            
            return True
        except Exception:
            return False
    
    def render(self, view_type: str = "combined", 
               scale: int = 1, 
               layout: str = "",
               spacing: int = 0,
               add_labels: bool = False,
               use_block_models: bool = True) -> Optional[Image.Image]:
        """
        渲染当前加载的Litematic文件
        
        Args:
            view_type: 视图类型 (top/front/side/north/south/east/west/combined)
            scale: 缩放比例
            layout: 布局类型 (vertical/horizontal/grid/stacked)
            spacing: 视图间距
            add_labels: 是否添加标签
            use_block_models: 是否使用方块模型
            
        Returns:
            Optional[Image.Image]: 渲染后的图像，失败返回None
        """
        if not self._current_engine or not self._current_world:
            return None
            
        try:
            # 创建渲染选项
            options = RenderOptions()
            options.scale = scale
            options.spacing = spacing
            options.add_labels = add_labels
            options.use_block_models = use_block_models
            
            # 确定视图类型
            view_type = view_type.lower()
            
            # 单视图渲染
            if view_type in ["top", "front", "north", "side", "east", "south", "west"]:
                if view_type == "top":
                    return self._current_engine.render_top_view(
                        scale=scale, 
                        use_block_models=use_block_models
                    )
                elif view_type in ["front", "north"]:
                    return self._current_engine.render_front_view(
                        scale=scale, 
                        use_block_models=use_block_models
                    )
                elif view_type in ["side", "east"]:
                    return self._current_engine.render_side_view(
                        scale=scale, 
                        use_block_models=use_block_models
                    )
                elif view_type == "south":
                    return self._current_engine.render_front_view(
                        z=0, 
                        scale=scale, 
                        use_block_models=use_block_models
                    )
                elif view_type == "west":
                    return self._current_engine.render_side_view(
                        x=0, 
                        scale=scale, 
                        use_block_models=use_block_models
                    )
            
            # 组合视图渲染
            layout_type = self._map_layout_type(layout)
            if layout_type:
                options.layout_type = layout_type
                return self._current_engine.render_with_layout(layout_type, options)
            else:
                return self._current_engine.render_all_views(
                    scale=scale, 
                    use_block_models=use_block_models
                )
                
        except Exception:
            return None
    
    def save_image(self, image: Image.Image, output_path: str, format: str = 'PNG') -> bool:
        """
        保存图像到文件
        
        Args:
            image: 图像对象
            output_path: 输出路径
            format: 图像格式
            
        Returns:
            bool: 是否成功保存
        """
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            image.save(output_path, format=format)
            return True
        except Exception:
            return False
    
    def render_to_file(self, output_path: str, view_type: str = "combined", 
                      scale: int = 1, layout: str = "", 
                      spacing: int = 0, add_labels: bool = False,
                      use_block_models: bool = True) -> bool:
        """
        渲染并直接保存到文件
        
        Args:
            output_path: 输出文件路径
            view_type: 视图类型
            scale: 缩放比例
            layout: 布局类型
            spacing: 视图间距
            add_labels: 是否添加标签
            use_block_models: 是否使用方块模型
            
        Returns:
            bool: 是否成功
        """
        image = self.render(
            view_type, 
            scale, 
            layout, 
            spacing, 
            add_labels, 
            use_block_models
        )
        if image:
            return self.save_image(image, output_path)
        return False
    
    def get_bounds(self) -> Tuple[int, int, int, int, int, int]:
        """
        获取当前结构的边界
        
        Returns:
            Tuple[int, int, int, int, int, int]: (min_x, max_x, min_y, max_y, min_z, max_z)
        """
        if not self._current_engine:
            return (0, 0, 0, 0, 0, 0)
        return self._current_engine._get_structure_bounds()
    
    def _map_layout_type(self, layout: str) -> str:
        """
        映射布局类型
        
        Args:
            layout: 布局类型字符串
            
        Returns:
            str: 内部布局类型
        """
        mapping = {
            "vertical": "vertical",
            "horizontal": "horizontal",
            "grid": "grid",
            "stacked": "stacked",
            "combined": "custom_combined",
            "default": "custom_combined",
            "v": "vertical",
            "h": "horizontal",
            "g": "grid",
            "s": "stacked",
            "c": "custom_combined"
        }
        return mapping.get(layout.lower(), "") 