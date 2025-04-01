import time
import os
import shutil
from astrbot import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import File

class UploadCommand:
    def __init__(self, file_manager, category_manager):
        self.file_manager = file_manager
        self.category_manager = category_manager
        self.upload_states = {}  # 用户上传状态跟踪
    
    async def execute(self, event: AstrMessageEvent, category: str = "default"):
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助
        /投影 分类名 - 上传文件到指定分类
        """
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
        if not self.category_manager.category_exists(category):
            self.category_manager.create_category(category)
            yield event.plain_result(f"创建了新分类: {category}")
            
        # 记录用户上传状态
        user_key = f"{event.session_id}_{event.get_sender_id()}"
        self.upload_states[user_key] = {
            "category": category,
            "expire_time": time.time() + 300
        }
        
        yield event.plain_result(f"请在5分钟内上传.litematic文件到{category}分类")
    
    async def handle_upload(self, event: AstrMessageEvent):
        """处理文件上传事件"""
        user_key = f"{event.session_id}_{event.get_sender_id()}"
        
        # 验证上传状态
        if user_key not in self.upload_states:
            return
            
        # 检查是否超时
        if time.time() > self.upload_states[user_key].get("expire_time", 0):
            del self.upload_states[user_key]
            return
        
        # 处理文件上传
        for comp in event.message_obj.message:
            if isinstance(comp, File) and comp.name.endswith('.litematic'):
                file_path = comp.file
                category = self.upload_states[user_key].get("category", "default")
                
                try:
                    target_path = self.file_manager.save_litematic_file(file_path, category, comp.name)
                    yield event.plain_result(f"已成功保存litematic文件到{category}分类: {comp.name}")
                except Exception as e:
                    logger.error(f"保存litematic文件失败: {e}")
                    yield event.plain_result(f"保存litematic文件失败: {e}")
                
                # 清理用户状态
                del self.upload_states[user_key]
                return
        return 