import time
import os
import shutil
import asyncio
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
        self.timeout_tasks: Dict[UserKey, asyncio.Task] = {}  # 超时任务
    
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
                categories_text = "\n".join([f"- {cat}" for cat in await self.category_manager.get_categories_async()])
                yield event.plain_result(
                    f"投影\n"
                    f"请提供分类名称,例如: /投影 建筑\n"
                    f"当前可用分类：\n{categories_text}"
                )
                return
            
            # 处理新分类
            try:
                if not await self.category_manager.category_exists_async(category):
                    try:
                        await self.category_manager.create_category_async(category)
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
                timeout_sec = 300  # 5分钟超时
                
                # 清除之前的超时任务（如果存在）
                if user_key in self.timeout_tasks and not self.timeout_tasks[user_key].done():
                    self.timeout_tasks[user_key].cancel()
                
                # 设置新的状态和超时任务
                self.upload_states[user_key] = {
                    "category": category,
                    "expire_time": time.time() + timeout_sec
                }
                
                # 创建新的超时任务
                self.timeout_tasks[user_key] = asyncio.create_task(
                    self._handle_timeout(user_key, timeout_sec)
                )
                
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
        
        try:
            # 处理文件上传
            for comp in event.message_obj.message:
                if isinstance(comp, File) and comp.name.endswith('.litematic'):
                    file_path = comp.file
                    category = self.upload_states[user_key].get("category", "default")
                    
                    try:
                        # 使用异步方法保存文件
                        target_path = await self.file_manager.save_litematic_file_async(file_path, category, comp.name)
                        log_operation("保存文件", True, {"category": category, "filename": comp.name, "path": target_path})
                        yield event.plain_result(f"已成功保存litematic文件到{category}分类: {comp.name}")
                    except FileSaveError as e:
                        log_error(e, extra_info={"category": category, "filename": comp.name})
                        yield event.plain_result(f"保存litematic文件失败: {e.message}")
                    except Exception as e:
                        log_error(e, extra_info={"category": category, "filename": comp.name, "operation": "保存文件"})
                        yield event.plain_result(f"保存文件时出现错误: {str(e)}")
                    
                    # 清理用户状态和取消超时任务
                    await self._clear_user_state(user_key)
                    return
        except Exception as e:
            log_error(e, extra_info={"user_key": user_key, "operation": "处理文件上传"})
            yield event.plain_result(f"处理文件上传时出现错误: {str(e)}")
            # 出错时也清理状态
            await self._clear_user_state(user_key)
        return
    
    async def _handle_timeout(self, user_key: UserKey, timeout_sec: int) -> None:
        """
        处理上传超时
        
        Args:
            user_key: 用户标识
            timeout_sec: 超时秒数
        """
        try:
            await asyncio.sleep(timeout_sec)
            # 如果用户状态仍存在，则说明超时了
            if user_key in self.upload_states:
                log_operation("上传超时", False, {"user_key": user_key})
                del self.upload_states[user_key]
        except asyncio.CancelledError:
            # 任务被取消，正常情况（例如用户完成了上传）
            pass
        except Exception as e:
            log_error(e, extra_info={"user_key": user_key, "operation": "处理超时"})
    
    async def _clear_user_state(self, user_key: UserKey) -> None:
        """
        清理用户状态和相关任务
        
        Args:
            user_key: 用户标识
        """
        # 删除上传状态
        if user_key in self.upload_states:
            del self.upload_states[user_key]
        
        # 取消超时任务
        if user_key in self.timeout_tasks and not self.timeout_tasks[user_key].done():
            self.timeout_tasks[user_key].cancel()
            del self.timeout_tasks[user_key] 