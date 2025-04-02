from typing import List, Union, Optional, Tuple
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from ..services.category_manager import CategoryManager
from ..services.file_manager import FileManager
from ..utils.types import CategoryType, FilePath, MessageResponse
from ..utils.exceptions import (
    CategoryNotFoundError,
    CategoryDeleteError,
    FileNotFoundError,
    FileDeleteError,
    MultipleFilesFoundError
)
from ..utils.logging_utils import log_error, log_operation

class DeleteCommand:
    def __init__(self, category_manager: CategoryManager, file_manager: FileManager) -> None:
        self.category_manager: CategoryManager = category_manager
        self.file_manager: FileManager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "") -> MessageResponse:
        """
        删除litematic文件或分类
        使用方法：
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影删除 分类名 文件名 - 删除指定分类下的文件
        
        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category:
            yield event.plain_result("请指定要删除的分类名，例如：/投影删除 建筑")
            return
        
        try:
            # 验证分类是否存在
            if not await self.category_manager.category_exists_async(category):
                # 使用异步方法检查分类
                log_operation("检查分类", False, {"category": category})
                categories = await self.category_manager.get_categories_async()
                yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(categories)}")
                return
            
            # 删除整个分类
            if not filename:
                try:
                    # 使用异步方法删除分类
                    await self.file_manager.delete_category_async(category)
                    # 删除分类记录
                    await self.category_manager.delete_category_async(category)
                    log_operation("删除分类", True, {"category": category})
                    yield event.plain_result(f"已删除分类 {category} 及其下所有文件")
                except CategoryDeleteError as e:
                    log_error(e)
                    yield event.plain_result(f"删除分类失败: {e.message}")
                except Exception as e:
                    log_error(e, extra_info={"category": category, "operation": "删除分类"})
                    yield event.plain_result(f"删除分类时出现错误: {str(e)}")
                return
            
            # 删除指定文件
            try:
                # 使用异步方法删除文件
                deleted_filename = await self.file_manager.delete_litematic_file_async(category, filename)
                # 成功删除
                log_operation("删除文件", True, {"category": category, "filename": deleted_filename})
                yield event.plain_result(f"已删除文件: {deleted_filename}")
            except MultipleFilesFoundError as e:
                log_error(e)
                matches_text = "\n".join([f"- {file}" for file in e.details.get("matches", [])])
                yield event.plain_result(f"找到多个匹配的文件，请指定完整文件名：\n{matches_text}")
            except FileNotFoundError as e:
                log_error(e)
                yield event.plain_result(e.message)
            except FileDeleteError as e:
                log_error(e)
                yield event.plain_result(f"删除文件失败: {e.message}")
            except Exception as e:
                log_error(e, extra_info={"category": category, "filename": filename, "operation": "删除文件"})
                yield event.plain_result(f"删除文件时出现错误: {str(e)}")
                
        except Exception as e:
            log_error(e, extra_info={"category": category, "filename": filename, "operation": "执行删除命令"})
            yield event.plain_result(f"执行命令时出现错误: {str(e)}") 