from astrbot import logger
from astrbot.api.event import AstrMessageEvent

class DeleteCommand:
    def __init__(self, category_manager, file_manager):
        self.category_manager = category_manager
        self.file_manager = file_manager
    
    async def execute(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        删除litematic文件或分类
        使用方法：
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影删除 分类名 文件名 - 删除指定分类下的文件
        """
        # 验证参数
        if not category:
            yield event.plain_result("请指定要删除的分类名，例如：/投影删除 建筑")
            return
        
        # 验证分类是否存在
        if not self.category_manager.category_exists(category):
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.category_manager.get_categories())}")
            return
        
        # 删除整个分类
        if not filename:
            success = self.category_manager.delete_category(category)
            if success:
                yield event.plain_result(f"已删除分类 {category} 及其下所有文件")
            else:
                yield event.plain_result(f"删除分类 {category} 失败")
            return
        
        # 删除指定文件
        result, error = self.file_manager.delete_litematic_file(category, filename)
        
        if error and isinstance(result, list):
            # 找到多个匹配的文件
            matches_text = "\n".join([f"- {file}" for file in result])
            yield event.plain_result(f"找到多个匹配的文件，请指定完整文件名：\n{matches_text}")
        elif error:
            # 其他错误
            yield event.plain_result(error)
        else:
            # 成功删除
            yield event.plain_result(f"已删除文件: {result}") 