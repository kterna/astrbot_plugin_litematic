import time
import os
import shutil
from typing import Dict, Any

from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import File

from ..services.file_manager import FileManager
from ..services.category_manager import CategoryManager
from ..utils.types import UploadStatus, UserKey, MessageResponse, CategoryType
from ..utils.exceptions import CategoryNotFoundError, CategoryCreateError, CategoryAlreadyExistsError, FileSaveError
from ..utils.logging_utils import log_error, log_operation

class UploadCommand:
    def __init__(self, file_manager: FileManager, category_manager: CategoryManager) -> None:
        self.file_manager: FileManager = file_manager
        self.category_manager: CategoryManager = category_manager
        self.upload_states: Dict[UserKey, UploadStatus] = {}  # 用户上传状态跟踪
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "default") -> MessageResponse:
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助
        /投影 分类名 - 上传文件到指定分类
        
        Args:
            event: 消息事件
            category: 分类名称，默认为"default"
            
        Yields:
            MessageChain: 响应消息
        """
        try:
            # 显示帮助信息
            if not category or category == "default":
                categories_text = "\n".join([f"- {cat}" for cat in self.category_manager.get_categories()])
                yield event.plain_result(
                    f"投影\n"
                    f"请提供分类名称,例如: /投影 建筑\n"
                    f"当前可用分类：\n{categories_text}"
                )
                return
            
            # 处理新分类
            try:
                if not self.category_manager.category_exists(category):
                    try:
                        self.category_manager.create_category(category)
                        log_operation("创建分类", True, {"category": category})
                        yield event.plain_result(f"创建了新分类: {category}")
                    except CategoryAlreadyExistsError:
                        # 忽略分类已存在的异常，这种情况不应该发生，因为我们已经检查了分类是否存在
                        pass
                    except CategoryCreateError as e:
                        log_error(e)
                        yield event.plain_result(f"创建分类失败: {e.message}")
                        return
                
                # 记录用户上传状态
                user_key: UserKey = f"{event.session_id}_{event.get_sender_id()}"
                self.upload_states[user_key] = {
                    "category": category,
                    "expire_time": time.time() + 300
                }
                
                log_operation("准备上传", True, {"category": category, "user_key": user_key})
                yield event.plain_result(f"请在5分钟内上传.litematic文件到{category}分类")
            except Exception as e:
                log_error(e, extra_info={"category": category, "operation": "设置上传状态"})
                yield event.plain_result(f"准备上传时出现错误: {str(e)}")
        except Exception as e:
            log_error(e, extra_info={"category": category, "operation": "执行上传命令"})
            yield event.plain_result(f"执行命令时出现错误: {str(e)}")
    
    async def handle_upload(self, event: AstrMessageEvent) -> MessageResponse:
        """
        处理文件上传事件
        
        Args:
            event: 消息事件
            
        Yields:
            MessageChain: 响应消息
        """
        user_key: UserKey = f"{event.session_id}_{event.get_sender_id()}"
        
        # 验证上传状态
        if user_key not in self.upload_states:
            return
            
        # 检查是否超时
        if time.time() > self.upload_states[user_key].get("expire_time", 0):
            log_operation("上传超时", False, {"user_key": user_key})
            del self.upload_states[user_key]
            return
        
        try:
            # 处理文件上传
            for comp in event.message_obj.message:
                if isinstance(comp, File) and comp.name.endswith('.litematic'):
                    file_path = comp.file
                    category = self.upload_states[user_key].get("category", "default")
                    
                    try:
                        target_path = self.file_manager.save_litematic_file(file_path, category, comp.name)
                        log_operation("保存文件", True, {"category": category, "filename": comp.name, "path": target_path})
                        yield event.plain_result(f"已成功保存litematic文件到{category}分类: {comp.name}")
                    except FileSaveError as e:
                        log_error(e, extra_info={"category": category, "filename": comp.name})
                        yield event.plain_result(f"保存litematic文件失败: {e.message}")
                    except Exception as e:
                        log_error(e, extra_info={"category": category, "filename": comp.name, "operation": "保存文件"})
                        yield event.plain_result(f"保存文件时出现错误: {str(e)}")
                    
                    # 清理用户状态
                    del self.upload_states[user_key]
                    return
        except Exception as e:
            log_error(e, extra_info={"user_key": user_key, "operation": "处理文件上传"})
            yield event.plain_result(f"处理文件上传时出现错误: {str(e)}")
            # 出错时也清理状态
            if user_key in self.upload_states:
                del self.upload_states[user_key]
        return 