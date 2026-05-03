import base64
import os
import time
from pathlib import Path
from typing import Any, List, Dict, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from quart import jsonify, request

from astrbot import logger
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Star, register, Context
from astrbot.core import AstrBotConfig

# 导入新的模块化结构
from .services.file_manager import FileManager
from .services.category_manager import CategoryManager
from .services.render_manager import RenderManager
from .services.render_3d_manager import Render3DManager
from .services.lang_manager import LangManager
from .utils.config import Config
from .commands.get_command import GetCommand
from .commands.delete_command import DeleteCommand
from .commands.upload_command import UploadCommand
from .commands.list_command import ListCommand
from .commands.material_command import MaterialCommand
from .commands.info_command import InfoCommand
from .commands.preview_command import PreviewCommand
from .commands.render3d_command import Render3DCommand

@register("litematic", "kterna", "读取、管理并 WebUI 渲染 Litematic 文件", "1.4.0", "https://github.com/kterna/astrbot_plugin_litematic")
class LitematicPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)

        # 初始化配置
        self.config: Config = Config(context, config)
        
        # 获取插件目录
        plugin_dir: str = os.path.dirname(os.path.abspath(__file__))
        
        # 初始化服务
        self.category_manager: CategoryManager = CategoryManager(self.config)
        self.file_manager: FileManager = FileManager(self.config, self.category_manager)
        self.render_manager: RenderManager = RenderManager(self.config)
        self.render_3d_manager: Render3DManager = Render3DManager(self.config)
        self.lang_manager: LangManager = LangManager(plugin_dir)
        
        # 初始化命令处理器
        self.upload_command: UploadCommand = UploadCommand(self.file_manager, self.category_manager)
        self.list_command: ListCommand = ListCommand(self.category_manager, self.file_manager)
        self.delete_command: DeleteCommand = DeleteCommand(self.category_manager, self.file_manager)
        self.get_command: GetCommand = GetCommand(self.file_manager)
        self.material_command: MaterialCommand = MaterialCommand(self.file_manager, self.category_manager, self.lang_manager)
        self.info_command: InfoCommand = InfoCommand(self.file_manager, self.category_manager)
        self.preview_command: PreviewCommand = PreviewCommand(self.file_manager, self.render_manager)
        self.render3d_command: Render3DCommand = Render3DCommand(self.file_manager, self.render_3d_manager)
        
        # 保留原有变量以保持兼容性
        self.litematic_dir: str = self.config.get_litematic_dir()
        self.categories_file: str = self.config.get_categories_file()
        self.webui_max_file_size_bytes: int = self.config.get_config_value("webui_max_file_size_bytes", 33554432)
        os.makedirs(self.litematic_dir, exist_ok=True)
        os.makedirs(os.path.join(plugin_dir, "temp"), exist_ok=True)
        
        self.litematic_categories: List[str] = self.category_manager.get_categories()
        
        # 保留原有的线程池
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self.config.get_config_value("max_workers", 3))

        self._register_webui_apis(context)

    def _register_webui_apis(self, context: Context) -> None:
        """注册 WebUI 读取接口。"""
        context.register_web_api(
            "/litematic/categories",
            self.webui_categories,
            ["GET"],
            "获取 Litematic 分类与文件统计",
        )
        context.register_web_api(
            "/litematic/files",
            self.webui_files,
            ["GET"],
            "获取指定分类下的 Litematic 文件列表",
        )
        context.register_web_api(
            "/litematic/file",
            self.webui_file,
            ["GET"],
            "读取指定 Litematic 文件内容",
        )

    def _webui_response(self, data: Any = None, *, ok: bool = True, error: str = "", status: int = 200):
        return jsonify({"ok": ok, "data": data, "error": error}), status

    def _category_names_for_webui(self) -> List[str]:
        configured = self.category_manager.get_categories()
        data_root = Path(self.file_manager.get_litematic_dir())
        disk_categories: List[str] = []
        if data_root.exists():
            disk_categories = sorted(path.name for path in data_root.iterdir() if path.is_dir())

        names: List[str] = []
        seen = set()
        for name in [*configured, *disk_categories]:
            if name and name not in seen:
                names.append(name)
                seen.add(name)
        return names

    def _category_dir_for_webui(self, category: str) -> Path:
        if not category or category in {".", ".."} or "/" in category or "\\" in category:
            raise ValueError("分类名称无效")

        root = Path(self.file_manager.get_litematic_dir()).resolve()
        category_dir = (root / category).resolve()
        category_dir.relative_to(root)
        if not category_dir.is_dir():
            raise FileNotFoundError(f"分类不存在：{category}")
        return category_dir

    def _file_path_for_webui(self, category: str, filename: str) -> Path:
        if not filename or filename != os.path.basename(filename):
            raise ValueError("文件名称无效")
        if not filename.endswith(".litematic"):
            raise ValueError("仅支持 .litematic 文件")

        category_dir = self._category_dir_for_webui(category)
        file_path = (category_dir / filename).resolve()
        file_path.relative_to(category_dir)
        if not file_path.is_file():
            raise FileNotFoundError(f"文件不存在：{filename}")
        return file_path

    def _file_info_for_webui(self, path: Path) -> Dict[str, Any]:
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
            "modified_ts": int(stat.st_mtime),
        }

    async def webui_categories(self):
        """WebUI：获取分类列表。"""
        try:
            categories = []
            for category in self._category_names_for_webui():
                try:
                    category_dir = self._category_dir_for_webui(category)
                    files = sorted(path for path in category_dir.iterdir() if path.is_file() and path.name.endswith(".litematic"))
                except FileNotFoundError:
                    files = []

                categories.append(
                    {
                        "name": category,
                        "count": len(files),
                        "total_size": sum(path.stat().st_size for path in files),
                    }
                )
            return self._webui_response(categories)
        except Exception as exc:
            logger.error(f"Litematic WebUI 获取分类失败: {exc}")
            return self._webui_response(ok=False, error=str(exc), status=500)

    async def webui_files(self):
        """WebUI：获取指定分类的文件列表。"""
        category = (request.args.get("category") or "").strip()
        try:
            category_dir = self._category_dir_for_webui(category)
            files = sorted(
                (
                    self._file_info_for_webui(path)
                    for path in category_dir.iterdir()
                    if path.is_file() and path.name.endswith(".litematic")
                ),
                key=lambda item: item["modified_ts"],
                reverse=True,
            )
            return self._webui_response({"category": category, "files": files})
        except Exception as exc:
            status = 404 if isinstance(exc, FileNotFoundError) else 400
            return self._webui_response(ok=False, error=str(exc), status=status)

    async def webui_file(self):
        """WebUI：读取指定文件，返回 base64 内容。"""
        category = (request.args.get("category") or "").strip()
        filename = (request.args.get("filename") or "").strip()
        try:
            file_path = self._file_path_for_webui(category, filename)
            stat = file_path.stat()
            if stat.st_size > self.webui_max_file_size_bytes:
                raise ValueError(
                    f"文件超过 WebUI 读取上限：{format(stat.st_size, ',')} > {format(self.webui_max_file_size_bytes, ',')} 字节"
                )
            content = base64.b64encode(file_path.read_bytes()).decode("ascii")
            return self._webui_response(
                {
                    "category": category,
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                    "content_base64": content,
                }
            )
        except Exception as exc:
            status = 404 if isinstance(exc, FileNotFoundError) else 400
            return self._webui_response(ok=False, error=str(exc), status=status)
    
    def load_categories(self) -> None:
        """保留兼容性，实际调用CategoryManager"""
        self.litematic_categories = self.category_manager.get_categories()
    
    def save_categories(self) -> None:
        """保留兼容性，实际调用CategoryManager"""
        self.category_manager.save_categories()
    
    @filter.command("投影",alias=["litematic"])
    async def litematic(self, event: AstrMessageEvent, category: str = "default") -> AsyncGenerator[MessageChain, None]:
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助
        /投影 分类名 - 上传文件到指定分类
        /投影列表 分类名 - 列出指定分类下的文件
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影获取 分类名 文件名 - 发送指定分类下的文件
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
        /投影信息 分类名 文件名 - 分析指定分类下文件的详细信息
        /投影预览 分类名 文件名 - 生成并显示litematic的2D预览图
        /投影3D 分类名 文件名 [动画类型] [帧数] [持续时间] [仰角] [分辨率] - 生成并显示litematic的3D渲染动画
        
        Args:
            event: 消息事件
            category: 分类名称，默认为"default"
            
        Yields:
            MessageChain: 响应消息
        """
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
                         duration: int = 100, elevation: float = 30.0,
                         resolution: str = "native") -> AsyncGenerator[MessageChain, None]:
        """
        生成litematic文件的3D渲染动画
        使用方法：
        /投影3D 分类名 文件名 - 生成并显示litematic的3D渲染动画
        /投影3D 分类名 文件名 动画类型 帧数 持续时间 仰角 分辨率 - 自定义参数生成3D渲染动画
        
        Args:
            event: 消息事件
            category: 分类名称
            filename: 文件名
            animation_type: 动画类型 (rotation/orbit/zoom)，默认为"rotation"
            frames: 帧数，默认为36
            duration: 每帧持续时间(毫秒)，默认为100
            elevation: 相机仰角(度)，默认为30.0
            resolution: 分辨率(native/default 或 WxH，支持 native@上限)，默认为native
            
        Yields:
            MessageChain: 响应消息
        """
        # 使用Render3DCommand处理投影3D命令
        async for response in self.render3d_command.execute(
            event, category, filename, animation_type, int(frames), int(duration), float(elevation), resolution
        ):
            yield response
