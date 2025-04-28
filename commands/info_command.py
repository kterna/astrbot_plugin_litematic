import os
import traceback
import asyncio
from typing import List, Tuple
from astrbot import logger
from astrbot.api.event import AstrMessageEvent
from ..core.detail_analysis.detail_analysis import DetailAnalysis
from litemapy import Schematic
from ..services.file_manager import FileManager
from ..services.category_manager import CategoryManager
from ..utils.types import CategoryType, FilePath, MessageResponse
from ..utils.exceptions import (
    CategoryNotFoundError,
    FileNotFoundError,
    LitematicPluginError
)
from ..utils.button_utils import ButtonUtils
from ..utils.logging_utils import log_operation

class InfoCommand:
    """投影信息命令处理器，负责处理查看投影详细信息的命令"""

    def __init__(self, file_manager: FileManager, category_manager: CategoryManager, button_utils: ButtonUtils = None) -> None:
        """初始化投影信息命令处理器

        Args:
            file_manager: 文件管理器对象
            category_manager: 分类管理器对象
            button_utils: 按钮工具对象
        """
        self.file_manager: FileManager = file_manager
        self.category_manager: CategoryManager = category_manager
        self.button_utils: ButtonUtils = button_utils

    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "") -> MessageResponse:
        """执行投影信息命令

        Args:
            event: 消息事件对象
            category: 分类名
            filename: 文件名

        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影信息 建筑 house.litematic")
            return

        try:
            # 加载litematic文件
            yield event.plain_result("正在分析投影文件，请稍候...")

            # 获取文件路径 - 使用异步方法
            file_path: FilePath = await self.file_manager.get_litematic_file_async(category, filename)

            # 分析投影文件 - 使用线程池处理CPU密集型操作
            schematic, details = await asyncio.to_thread(self._analyze_schematic, file_path)

            # 生成结果文本
            result_text: str = f"【{os.path.basename(file_path)}】详细信息：\n\n"
            result_text += "\n".join(details)

            # 无论按钮功能是否开启，都先发送文字内容
            yield event.plain_result(result_text)

            # 如果按钮插件已安装且启用，额外显示按钮
            if self.button_utils and self.button_utils.is_button_enabled():
                log_operation("添加文件操作按钮", True, {"category": category, "filename": filename})
                buttons_info = self.button_utils.create_file_operation_buttons(category, filename)
                await self.button_utils.send_buttons(event, buttons_info)

        except FileNotFoundError as e:
            yield event.plain_result(e.message)
        except CategoryNotFoundError as e:
            yield event.plain_result(e.message)
        except LitematicPluginError as e:
            logger.error(f"分析投影文件失败: {e.message} (错误代码: {e.code})")
            yield event.plain_result(f"分析投影文件失败: {e.message}")
        except Exception as e:
            logger.error(f"分析投影文件时出现未知错误: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"分析投影文件时出现错误: {str(e)}")

    def _analyze_schematic(self, file_path: FilePath) -> Tuple[Schematic, List[str]]:
        """分析投影文件（在线程池中运行的CPU密集型操作）

        Args:
            file_path: 投影文件路径

        Returns:
            Tuple[Schematic, List[str]]: 结构体和分析结果
        """
        schematic: Schematic = Schematic.load(file_path)
        analyzer: DetailAnalysis = DetailAnalysis(schematic)
        details: List[str] = analyzer.analyze_schematic(file_path)
        return schematic, details