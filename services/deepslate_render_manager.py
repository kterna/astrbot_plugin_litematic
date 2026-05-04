import base64
import math
import os
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Iterator, Optional, Tuple

from PIL import Image
from astrbot import logger
from litemapy import Schematic

from ..core.image_render.interfaces import RenderContext
from ..core.image_render.view_combiner import (
    CustomCombinedLayout,
    GridLayout,
    HorizontalLayout,
    StackedLayout,
    VerticalLayout,
)
from ..core.model_3d.model_builder import ModelBuilder
from ..core.render_3d.gif_exporter import GifExporter
from ..core.render_3d.texture_sampler import TextureSampler
from ..utils.config import Config
from ..utils.exceptions import RenderError


class DeepslateRenderManager:
    """使用 Deepslate + Chromium 渲染 Litematic 文件。"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.plugin_dir = Path(config.get_plugin_dir())
        self.worker_page = self.plugin_dir / "pages" / "render_worker" / "index.html"
        self.atlas_path = self.plugin_dir / "pages" / "webui" / "vendor" / "atlas.png"
        self.browser_executable = str(
            config.get_config_value("deepslate_browser_executable", "/usr/bin/chromium")
        )
        self.timeout_ms = int(config.get_config_value("deepslate_render_timeout_ms", 120000))
        self._native_texture_size: Optional[int] = None
        self._preview_texture_size: Optional[int] = None

    def is_available(self) -> bool:
        return self.worker_page.is_file() and os.path.exists(self.browser_executable)

    def render_litematic_image(
        self,
        file_path: str,
        view_type: str = "iso",
        window_size: Optional[Tuple[int, int]] = None,
    ) -> str:
        width, height = self._normalize_window_size(window_size, default=(1024, 768))
        with self._open_page(width, height) as page:
            self._load_litematic(page, file_path, width, height, view_type=view_type)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                output_path = tmp.name
            page.locator("#renderCanvas").screenshot(path=output_path, timeout=self.timeout_ms)
            return output_path

    def render_litematic_preview(
        self,
        file_path: str,
        view_type: str = "combined",
        layout: str = "",
        spacing: int = 0,
        add_labels: bool = False,
        use_block_models: bool = True,
    ) -> str:
        if not use_block_models:
            raise RenderError("Deepslate 预览不支持 nomodel 参数", code=3005)

        model_data = self._load_model_data(file_path)
        texture_size = self._get_preview_texture_size()
        normalized_view = (view_type or "combined").lower()
        views = self._preview_view_order(normalized_view)
        view_sizes = {
            view: self._preview_view_size(model_data, view, texture_size)
            for view in views
        }
        for width, height in view_sizes.values():
            self._ensure_preview_canvas_size(width, height)

        first_size = next(iter(view_sizes.values()))
        with self._open_page(*first_size) as page:
            self._load_litematic(page, file_path, first_size[0], first_size[1], view_type=views[0])
            rendered_views = {
                self._preview_view_key(view): self._render_preview_view(page, view, view_sizes[view])
                for view in views
            }

        image = self._combine_preview_views(
            rendered_views,
            normalized_view,
            layout,
            spacing,
            add_labels,
        )
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            output_path = tmp.name
        image.save(output_path, "PNG")
        return output_path

    def render_litematic_gif(
        self,
        file_path: str,
        animation_type: str = "rotation",
        frames: int = 36,
        duration: int = 100,
        elevation: float = 30.0,
        window_size: Optional[Tuple[int, int]] = None,
        native_textures: bool = False,
        native_max_size: Optional[Tuple[int, int]] = None,
    ) -> str:
        requested_size = self._resolve_gif_window_size(file_path, window_size, native_textures, native_max_size)
        exporter = GifExporter()
        resize_to = exporter.estimate_scaled_size(
            requested_size[0],
            requested_size[1],
            frames,
            int(self.config.get_config_value("max_gif_size_bytes", 5 * 1024 * 1024)),
        )
        width, height = self._normalize_window_size(resize_to or requested_size, default=(800, 600))
        with self._open_page(width, height) as page:
            self._load_litematic(page, file_path, width, height, view_type="iso")
            frame_iter = self._iter_frames(page, animation_type, frames, elevation)
            output_path = exporter.export_gif_with_temp_stream(frame_iter, duration=duration)
            if not output_path:
                raise RenderError("Deepslate GIF 导出失败", code=3004)
            return output_path

    def _open_page(self, width: int, height: int):
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise RenderError(f"Playwright 未安装或不可用: {exc}", code=3001)

        if not self.worker_page.is_file():
            raise RenderError(f"Deepslate 渲染页面不存在: {self.worker_page}", code=3002)
        if not os.path.exists(self.browser_executable):
            raise RenderError(f"Chromium 不存在: {self.browser_executable}", code=3003)

        manager = _PageContext(sync_playwright(), self.browser_executable, self.worker_page, width, height, self.timeout_ms)
        return manager

    def _load_litematic(self, page, file_path: str, width: int, height: int, view_type: str) -> dict:
        content = base64.b64encode(Path(file_path).read_bytes()).decode("ascii")
        return page.evaluate(
            """async ({ content, options }) => window.renderLitematicBase64(content, options)""",
            {
                "content": content,
                "options": {
                    "width": width,
                    "height": height,
                    "viewType": view_type,
                },
            },
        )

    def _iter_frames(self, page, animation_type: str, frames: int, elevation: float) -> Iterator[Image.Image]:
        for index in range(frames):
            options = self._frame_options(animation_type, index, frames, elevation)
            page.evaluate("options => window.renderFrame(options)", options)
            png_bytes = page.locator("#renderCanvas").screenshot(timeout=self.timeout_ms)
            image = Image.open(BytesIO(png_bytes)).convert("RGBA")
            yield image

    def _frame_options(self, animation_type: str, index: int, frames: int, elevation: float) -> dict:
        total = max(1, frames)
        progress = index / total
        angle = math.tau * progress
        elevation_rad = math.radians(elevation)

        if animation_type == "orbit":
            orbit_elevation = math.radians(90 * progress)
            return {
                "cameraMode": "legacy",
                "animationType": "orbit",
                "angle": angle,
                "elevation": orbit_elevation,
                "distanceFactor": 2,
                "fov": 30,
                "grid": False,
            }
        if animation_type == "zoom":
            factor = 3.0 + (1.5 - 3.0) * progress
            return {
                "cameraMode": "legacy",
                "animationType": "orbit",
                "angle": math.radians(45),
                "elevation": math.radians(30),
                "distanceFactor": factor,
                "fov": 30,
                "grid": False,
            }
        return {
            "cameraMode": "legacy",
            "animationType": "rotation",
            "angle": angle,
            "elevation": elevation_rad,
            "distanceFactor": 2,
            "fov": 30,
            "grid": False,
        }

    def _normalize_window_size(
        self,
        window_size: Optional[Tuple[int, int]],
        default: Tuple[int, int],
    ) -> Tuple[int, int]:
        if not window_size:
            return default
        return (
            max(64, min(int(window_size[0]), 4096)),
            max(64, min(int(window_size[1]), 4096)),
        )

    def _load_model_data(self, file_path: str) -> dict:
        schematic = Schematic.load(file_path)
        model_builder = ModelBuilder()
        if not model_builder.build_from_litematic(schematic):
            raise RenderError("构建投影尺寸信息失败", code=3006)
        return model_builder.get_model_data()

    def _get_preview_texture_size(self) -> int:
        if self._preview_texture_size is None:
            self._preview_texture_size = TextureSampler(
                self.config.get_resource_dir(),
                native_textures=False,
            ).texture_size
        return self._preview_texture_size

    def _preview_view_order(self, view_type: str) -> Tuple[str, ...]:
        if view_type in {"top", "front", "north", "side", "east", "south", "west"}:
            return (view_type,)
        if view_type != "combined":
            raise RenderError(f"不支持的视图类型: {view_type}", code=3007)
        return ("top", "front", "side")

    def _preview_view_key(self, view_type: str) -> str:
        if view_type == "top":
            return "top_view"
        if view_type in {"front", "north", "south"}:
            return "front_view"
        return "side_view"

    def _preview_view_size(self, model_data: dict, view_type: str, texture_size: int) -> Tuple[int, int]:
        dimensions = model_data.get("dimensions", {})
        width = max(1, int(dimensions.get("width", 1)))
        height = max(1, int(dimensions.get("height", 1)))
        length = max(1, int(dimensions.get("length", 1)))
        if view_type == "top":
            return (width * texture_size, length * texture_size)
        if view_type in {"front", "north", "south"}:
            return (width * texture_size, height * texture_size)
        return (length * texture_size, height * texture_size)

    def _ensure_preview_canvas_size(self, width: int, height: int) -> None:
        max_size = 4096
        if width > max_size or height > max_size:
            raise RenderError(
                f"Deepslate 预览画布 {width}x{height} 超过浏览器安全上限 {max_size}x{max_size}",
                code=3008,
            )

    def _render_preview_view(self, page, view_type: str, size: Tuple[int, int]) -> Image.Image:
        page.evaluate(
            "options => window.renderFrame(options)",
            {
                "width": size[0],
                "height": size[1],
                "viewType": view_type,
                "projection": "orthographic",
                "background": "transparent",
                "grid": False,
            },
        )
        png_bytes = page.locator("#renderCanvas").screenshot(timeout=self.timeout_ms, omit_background=True)
        return Image.open(BytesIO(png_bytes)).convert("RGBA")

    def _combine_preview_views(
        self,
        views: dict,
        view_type: str,
        layout: str,
        spacing: int,
        add_labels: bool,
    ) -> Image.Image:
        if view_type != "combined":
            return next(iter(views.values()))

        layout_name = (layout or "").lower()
        if layout_name in {"vertical", "v"}:
            combiner = VerticalLayout(spacing=spacing)
        elif layout_name in {"horizontal", "h"}:
            combiner = HorizontalLayout(spacing=spacing)
        elif layout_name in {"grid", "g"}:
            combiner = GridLayout(rows=2, cols=2, h_spacing=spacing, v_spacing=spacing)
        elif layout_name in {"stacked", "s"}:
            combiner = StackedLayout(x_offset=max(20, spacing), y_offset=max(20, spacing))
        else:
            combiner = CustomCombinedLayout(spacing=spacing, add_labels=add_labels)
        return combiner.arrange(views, RenderContext())

    def _resolve_gif_window_size(
        self,
        file_path: str,
        window_size: Optional[Tuple[int, int]],
        native_textures: bool,
        native_max_size: Optional[Tuple[int, int]],
    ) -> Tuple[int, int]:
        if window_size is not None:
            return self._normalize_window_size(window_size, default=(800, 600))
        if not native_textures:
            return (800, 600)

        try:
            schematic = Schematic.load(file_path)
            model_builder = ModelBuilder()
            if not model_builder.build_from_litematic(schematic):
                return (800, 600)
            return self._calculate_native_window_size(
                model_builder.get_model_data(),
                self._get_native_texture_size(),
                native_max_size,
            )
        except Exception as exc:
            logger.warning(f"Deepslate 原生分辨率估算失败，使用默认 800x600: {exc}")
            return (800, 600)

    def _get_native_texture_size(self) -> int:
        if self._native_texture_size is None:
            self._native_texture_size = TextureSampler(
                self.config.get_resource_dir(),
                native_textures=True,
            ).get_native_texture_size()
        return self._native_texture_size

    def _calculate_native_window_size(
        self,
        model_data: dict,
        texture_size: int,
        max_size: Optional[Tuple[int, int]] = None,
    ) -> Tuple[int, int]:
        dimensions = model_data.get("dimensions", {})
        width_blocks = max(1, int(dimensions.get("width", 1)))
        length_blocks = max(1, int(dimensions.get("length", 1)))
        height_blocks = max(1, int(dimensions.get("height", 1)))

        projected_width = width_blocks + length_blocks
        projected_height = height_blocks + max(width_blocks, length_blocks) * 0.5
        width = int(projected_width * texture_size)
        height = int(projected_height * texture_size)

        min_width, min_height = 800, 600
        default_max_size = 16384
        max_width, max_height = max_size if max_size else (default_max_size, default_max_size)
        max_width = max(min_width, max_width)
        max_height = max(min_height, max_height)
        return (
            max(min_width, min(width, max_width)),
            max(min_height, min(height, max_height)),
        )


class _PageContext:
    def __init__(
        self,
        playwright_context,
        browser_executable: str,
        worker_page: Path,
        width: int,
        height: int,
        timeout_ms: int,
    ) -> None:
        self.playwright_context = playwright_context
        self.browser_executable = browser_executable
        self.worker_page = worker_page
        self.width = width
        self.height = height
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self.playwright = self.playwright_context.__enter__()
        self.browser = self.playwright.chromium.launch(
            executable_path=self.browser_executable,
            headless=True,
            args=["--no-sandbox"],
        )
        self.context = self.browser.new_context(viewport={"width": self.width, "height": self.height})
        self.page = self.context.new_page()
        messages = []
        self.page.on("pageerror", lambda exc: messages.append(str(exc)))
        self.page.goto(self.worker_page.as_uri(), wait_until="networkidle", timeout=self.timeout_ms)
        self._inject_atlas_data_url()
        if messages:
            logger.warning(f"Deepslate 渲染页面加载警告: {messages[:3]}")
        return self.page

    def _inject_atlas_data_url(self) -> None:
        atlas_path = self.worker_page.parent.parent / "webui" / "vendor" / "atlas.png"
        if not atlas_path.is_file():
            return
        atlas_base64 = base64.b64encode(atlas_path.read_bytes()).decode("ascii")
        self.page.evaluate(
            """src => new Promise((resolve, reject) => {
                const image = document.getElementById("atlasImage");
                image.onload = () => resolve(true);
                image.onerror = () => reject(new Error("atlas data url load failed"));
                image.src = src;
            })""",
            f"data:image/png;base64,{atlas_base64}",
        )

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        finally:
            self.playwright_context.__exit__(exc_type, exc, tb)
