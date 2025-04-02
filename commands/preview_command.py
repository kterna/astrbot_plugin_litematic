import os
import traceback
import asyncio
from typing import Dict, List, Optional
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image
from ..services.file_manager import FileManager
from ..services.render_manager import RenderManager, LAYOUT_MAPPING
from ..utils.types import CategoryType, FilePath, MessageResponse
from ..utils.exceptions import (
    CategoryNotFoundError, 
    FileNotFoundError, 
    LitematicPluginError,
    RenderError,
    InvalidViewTypeError
)

class PreviewCommand:
    def __init__(self, file_manager: FileManager, render_manager: RenderManager) -> None:
        self.file_manager: FileManager = file_manager
        self.render_manager: RenderManager = render_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "", 
                     view_type: str = "combined", layout: str = "", spacing: int = 0, add_labels: bool = False) -> MessageResponse:
        """
        渲染并预览litematic文件
        
        Args:
            event: 消息事件
            category: 分类名称
            filename: 文件名
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            layout: 布局类型，支持vertical/horizontal/grid/stacked/combined
            spacing: 视图间距
            add_labels: 是否添加标签
            
        Yields:
            MessageChain: 响应消息
        """
        # 解析布局相关参数
        parts = view_type.split(":")
        if len(parts) > 1:
            view_type = parts[0]
            # 解析附加参数
            for part in parts[1:]:
                if part in LAYOUT_MAPPING:
                    layout = part
                elif part.startswith("spacing="):
                    try:
                        spacing = int(part.split("=")[1])
                    except ValueError:
                        pass
                elif part == "labels":
                    add_labels = True
        
        # 验证参数
        if not category or not filename:
            yield event.plain_result(self._get_help_text())
            return
        
        try:
            # 发送加载提示
            yield event.plain_result("正在生成预览图，请稍候...")
            
            # 获取文件路径 - 使用异步方法
            file_path: FilePath = await self.file_manager.get_litematic_file_async(category, filename)
            
            # 渲染litematic文件 - 使用异步方法
            image_path: FilePath = await self.render_manager.render_litematic_async(
                file_path, 
                view_type, 
                scale=1, 
                layout=layout,
                spacing=spacing,
                add_labels=add_labels
            )
            
            # 准备消息链
            message: MessageChain = MessageChain()
            message.chain.append(Image.fromFileSystem(image_path))
            
            # 发送图像
            await event.send(message)
            
            # 获取视图说明
            caption = self._get_view_caption(view_type)
            layout_caption = self._get_layout_caption(layout) if layout else ""
            caption_text = f"【{os.path.basename(file_path)}】{caption}"
            if layout_caption:
                caption_text += f" - {layout_caption}"
            
            # 发送说明文本
            yield event.plain_result(caption_text)
            
            # 删除临时图像文件 - 使用异步删除
            if os.path.exists(image_path):
                await asyncio.to_thread(os.remove, image_path)
                
        except FileNotFoundError as e:
            yield event.plain_result(e.message)
        except CategoryNotFoundError as e:
            yield event.plain_result(e.message)
        except InvalidViewTypeError as e:
            yield event.plain_result(e.message)
        except RenderError as e:
            logger.error(f"渲染失败: {e.message} (错误代码: {e.code})")
            yield event.plain_result(f"生成预览图失败: {e.message}")
        except LitematicPluginError as e:
            logger.error(f"渲染失败: {e.message} (错误代码: {e.code})")
            yield event.plain_result(f"生成预览图失败: {e.message}")
        except Exception as e:
            logger.error(f"生成预览图时出现未知错误: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"生成预览图时出现错误: {str(e)}")
    
    def _get_view_caption(self, view_type: str) -> str:
        """
        获取视图类型对应的说明文字
        
        Args:
            view_type: 视图类型
            
        Returns:
            str: 说明文字
        """
        view_type = view_type.lower()
        captions: Dict[str, str] = {
            "top": "俯视图 (从上向下看)",
            "front": "正视图 (北面)",
            "north": "正视图 (北面)",
            "side": "侧视图 (东面)",
            "east": "侧视图 (东面)",
            "south": "南面视图",
            "west": "西面视图",
            "combined": "综合视图 (俯视图 + 正视图 + 侧视图)"
        }
        return captions.get(view_type, "综合视图")
    
    def _get_layout_caption(self, layout: str) -> str:
        """
        获取布局类型对应的说明文字
        
        Args:
            layout: 布局类型
            
        Returns:
            str: 说明文字
        """
        layout = layout.lower()
        captions: Dict[str, str] = {
            "vertical": "垂直布局",
            "v": "垂直布局",
            "horizontal": "水平布局",
            "h": "水平布局",
            "grid": "网格布局",
            "g": "网格布局",
            "stacked": "堆叠布局",
            "s": "堆叠布局",
            "combined": "综合布局",
            "c": "综合布局"
        }
        return captions.get(layout, "")
    
    def _get_help_text(self) -> str:
        """
        获取帮助文本
        
        Returns:
            str: 帮助文本
        """
        return (
            "投影预览命令使用方法：\n"
            "/投影预览 分类 文件名 [视角][:布局][:参数]\n\n"
            "支持的视角：\n"
            "- top: 俯视图\n"
            "- front/north: 正视图(北面)\n"
            "- side/east: 侧视图(东面)\n"
            "- south: 南面视图\n"
            "- west: 西面视图\n"
            "- combined: 综合视图(默认)\n\n"
            "支持的布局：\n"
            "- vertical/v: 垂直布局\n"
            "- horizontal/h: 水平布局\n"
            "- grid/g: 网格布局\n"
            "- stacked/s: 堆叠布局\n"
            "- combined/c: 综合布局(默认)\n\n"
            "可选参数：\n"
            "- spacing=数字: 设置间距\n"
            "- labels: 添加标签\n\n"
            "例如：/投影预览 建筑 房子 combined:v:spacing=10:labels"
        ) 