from typing import List
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from ..services.category_manager import CategoryManager
from ..services.file_manager import FileManager
from ..utils.types import CategoryType, MessageResponse
from ..utils.exceptions import CategoryNotFoundError, FileError
from ..utils.logging_utils import log_error, log_operation

class ListCommand:
    def __init__(self, category_manager: CategoryManager, file_manager: FileManager) -> None:
        self.category_manager: CategoryManager = category_manager
        self.file_manager: FileManager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "") -> MessageResponse:
        """
        列出litematic文件
        使用方法：
        /投影列表 - 列出所有分类
        /投影列表 分类名 - 列出指定分类下的文件
        
        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            
        Yields:
            MessageChain: 响应消息
        """
        try:
            # 列出所有分类
            if not category:
                categories: List[CategoryType] = self.category_manager.get_categories()
                if not categories:
                    log_operation("列出分类", True, {"result": "empty"})
                    yield event.plain_result("还没有任何分类，使用 /投影 分类名 来创建分类")
                    return
                    
                categories_text: str = "\n".join([f"- {cat}" for cat in categories])
                log_operation("列出分类", True, {"categories": categories})
                yield event.plain_result(f"可用的分类列表：\n{categories_text}\n\n使用 /投影列表 分类名 查看分类下的文件")
                return
            
            # 验证分类是否存在 - 这里仍然使用手动检查以避免异常干扰正常流程
            if not self.category_manager.category_exists(category):
                log_operation("检查分类", False, {"category": category})
                yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.category_manager.get_categories())}")
                return
            
            # 列出分类下的文件
            try:
                files: List[str] = self.file_manager.list_files(category)
                if not files:
                    log_operation("列出文件", True, {"category": category, "result": "empty"})
                    yield event.plain_result(f"分类 {category} 下还没有文件，使用 /投影 {category} 来上传文件")
                    return
                    
                files_text: str = "\n".join([f"- {file}" for file in files])
                log_operation("列出文件", True, {"category": category, "files_count": len(files)})
                yield event.plain_result(f"分类 {category} 下的文件：\n{files_text}")
            except FileError as e:
                log_error(e)
                yield event.plain_result(f"获取文件列表失败: {e.message}")
            except Exception as e:
                log_error(e, extra_info={"category": category, "operation": "列出文件"})
                yield event.plain_result(f"列出文件时出现错误: {str(e)}")
                
        except Exception as e:
            log_error(e, extra_info={"category": category, "operation": "执行列表命令"})
            yield event.plain_result(f"执行命令时出现错误: {str(e)}") 