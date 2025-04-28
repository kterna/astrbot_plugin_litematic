import os
from typing import List, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Star, register, Context

# 导入新的模块化结构
from .services.file_manager import FileManager
from .services.category_manager import CategoryManager
from .services.render_manager import RenderManager
from .services.render_3d_manager import Render3DManager
from .utils.config import Config
from .utils.button_utils import ButtonUtils
from .commands.get_command import GetCommand
from .commands.delete_command import DeleteCommand
from .commands.upload_command import UploadCommand
from .commands.list_command import ListCommand
from .commands.material_command import MaterialCommand
from .commands.info_command import InfoCommand
from .commands.preview_command import PreviewCommand
from .commands.render3d_command import Render3DCommand

@register("litematic", "kterna", "读取处理Litematic文件", "1.3.5", "https://github.com/kterna/astrbot_plugin_litematic")
class LitematicPlugin(Star):
    def __init__(self, context: Context) -> None:
        super().__init__(context)

        # 初始化配置
        self.config: Config = Config(context)

        # 初始化服务
        self.category_manager: CategoryManager = CategoryManager(self.config)
        self.file_manager: FileManager = FileManager(self.config, self.category_manager)
        self.render_manager: RenderManager = RenderManager(self.config)
        self.render_3d_manager: Render3DManager = Render3DManager(self.config)

        # 初始化按钮工具
        self.button_utils: ButtonUtils = ButtonUtils(context)

        # 初始化命令处理器
        self.upload_command: UploadCommand = UploadCommand(self.file_manager, self.category_manager)
        self.list_command: ListCommand = ListCommand(self.category_manager, self.file_manager, self.button_utils)
        self.delete_command: DeleteCommand = DeleteCommand(self.category_manager, self.file_manager)
        self.get_command: GetCommand = GetCommand(self.file_manager)
        self.material_command: MaterialCommand = MaterialCommand(self.file_manager, self.category_manager, self.button_utils)
        self.info_command: InfoCommand = InfoCommand(self.file_manager, self.category_manager, self.button_utils)
        self.preview_command: PreviewCommand = PreviewCommand(self.file_manager, self.render_manager, self.button_utils)
        self.render3d_command: Render3DCommand = Render3DCommand(self.file_manager, self.render_3d_manager, self.button_utils)

        # 保留原有变量以保持兼容性
        plugin_dir: str = os.path.dirname(os.path.abspath(__file__))
        self.litematic_dir: str = self.config.get_litematic_dir()
        self.categories_file: str = self.config.get_categories_file()
        os.makedirs(self.litematic_dir, exist_ok=True)
        os.makedirs(os.path.join(plugin_dir, "temp"), exist_ok=True)

        self.litematic_categories: List[str] = self.category_manager.get_categories()

        # 保留原有的线程池
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self.config.get_config_value("max_workers", 3))

    def load_categories(self) -> None:
        """保留兼容性，实际调用CategoryManager"""
        self.litematic_categories = self.category_manager.get_categories()

    def save_categories(self) -> None:
        """保留兼容性，实际调用CategoryManager"""
        self.category_manager.save_categories()

    @filter.command("投影",alias=["litematic"])
    async def litematic(self, event: AstrMessageEvent, category: str = "default") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助和主菜单
        /投影 分类名 - 上传文件到指定分类
        /投影列表 分类名 - 列出指定分类下的文件
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影获取 分类名 文件名 - 发送指定分类下的文件
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
        /投影信息 分类名 文件名 - 分析指定分类下文件的详细信息
        /投影预览 分类名 文件名 - 生成并显示litematic的2D预览图
        /投影3D 分类名 文件名 - 生成并显示litematic的3D渲染动画

        Args:
            event: 消息事件
            category: 分类名称，默认为"default"

        Yields:
            MessageChain: 响应消息
        """

        help_text = """投影插件使用帮助：
/投影 - 查看帮助和主菜单
/投影 分类名 - 上传文件到指定分类
/投影列表 - 列出所有分类
/投影列表 分类名 - 列出指定分类下的文件
/投影删除 分类名 - 删除指定分类及其下所有文件
/投影删除 分类名 文件名 - 删除指定分类下的文件
/投影获取 分类名 文件名 - 发送指定分类下的文件
/投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
/投影信息 分类名 文件名 - 分析指定分类下文件的详细信息
/投影预览 分类名 文件名 - 生成并显示litematic的2D预览图
/投影3D 分类名 文件名 - 生成并显示litematic的3D渲染动画"""

        # 如果分类为"help"，只显示帮助文本，不显示按钮
        if category == "help":

            # 无论是否安装按钮插件，都只显示文字帮助信息
            yield event.plain_result(help_text)
            return

        # 如果没有指定分类，显示帮助和主菜单按钮
        if category == "default":

            # 检查按钮插件是否安装且启用
            if self.button_utils and self.button_utils.is_button_enabled():
                # 按钮插件已安装且启用，显示按钮
                buttons_info = self.button_utils.create_main_menu_buttons()
                button_sent = await self.button_utils.send_buttons(event, buttons_info)

                # 如果按钮发送失败，显示文字
                if not button_sent:
                    yield event.plain_result(help_text)
            else:
                # 按钮插件未安装或未启用，显示文字
                yield event.plain_result(help_text)

            return

        # 使用UploadCommand处理投影命令
        async for response in self.upload_command.execute(event, category):
            yield response

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_upload_litematic(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        """
        处理上传的.litematic文件

        Args:
            event: 消息事件

        Yields:
            MessageChain: 响应消息
        """
        # 直接委托给UploadCommand处理
        async for response in self.upload_command.handle_upload(event):
            yield response

    @filter.command("投影列表",alias=["litematic_list"])
    async def litematic_list(self, event: AstrMessageEvent, category: str = "") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
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
        # 使用ListCommand处理投影列表命令
        async for response in self.list_command.execute(event, category):
            yield response

    @filter.command("投影删除", alias=["litematic_delete"])
    async def litematic_delete(self, event: AstrMessageEvent, category: str = "", filename: str = "") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
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
        # 使用DeleteCommand处理删除命令
        async for response in self.delete_command.execute(event, category, filename):
            yield response

    @filter.command("投影获取", alias=["litematic_get"])
    async def litematic_get(self, event: AstrMessageEvent, category: str = "", filename: str = "") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        获取litematic文件
        使用方法：
        /投影获取 分类名 文件名 - 发送指定分类下的文件

        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串

        Yields:
            MessageChain: 响应消息
        """
        # 使用GetCommand处理获取命令
        async for response in self.get_command.execute(event, category, filename):
            yield response

    @filter.command("投影材料", alias=["litematic_material"])
    async def litematic_material(self, event: AstrMessageEvent, category: str = "", filename: str = "") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        分析litematic文件所需材料
        使用方法：
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料

        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串

        Yields:
            MessageChain: 响应消息
        """
        # 使用MaterialCommand处理投影材料命令
        async for response in self.material_command.execute(event, category, filename):
            yield response

    @filter.command("投影信息", alias=["litematic_info"])
    async def litematic_info(self, event: AstrMessageEvent, category: str = "", filename: str = "") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        分析litematic文件详细信息
        使用方法：
        /投影信息 分类名 文件名 - 分析指定分类下文件的详细信息

        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串

        Yields:
            MessageChain: 响应消息
        """
        # 使用InfoCommand处理投影信息命令
        async for response in self.info_command.execute(event, category, filename):
            yield response

    @filter.command("投影预览", alias=["litematic_preview"])
    async def litematic_preview(self, event: AstrMessageEvent, category: str = "", filename: str = "", view: str = "combined") -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        预览litematic文件的2D渲染效果
        使用方法：
        /投影预览 分类名 文件名 - 生成并显示litematic的预览图
        /投影预览 分类名 文件名 视角 - 生成并显示指定视角的预览图

        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串
            view: 视角类型，默认为"combined"

        Yields:
            MessageChain: 响应消息
        """
        # 使用PreviewCommand处理投影预览命令
        async for response in self.preview_command.execute(event, category, filename, view):
            yield response

    @filter.command("投影3D", alias=["litematic_3d"])
    async def litematic_3d(self, event: AstrMessageEvent, category: str = "", filename: str = "",
                         animation_type: str = "rotation", frames: int = 36,
                         duration: int = 100, elevation: float = 30.0) -> AsyncGenerator[MessageChain, None]:
        # 禁止 LLM 请求
        event.should_call_llm(True)
        """
        生成litematic文件的3D渲染动画
        使用方法：
        /投影3D 分类名 文件名 - 生成并显示litematic的3D渲染动画
        /投影3D 分类名 文件名 动画类型 帧数 持续时间 仰角 - 自定义参数生成3D渲染动画

        Args:
            event: 消息事件
            category: 分类名称
            filename: 文件名
            animation_type: 动画类型 (rotation/orbit/zoom)，默认为"rotation"
            frames: 帧数，默认为36
            duration: 每帧持续时间(毫秒)，默认为100
            elevation: 相机仰角(度)，默认为30.0

        Yields:
            MessageChain: 响应消息
        """
        # 使用Render3DCommand处理投影3D命令
        async for response in self.render3d_command.execute(
            event, category, filename, animation_type, int(frames), int(duration), float(elevation)
        ):
            yield response

    @filter.command("投影按钮")
    async def litematic_button(self, event: AstrMessageEvent) -> AsyncGenerator[MessageChain, None]:
        """
        开关投影按钮功能
        使用方法：
        /投影按钮 - 开关当前按钮状态

        Args:
            event: 消息事件

        Yields:
            MessageChain: 响应消息
        """
        # 禁止 LLM 请求
        event.should_call_llm(True)

        # 仅管理员可以使用此命令
        if not event.is_admin():
            yield event.plain_result("⛔ 只有管理员才能使用此命令")
            return

        # 检查按钮插件是否安装
        button_plugin = None
        if self.button_utils:
            button_plugin = self.button_utils.get_button_plugin()

        if button_plugin and button_plugin.star_cls:
            # 确保button_enabled属性存在
            if not hasattr(button_plugin.star_cls, "button_enabled"):
                button_plugin.star_cls.button_enabled = True

            # 按钮插件已安装，切换按钮状态
            button_enabled = not button_plugin.star_cls.button_enabled
            button_plugin.star_cls.button_enabled = button_enabled
            yield event.plain_result(f"投影按钮功能已{'启用' if button_enabled else '禁用'}")
        else:
            yield event.plain_result("未找到按钮插件，请确保已安装并启用 astrbot_plugin_buttons 插件")