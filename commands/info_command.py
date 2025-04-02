import os
import traceback
from typing import List, Optional
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from ..core.detail_analysis.detail_analysis import DetailAnalysis
from litemapy import Schematic
from ..services.file_manager import FileManager
from ..services.category_manager import CategoryManager
from ..utils.types import CategoryType, FilePath, MessageResponse

class InfoCommand:
    """投影信息命令处理器，负责处理查看投影详细信息的命令"""
    
    def __init__(self, file_manager: FileManager, category_manager: CategoryManager) -> None:
        """初始化投影信息命令处理器
        
        Args:
            file_manager: 文件管理器对象
            category_manager: 分类管理器对象
        """
        self.file_manager: FileManager = file_manager
        self.category_manager: CategoryManager = category_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "") -> MessageResponse:
        """执行投影信息命令
        
        Args:
            event: 消息事件对象
            category: 分类名
            filename: 文件名
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影信息 建筑 house.litematic")
            return
        
        # 验证分类是否存在
        categories: List[CategoryType] = self.category_manager.get_categories()
        if category not in categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(categories)}")
            return
        
        # 获取文件路径
        file_path: Optional[FilePath] = self._get_litematic_file(category, filename)
        if not file_path:
            yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}，请检查文件名")
            return
        
        try:
            # 加载litematic文件
            yield event.plain_result("正在分析投影文件，请稍候...")
            
            # 分析投影文件
            schematic: Schematic = Schematic.load(file_path)
            analyzer: DetailAnalysis = DetailAnalysis(schematic)
            details: List[str] = analyzer.analyze_schematic(file_path)
            
            # 生成结果文本
            result_text: str = f"【{os.path.basename(file_path)}】详细信息：\n\n"
            result_text += "\n".join(details)
            
            # 发送分析结果
            yield event.plain_result(result_text)
            
        except Exception as e:
            logger.error(f"分析投影文件失败: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"分析投影文件失败: {e}")
    
    def _get_litematic_file(self, category: CategoryType, filename: str) -> Optional[FilePath]:
        """获取litematic文件路径，支持模糊匹配
        
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