from astrbot import logger
from astrbot.api.event import AstrMessageEvent

class ListCommand:
    def __init__(self, category_manager, file_manager):
        self.category_manager = category_manager
        self.file_manager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: str = ""):
        """
        列出litematic文件
        使用方法：
        /投影列表 - 列出所有分类
        /投影列表 分类名 - 列出指定分类下的文件
        """
        # 列出所有分类
        if not category:
            categories = self.category_manager.get_categories()
            if not categories:
                yield event.plain_result("还没有任何分类，使用 /投影 分类名 来创建分类")
                return
                
            categories_text = "\n".join([f"- {cat}" for cat in categories])
            yield event.plain_result(f"可用的分类列表：\n{categories_text}\n\n使用 /投影列表 分类名 查看分类下的文件")
            return
        
        # 验证分类是否存在
        if not self.category_manager.category_exists(category):
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.category_manager.get_categories())}")
            return
        
        # 列出分类下的文件
        files = self.file_manager.list_files(category)
        if not files:
            yield event.plain_result(f"分类 {category} 下还没有文件，使用 /投影 {category} 来上传文件")
            return
            
        files_text = "\n".join([f"- {file}" for file in files])
        yield event.plain_result(f"分类 {category} 下的文件：\n{files_text}") 