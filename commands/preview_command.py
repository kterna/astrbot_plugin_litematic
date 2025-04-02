import os
import traceback
import asyncio
from typing import Dict, List, Optional
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image
from ..services.file_manager import FileManager
from ..services.render_manager import RenderManager
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
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "", view_type: str = "combined") -> MessageResponse:
        """
        渲染并预览litematic文件
        
        Args:
            event: 消息事件
            category: 分类名称
            filename: 文件名
            view_type: 视图类型，支持top/front/side/north/south/east/west/combined
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影预览 建筑 house.litematic [视角]")
            return
        
        try:
            # 发送加载提示
            yield event.plain_result("正在生成预览图，请稍候...")
            
            # 获取文件路径 - 使用异步方法
            file_path: FilePath = await self.file_manager.get_litematic_file_async(category, filename)
            
            # 渲染litematic文件 - 使用异步方法
            image_path: FilePath = await self.render_manager.render_litematic_async(file_path, view_type)
            
            # 准备消息链
            message: MessageChain = MessageChain()
            message.chain.append(Image.fromFileSystem(image_path))
            
            # 发送图像
            await event.send(message)
            
            # 发送说明文本
            yield event.plain_result(f"【{os.path.basename(file_path)}】{self._get_view_caption(view_type)}")
            
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