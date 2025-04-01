import os
from concurrent.futures import ThreadPoolExecutor

from astrbot import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star, register, Context

# 导入新的模块化结构
from .services.file_manager import FileManager
from .services.category_manager import CategoryManager
from .services.render_manager import RenderManager
from .utils.config import Config
from .commands.get_command import GetCommand
from .commands.delete_command import DeleteCommand
from .commands.upload_command import UploadCommand
from .commands.list_command import ListCommand
from .commands.material_command import MaterialCommand
from .commands.info_command import InfoCommand
from .commands.preview_command import PreviewCommand

@register("litematic", "kterna", "读取处理Litematic文件", "1.1.1", "https://github.com/kterna/astrbot_plugin_litematic")
class LitematicPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化配置
        self.config = Config(context)
        
        # 初始化服务
        self.category_manager = CategoryManager(self.config)
        self.file_manager = FileManager(self.config, self.category_manager)
        self.render_manager = RenderManager(self.config)
        
        # 初始化命令处理器
        self.upload_command = UploadCommand(self.file_manager, self.category_manager)
        self.list_command = ListCommand(self.category_manager, self.file_manager)
        self.delete_command = DeleteCommand(self.category_manager, self.file_manager)
        self.get_command = GetCommand(self.file_manager)
        self.material_command = MaterialCommand(self.file_manager, self.category_manager)
        self.info_command = InfoCommand(self.file_manager, self.category_manager)
        self.preview_command = PreviewCommand(self.file_manager, self.render_manager)
        
        # 保留原有变量以保持兼容性
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.litematic_dir = self.config.get_litematic_dir()
        self.categories_file = self.config.get_categories_file()
        os.makedirs(self.litematic_dir, exist_ok=True)
        os.makedirs(os.path.join(plugin_dir, "temp"), exist_ok=True)
        
        self.litematic_categories = self.category_manager.get_categories()
        
        # 保留原有的线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.get_config_value("max_workers", 3))
    
    def load_categories(self):
        """保留兼容性，实际调用CategoryManager"""
        self.litematic_categories = self.category_manager.get_categories()
    
    def save_categories(self):
        """保留兼容性，实际调用CategoryManager"""
        self.category_manager.save_categories()
    
    @filter.command("投影",alias=["litematic"])
    async def litematic(self, event: AstrMessageEvent, category: str = "default"):
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助
        /投影 分类名 - 上传文件到指定分类
        """
        # 使用UploadCommand处理投影命令
        async for response in self.upload_command.execute(event, category):
            yield response

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_upload_litematic(self, event: AstrMessageEvent):
        """处理上传的.litematic文件"""
        # 直接委托给UploadCommand处理
        async for response in self.upload_command.handle_upload(event):
            yield response

    @filter.command("投影列表",alias=["litematic_list"])
    async def litematic_list(self, event: AstrMessageEvent, category: str = ""):
        """
        列出litematic文件
        使用方法：
        /投影列表 - 列出所有分类
        /投影列表 分类名 - 列出指定分类下的文件
        """
        # 使用ListCommand处理投影列表命令
        async for response in self.list_command.execute(event, category):
            yield response
        
    @filter.command("投影删除", alias=["litematic_delete"])
    async def litematic_delete(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        删除litematic文件或分类
        使用方法：
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影删除 分类名 文件名 - 删除指定分类下的文件
        """
        # 使用DeleteCommand处理删除命令
        async for response in self.delete_command.execute(event, category, filename):
            yield response

    @filter.command("投影获取", alias=["litematic_get"])
    async def litematic_get(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        获取litematic文件
        使用方法：
        /投影获取 分类名 文件名 - 发送指定分类下的文件
        """
        # 使用GetCommand处理获取命令
        async for response in self.get_command.execute(event, category, filename):
            yield response
    
    @filter.command("投影材料", alias=["litematic_material"])
    async def litematic_material(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        分析litematic文件所需材料
        使用方法：
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
        """
        # 使用MaterialCommand处理投影材料命令
        async for response in self.material_command.execute(event, category, filename):
            yield response

    @filter.command("投影信息", alias=["litematic_info"])
    async def litematic_info(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        分析litematic文件详细信息
        使用方法：
        /投影信息 分类名 文件名 - 分析指定分类下文件的详细信息
        """
        # 使用InfoCommand处理投影信息命令
        async for response in self.info_command.execute(event, category, filename):
            yield response
            
    @filter.command("投影预览", alias=["litematic_preview"])
    async def litematic_preview(self, event: AstrMessageEvent, category: str = "", filename: str = "", view: str = "combined"):
        """
        预览litematic文件的2D渲染效果
        使用方法：
        /投影预览 分类名 文件名 - 生成并显示litematic的预览图
        /投影预览 分类名 文件名 视角 - 生成并显示指定视角的预览图
        支持的视角: top(俯视图), front(正视图), side(侧视图), combined(综合视图), 
                north(北面), south(南面), east(东面), west(西面)
        """
        # 使用PreviewCommand处理投影预览命令
        async for response in self.preview_command.execute(event, category, filename, view):
            yield response