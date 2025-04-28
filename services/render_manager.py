import os
import tempfile
import asyncio
from typing import Callable, Dict, Optional, Union, Any
from PIL import Image as PILImage
from astrbot import logger
from ..core.image_render.render_facade import RenderFacade
from litemapy import Schematic
from ..utils.config import Config
from ..utils.exceptions import InvalidViewTypeError, RenderError
from ..utils.types import ViewType, LayoutType

# 布局类型映射，将命令参数映射到内部布局类型
LAYOUT_MAPPING = {
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

class RenderManager:
    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.resource_dir: str = config.get_resource_dir()
        # 创建RenderFacade实例
        self.render_facade: RenderFacade = RenderFacade(resource_dir=self.resource_dir)
    
    def render_litematic(self, file_path: str, view_type: str = "combined", scale: int = 1, 
                         layout: str = "", spacing: int = 0) -> str:
        """
        渲染litematic文件
        
        Args:
            file_path: litematic文件路径
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            scale: 缩放比例
            layout: 布局类型，支持vertical/horizontal/grid/stacked/combined
            spacing: 视图间距
            
        Returns:
            str: 临时图像文件路径
            
        Raises:
            InvalidViewTypeError: 视图类型不支持时
            RenderError: 渲染过程出错时
        """
        return self._sync_render_litematic(
            file_path, view_type, scale, layout, spacing
        )
    
    async def render_litematic_async(self, file_path: str, view_type: str = "combined", scale: int = 1,
                                   layout: str = "", spacing: int = 0) -> str:
        """
        异步渲染litematic文件
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            file_path: litematic文件路径
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            scale: 缩放比例
            layout: 布局类型，支持vertical/horizontal/grid/stacked/combined
            spacing: 视图间距
            
        Returns:
            str: 临时图像文件路径
            
        Raises:
            InvalidViewTypeError: 视图类型不支持时
            RenderError: 渲染过程出错时
        """
        return await asyncio.to_thread(
            self._sync_render_litematic, file_path, view_type, scale, layout, spacing
        )
    
    def _sync_render_litematic(self, file_path: str, view_type: str = "combined", scale: int = 1,
                             layout: str = "", spacing: int = 0) -> str:
        """
        同步渲染litematic文件（内部方法）
        
        Args:
            file_path: litematic文件路径
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            scale: 缩放比例
            layout: 布局类型，支持vertical/horizontal/grid/stacked/combined
            spacing: 视图间距
            
        Returns:
            str: 临时图像文件路径
            
        Raises:
            InvalidViewTypeError: 视图类型不支持时
            RenderError: 渲染过程出错时
        """
        try:
            # 检查视图类型
            view_type = view_type.lower()
            if view_type not in ["top", "front", "north", "side", "east", "south", "west", "combined"]:
                raise InvalidViewTypeError(f"不支持的视图类型: {view_type}")
            
            # 使用RenderFacade加载并渲染
            if not self.render_facade.load_litematic(file_path):
                raise RenderError("无法加载litematic文件", code=1001)
            
            # 为新的接口准备选项
            options = {
                "spacing": spacing
            }
            
            # 渲染图像
            image = self.render_facade.render(
                view_type=view_type,
                scale=scale,
                layout=layout,
                options=options
            )
            
            if image is None:
                raise RenderError("渲染图像失败", code=1002)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_file = tmp.name
            
            # 保存图像
            if not self.render_facade.save_image(image, temp_file):
                raise RenderError("保存图像失败", code=1003)
            
            return temp_file
            
        except InvalidViewTypeError:
            raise
        except RenderError:
            raise
        except Exception as e:
            logger.error(f"渲染litematic文件失败: {e}")
            raise RenderError(f"渲染失败: {str(e)}", code=1000) 