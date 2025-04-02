import os
import traceback
from typing import Dict, List, Optional
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image
from ..services.file_manager import FileManager
from ..services.render_manager import RenderManager
from ..utils.types import CategoryType, FilePath, MessageResponse

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
        
        # 获取文件路径
        file_path: Optional[FilePath] = self._get_litematic_file(category, filename)
        if not file_path:
            yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}，请检查文件名")
            return
        
        try:
            # 发送加载提示
            yield event.plain_result("正在生成预览图，请稍候...")
            
            # 渲染litematic文件
            image_path: FilePath = self.render_manager.render_litematic(file_path, view_type)
            
            # 准备消息链
            message: MessageChain = MessageChain()
            message.chain.append(Image.fromFileSystem(image_path))
            
            # 发送图像
            await event.send(message)
            
            # 发送说明文本
            yield event.plain_result(f"【{os.path.basename(file_path)}】{self._get_view_caption(view_type)}")
            
            # 删除临时图像文件
            if os.path.exists(image_path):
                os.remove(image_path)
                
        except Exception as e:
            logger.error(f"生成预览图像失败: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"生成预览图像失败: {e}")
    
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
    
    def _get_litematic_file(self, category: CategoryType, filename: str) -> Optional[FilePath]:
        """
        获取litematic文件路径，支持模糊匹配
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            Optional[FilePath]: 文件路径，找不到则返回None
        """
        try:
            # 若文件管理器实现了get_litematic_file方法，则使用
            if hasattr(self.file_manager, 'get_litematic_file'):
                return self.file_manager.get_litematic_file(category, filename)
            
            # 否则，自行实现简单版本
            litematic_dir: FilePath = self.file_manager.get_litematic_dir()
            category_dir: FilePath = os.path.join(litematic_dir, category)
            
            if not os.path.exists(category_dir):
                return None
                
            # 精确匹配
            file_path: FilePath = os.path.join(category_dir, filename)
            if os.path.exists(file_path):
                return file_path
                
            # 模糊匹配
            matches: List[str] = [f for f in os.listdir(category_dir) 
                      if f.endswith('.litematic') and filename.lower() in f.lower()]
            
            if matches:
                return os.path.join(category_dir, matches[0])
            
            return None
            
        except Exception as e:
            logger.error(f"获取litematic文件失败: {e}")
            return None 