import os
import re
import traceback
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.message_components import Image

from ..services.file_manager import FileManager
from ..services.render_3d_manager import Render3DManager
from ..utils.types import CategoryType, FilePath, MessageResponse
from ..utils.exceptions import (
    CategoryNotFoundError, 
    FileNotFoundError, 
    LitematicPluginError,
    RenderError
)

class Render3DCommand:
    """实现3D渲染命令"""
    
    def __init__(self, file_manager: FileManager, render_3d_manager: Render3DManager) -> None:
        """
        初始化3D渲染命令
        
        Args:
            file_manager: 文件管理器
            render_3d_manager: 3D渲染管理器
        """
        self.file_manager = file_manager
        self.render_3d_manager = render_3d_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "", 
                     animation_type: str = "rotation", frames: int = 36, duration: int = 100,
                     elevation: float = 30.0, resolution: str = "native") -> MessageResponse:
        """
        渲染litematic文件的3D动画
        
        Args:
            event: 消息事件
            category: 分类名称
            filename: 文件名
            animation_type: 动画类型 (rotation/orbit/zoom)
            frames: 帧数
            duration: 每帧持续时间(毫秒)
            elevation: 相机仰角(度)
            resolution: 分辨率(native/default 或 WxH)
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result(self._get_help_text())
            return
        
        # 验证动画类型
        if animation_type not in ["rotation", "orbit", "zoom"]:
            yield event.plain_result(f"不支持的动画类型: {animation_type}，请使用 rotation、orbit 或 zoom")
            return
        
        # 验证帧数
        if frames < 1 or frames > 120:
            yield event.plain_result("帧数必须在1到120之间")
            return
        
        # 验证持续时间
        if duration < 50 or duration > 500:
            yield event.plain_result("每帧持续时间必须在50到500毫秒之间")
            return
        
        # 验证仰角
        if elevation < 0 or elevation > 90:
            yield event.plain_result("相机仰角必须在0到90度之间")
            return

        # 验证分辨率
        try:
            window_size, native_textures, native_max_size = self._parse_resolution(resolution)
        except ValueError as e:
            yield event.plain_result(str(e))
            return
        
        try:
            # 发送处理提示
            yield event.plain_result("正在生成3D渲染动画，请稍候...")
            
            # 获取文件路径
            file_path: FilePath = await self.file_manager.get_litematic_file_async(category, filename)
            
            # 渲染3D动画
            gif_path = await self.render_3d_manager.render_litematic_3d_async(
                file_path, 
                animation_type=animation_type,
                frames=frames,
                duration=duration,
                elevation=elevation,
                optimize=True,
                window_size=window_size,
                native_textures=native_textures,
                native_max_size=native_max_size
            )
            
            # 准备消息链
            message: MessageChain = MessageChain()
            message.chain.append(Image.fromFileSystem(gif_path))
            
            # 发送GIF
            await event.send(message)
            
            # 发送说明文本
            caption = self._get_animation_caption(animation_type)
            yield event.plain_result(f"【{os.path.basename(file_path)}】3D{caption}")
            
            # 删除临时文件
            if os.path.exists(gif_path):
                await asyncio.to_thread(os.remove, gif_path)
                
        except FileNotFoundError as e:
            yield event.plain_result(e.message)
        except CategoryNotFoundError as e:
            yield event.plain_result(e.message)
        except RenderError as e:
            logger.error(f"3D渲染失败: {e.message} (错误代码: {e.code})")
            yield event.plain_result(f"3D渲染失败: {e.message}")
        except LitematicPluginError as e:
            logger.error(f"3D渲染失败: {e.message} (错误代码: {e.code})")
            yield event.plain_result(f"3D渲染失败: {e.message}")
        except Exception as e:
            logger.error(f"3D渲染时出现未知错误: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"3D渲染时出现错误: {str(e)}")
    
    def _get_animation_caption(self, animation_type: str) -> str:
        """
        获取动画类型对应的说明文字
        
        Args:
            animation_type: 动画类型
            
        Returns:
            str: 说明文字
        """
        captions: Dict[str, str] = {
            "rotation": "旋转动画",
            "orbit": "环绕动画",
            "zoom": "缩放动画"
        }
        return captions.get(animation_type, "动画")
    
    def _get_help_text(self) -> str:
        """
        获取帮助文本
        
        Returns:
            str: 帮助文本
        """
        return (
            "3D渲染命令使用方法：\n"
            "/投影3D 分类 文件名 [动画类型] [帧数] [持续时间] [仰角] [分辨率]\n\n"
            "支持的动画类型：\n"
            "- rotation: 旋转动画(默认)\n"
            "- orbit: 环绕动画\n"
            "- zoom: 缩放动画\n\n"
            "可选参数：\n"
            "- 帧数: 1-120之间的整数，默认36\n"
            "- 持续时间: 每帧的持续时间(毫秒)，50-500之间，默认100\n"
            "- 仰角: 相机仰角(度)，0-90之间，默认30\n"
            "- 分辨率: native(按贴图原生分辨率自动计算，可用 native@12000 提高上限)\n"
            "          default(固定800x600) / WxH，例如 1024x768\n\n"
            "例如：/投影3D 建筑 房子 rotation 36 100 30 native\n"
            "或：/投影3D 建筑 房子 rotation 36 100 30 1024x768"
        )

    def _parse_resolution(self, resolution: str) -> Tuple[Optional[Tuple[int, int]], bool, Optional[Tuple[int, int]]]:
        min_size = 64
        max_size = 32768

        if resolution is None:
            return None, True, None

        value = str(resolution).strip().lower()
        if not value:
            return None, True, None

        native_match = re.match(
            r"^(native|原生|原生分辨率|auto|自动)(?:[@:](\d+)(?:\s*[xX×\*_,]\s*(\d+))?)?$",
            value
        )
        if native_match:
            if native_match.group(2):
                max_width = int(native_match.group(2))
                max_height = int(native_match.group(3)) if native_match.group(3) else max_width
                if (max_width < min_size or max_height < min_size
                        or max_width > max_size or max_height > max_size):
                    raise ValueError(
                        f"原生分辨率上限必须在 {min_size}x{min_size} 到 {max_size}x{max_size} 之间"
                    )
                return None, True, (max_width, max_height)
            return None, True, None

        if value in {"default", "默认"}:
            return None, False, None

        match = re.match(r"^(\d+)\s*[xX×\*_,]\s*(\d+)$", value)
        if not match:
            raise ValueError("分辨率格式错误，请使用 native、default、native@上限 或 WxH，例如 1024x768/1024×768")

        width = int(match.group(1))
        height = int(match.group(2))
        if width < min_size or height < min_size or width > max_size or height > max_size:
            raise ValueError(f"分辨率必须在 {min_size}x{min_size} 到 {max_size}x{max_size} 之间")

        return (width, height), False, None
