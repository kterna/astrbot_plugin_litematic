from typing import List, Dict
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context
from ..utils.logging_utils import log_error, log_operation

class ButtonUtils:
    def __init__(self, context: Context):
        self.context = context

    def get_button_plugin(self):
        """获取按钮插件实例"""
        try:
            return self.context.get_registered_star("astrbot_plugin_buttons")
        except Exception as e:
            log_error(e, extra_info={"operation": "获取按钮插件"})
            return None

    async def send_buttons(self, event: AstrMessageEvent, buttons_info: List[List[Dict[str, str]]]) -> bool:
        """
        发送按钮

        Args:
            event: 消息事件
            buttons_info: 按钮信息

        Returns:
            bool: 是否成功发送按钮
        """
        button_plugin = self.get_button_plugin()
        if not button_plugin or not button_plugin.star_cls:
            return False

        try:
            client = event.bot
            group_id = event.get_group_id()
            user_id = event.get_sender_id()

            await button_plugin.star_cls.send_button(
                client,
                buttons_info,
                group_id,
                user_id
            )
            log_operation("发送按钮", True, {"buttons_count": sum(len(row) for row in buttons_info)})
            return True
        except Exception as e:
            log_error(e, extra_info={"operation": "发送按钮"})
            return False

    def create_file_operation_buttons(self, category: str, filename: str) -> List[List[Dict[str, str]]]:
        """
        创建文件操作按钮

        Args:
            category: 分类名称
            filename: 文件名

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        return [
            [{"label": f"📄 {filename}", "callback": f"/投影信息 {category} {filename}"}],
            [
                {"label": "📥 获取", "callback": f"/投影获取 {category} {filename}"},
                {"label": "🧮 材料", "callback": f"/投影材料 {category} {filename}"},
                {"label": "🖼️ 预览", "callback": f"/投影预览 {category} {filename}"}
            ],
            [
                {"label": "🎬 3D渲染", "callback": f"/投影3D {category} {filename}"},
                {"label": "🗑️ 删除", "callback": f"/投影删除 {category} {filename}"}
            ],
            [
                {"label": "⬅️ 返回列表", "callback": f"/投影列表 {category}"}
            ],
            [
                {"label": "🏠 返回主菜单", "callback": "/投影"}
            ]
        ]

    def create_preview_buttons(self, category: str, filename: str) -> List[List[Dict[str, str]]]:
        """
        创建预览操作按钮

        Args:
            category: 分类名称
            filename: 文件名

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        return [
            [
                {"label": "顶视图", "callback": f"/投影预览 {category} {filename} top"},
                {"label": "前视图", "callback": f"/投影预览 {category} {filename} front"},
                {"label": "侧视图", "callback": f"/投影预览 {category} {filename} side"}
            ],
            [
                {"label": "组合视图", "callback": f"/投影预览 {category} {filename} combined"},
                {"label": "🎬 3D渲染", "callback": f"/投影3D {category} {filename}"}
            ],
            [
                {"label": "📥 获取", "callback": f"/投影获取 {category} {filename}"},
                {"label": "🧮 材料", "callback": f"/投影材料 {category} {filename}"}
            ],
            [
                {"label": "📄 详细信息", "callback": f"/投影信息 {category} {filename}"},
                {"label": "⬅️ 返回列表", "callback": f"/投影列表 {category}"}
            ],
            [
                {"label": "🏠 返回主菜单", "callback": "/投影"}
            ]
        ]

    def create_3d_buttons(self, category: str, filename: str) -> List[List[Dict[str, str]]]:
        """
        创建3D渲染操作按钮

        Args:
            category: 分类名称
            filename: 文件名

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        return [
            [
                {"label": "旋转动画", "callback": f"/投影3D {category} {filename} rotation"},
                {"label": "轨道动画", "callback": f"/投影3D {category} {filename} orbit"}
            ],
            [
                {"label": "缩放动画", "callback": f"/投影3D {category} {filename} zoom"},
                {"label": "自定义参数", "callback": f"/投影3D {category} {filename} rotation 48 80 45"}
            ],
            [
                {"label": "🖼️ 预览", "callback": f"/投影预览 {category} {filename}"},
                {"label": "🧮 材料", "callback": f"/投影材料 {category} {filename}"}
            ],
            [
                {"label": "📄 详细信息", "callback": f"/投影信息 {category} {filename}"},
                {"label": "⬅️ 返回列表", "callback": f"/投影列表 {category}"}
            ],
            [
                {"label": "🏠 返回主菜单", "callback": "/投影"}
            ]
        ]

    def create_material_buttons(self, category: str, filename: str) -> List[List[Dict[str, str]]]:
        """
        创建材料分析操作按钮

        Args:
            category: 分类名称
            filename: 文件名

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        return [
            [
                {"label": "📄 详细信息", "callback": f"/投影信息 {category} {filename}"},
                {"label": "🖼️ 预览", "callback": f"/投影预览 {category} {filename}"}
            ],
            [
                {"label": "🎬 3D渲染", "callback": f"/投影3D {category} {filename}"},
                {"label": "📥 获取", "callback": f"/投影获取 {category} {filename}"}
            ],
            [
                {"label": "⬅️ 返回列表", "callback": f"/投影列表 {category}"}
            ],
            [
                {"label": "🏠 返回主菜单", "callback": "/投影"}
            ]
        ]

    def create_main_menu_buttons(self) -> List[List[Dict[str, str]]]:
        """
        创建主菜单按钮

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        return [
            [
                {"label": "📋 查看分类列表", "callback": "/投影列表"}
            ],
            [
                {"label": "❓ 帮助", "callback": "/投影 help"}
            ]
        ]

    def create_category_list_buttons(self, categories: List[str]) -> List[List[Dict[str, str]]]:
        """
        创建分类列表按钮

        Args:
            categories: 分类列表

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        buttons_info = []
        current_row = []

        for i, category in enumerate(categories):
            # 每行最多放3个按钮
            if i > 0 and i % 3 == 0:
                buttons_info.append(current_row)
                current_row = []

            current_row.append({
                "label": f"{category}",
                "callback": f"/投影列表 {category}"
            })

        # 添加最后一行
        if current_row:
            buttons_info.append(current_row)

        # 添加帮助按钮
        buttons_info.append([
            {"label": "❓ 帮助", "callback": "/投影 help"}
        ])

        return buttons_info

    def create_file_list_buttons(self, category: str, files: List[str]) -> List[List[Dict[str, str]]]:
        """
        创建文件列表按钮

        Args:
            category: 分类名称
            files: 文件列表

        Returns:
            List[List[Dict[str, str]]]: 按钮信息
        """
        buttons_info = []

        # 为每个文件创建按钮
        for file in files:
            buttons_info.append([{"label": f"{file}", "callback": f"/投影信息 {category} {file}"}])

        # 添加上传按钮和返回按钮
        buttons_info.append([
            {"label": "📤 上传新文件", "callback": f"/投影 {category}"},
            {"label": "⬅️ 返回主菜单", "callback": "/投影"}
        ])

        return buttons_info
