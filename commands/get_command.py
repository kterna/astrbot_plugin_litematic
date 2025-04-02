from typing import Optional, AsyncGenerator, Tuple
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import File
import os
from ..services.file_manager import FileManager

class GetCommand:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager: FileManager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: str = "", filename: str = "") -> AsyncGenerator[MessageChain, None]:
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
        
        # 获取文件
        file_path: Optional[str] = self.file_manager.get_litematic_file(category, filename)
        
        if not file_path:
            yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
            return
        
        # 发送文件
        try:
            # 发送提示信息
            yield event.plain_result("正在发送文件，请稍候...")
            
            # 构建消息链并发送文件
            file_name: str = os.path.basename(file_path)
            file_component: File = File(name=file_name, file=file_path)
            
            message: MessageChain = MessageChain()
            message.chain.append(file_component)
            
            await event.send(message)
            logger.info(f"已发送文件: {file_path}")
        except Exception as e:
            logger.error(f"发送文件失败: {e}")
            yield event.plain_result(f"发送文件失败: {e}") 