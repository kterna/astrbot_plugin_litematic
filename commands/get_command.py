from typing import Optional, Tuple
import os
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import File
from ..services.file_manager import FileManager
from ..utils.types import CategoryType, FilePath, MessageResponse
from ..utils.exceptions import FileNotFoundError, LitematicPluginError, CategoryNotFoundError
from ..utils.logging_utils import log_error, log_operation

class GetCommand:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager: FileManager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "") -> MessageResponse:
        """
        获取litematic文件
        使用方法：
        /投影获取 分类名 文件名 - 发送指定分类下的文件
        
        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影获取 建筑 house.litematic")
            return
        
        try:
            # 获取文件 - 使用异步方法
            file_path: FilePath = await self.file_manager.get_litematic_file_async(category, filename)
            
            # 发送提示信息
            yield event.plain_result("正在发送文件，请稍候...")
            
            # 构建消息链并发送文件
            file_name: str = os.path.basename(file_path)
            file_component: File = File(name=file_name, file=file_path)
            
            message: MessageChain = MessageChain()
            message.chain.append(file_component)
            
            await event.send(message)
            log_operation("发送文件", True, {"category": category, "filename": file_name, "path": file_path})
        except FileNotFoundError as e:
            log_error(e)
            yield event.plain_result(e.message)
        except CategoryNotFoundError as e:
            log_error(e)
            yield event.plain_result(e.message)
        except LitematicPluginError as e:
            log_error(e, extra_info={"category": category, "filename": filename})
            yield event.plain_result(f"获取文件失败: {e.message}")
        except Exception as e:
            log_error(e, extra_info={"category": category, "filename": filename, "operation": "发送文件"})
            yield event.plain_result(f"发送文件时出现错误: {str(e)}") 