from typing import Dict, Any, List, Tuple, Optional, cast
from PIL import Image

from .interfaces import RenderContext
from .render_pipeline import AbstractRenderProcessor
from .texture_manager import TextureManager
from .build_model import World, Block
from .model_loader import ModelLoader
from .model_renderer import ModelRenderer

class BoundsCalculatorProcessor(AbstractRenderProcessor[Tuple[int, int, int, int, int, int]]):
    """计算结构边界的处理器"""
    
    def __init__(self) -> None:
        """初始化边界计算处理器"""
        super().__init__("bounds_calculator")
    
    def process(self, context: RenderContext) -> Tuple[int, int, int, int, int, int]:
        """
        计算结构边界
        
        Args:
            context: 渲染上下文，必须包含world对象
            
        Returns:
            结构边界坐标 (min_x, max_x, min_y, max_y, min_z, max_z)
        """
        world = cast(World, context.get("world"))
        if not world:
            raise ValueError("上下文中缺少world对象")
        
        if not world.blocks:
            return (0, 0, 0, 0, 0, 0)
        
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        for block in world.blocks:
            x, y, z = block.position
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            min_z = min(min_z, z)
            max_z = max(max_z, z)
        
        bounds = (int(min_x), int(max_x), int(min_y), int(max_y), int(min_z), int(max_z))
        context.set("bounds", bounds)
        return bounds


class TextureLoaderProcessor(AbstractRenderProcessor[TextureManager]):
    """加载纹理的处理器"""
    
    def __init__(self, resource_base_path: str, texture_path: Optional[str] = None, 
                texture_size: Optional[int] = None) -> None:
        """
        初始化纹理加载处理器
        
        Args:
            resource_base_path: 资源基础路径
            texture_path: 纹理路径
            texture_size: 纹理大小
        """
        super().__init__("texture_loader")
        self.resource_base_path = resource_base_path
        self.texture_path = texture_path
        self.texture_size = texture_size
    
    def process(self, context: RenderContext) -> TextureManager:
        """
        加载纹理
        
        Args:
            context: 渲染上下文
            
        Returns:
            纹理管理器
        """
        # 创建纹理管理器或从上下文获取
        texture_manager = context.get("texture_manager")
        if not texture_manager:
            texture_manager = TextureManager(
                self.resource_base_path, 
                self.texture_path, 
                self.texture_size
            )
            context.set("texture_manager", texture_manager)
        
        return texture_manager


class TopViewProcessor(AbstractRenderProcessor[Image.Image]):
    """俯视图渲染处理器"""
    
    def __init__(self) -> None:
        """初始化俯视图渲染处理器"""
        super().__init__("top_view")
    
    def process(self, context: RenderContext) -> Image.Image:
        """
        渲染俯视图
        
        Args:
            context: 渲染上下文，必须包含world、texture_manager、bounds对象
            
        Returns:
            渲染后的图像
        """
        world = cast(World, context.get("world"))
        texture_manager = cast(TextureManager, context.get("texture_manager"))
        bounds = cast(Tuple[int, int, int, int, int, int], context.get("bounds"))
        scale = cast(int, context.get("scale", 1))
        use_block_models = cast(bool, context.get("use_block_models", True))
        model_renderer = context.get("model_renderer")
        
        if not world or not texture_manager or not bounds:
            raise ValueError("上下文中缺少必要对象")
        
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        
        # 创建图像
        width = (max_x - min_x + 1) * texture_manager.texture_size
        height = (max_z - min_z + 1) * texture_manager.texture_size
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 获取顶视图可见方块
        visible_blocks: List[Tuple[int, int, Block]] = []
        for block in world.blocks:
            x, y, z = block.position
            # 检查是否是顶层方块
            is_top = True
            for other_block in world.blocks:
                ox, oy, oz = other_block.position
                if ox == x and oz == z and oy > y:
                    is_top = False
                    break
            if is_top:
                visible_blocks.append((x, z, block))
        
        # 渲染方块
        for x, z, block in visible_blocks:
            pos_x = (x - min_x) * texture_manager.texture_size
            pos_z = (z - min_z) * texture_manager.texture_size
            
            # 尝试使用模型渲染
            block_image = None
            if use_block_models and model_renderer and hasattr(block, "model_data") and block.model_data:
                # 在这里复制model_data，并添加facing属性
                model_data = dict(block.model_data)
                if block.facing:
                    model_data["facing"] = block.facing
                block_image = model_renderer.render_model_face(model_data, "up")
            
            # 如果模型渲染失败，使用传统纹理
            if block_image is None:
                face = block.get_texture_face('top')
                block_image = texture_manager.get_texture(block.name, face)
            
            # 贴到图像上
            image.paste(block_image, (pos_x, pos_z), block_image)
        
        # 缩放图像
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class FrontViewProcessor(AbstractRenderProcessor[Image.Image]):
    """正视图渲染处理器"""
    
    def __init__(self) -> None:
        """初始化正视图渲染处理器"""
        super().__init__("front_view")
    
    def process(self, context: RenderContext) -> Image.Image:
        """
        渲染正视图
        
        Args:
            context: 渲染上下文，必须包含world、texture_manager、bounds对象
            
        Returns:
            渲染后的图像
        """
        world = cast(World, context.get("world"))
        texture_manager = cast(TextureManager, context.get("texture_manager"))
        bounds = cast(Tuple[int, int, int, int, int, int], context.get("bounds"))
        scale = cast(int, context.get("scale", 1))
        z_position = context.get("front_z")
        use_block_models = cast(bool, context.get("use_block_models", True))
        model_renderer = context.get("model_renderer")
        
        if not world or not texture_manager or not bounds:
            raise ValueError("上下文中缺少必要对象")
        
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        
        # 如果没有指定z位置，使用最小z
        if z_position is None:
            z_position = min_z
        
        # 创建图像
        width = (max_x - min_x + 1) * texture_manager.texture_size
        height = (max_y - min_y + 1) * texture_manager.texture_size
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 获取正视图可见方块
        visible_blocks: List[Tuple[int, int, Block]] = []
        for block in world.blocks:
            x, y, z = block.position
            # 检查是否是最前层方块
            if z == z_position:
                visible_blocks.append((x, y, block))
            
        # 渲染方块
        for x, y, block in visible_blocks:
            pos_x = (x - min_x) * texture_manager.texture_size
            pos_y = (max_y - y) * texture_manager.texture_size - texture_manager.texture_size
            
            # 尝试使用模型渲染
            block_image = None
            if use_block_models and model_renderer and hasattr(block, "model_data") and block.model_data:
                # 在这里复制model_data，并添加facing属性
                model_data = dict(block.model_data)
                if block.facing:
                    model_data["facing"] = block.facing
                block_image = model_renderer.render_model_face(model_data, "north")
            
            # 如果模型渲染失败，使用传统纹理
            if block_image is None:
                face = block.get_texture_face('front')
                block_image = texture_manager.get_texture(block.name, face)
            
            # 贴到图像上
            image.paste(block_image, (pos_x, pos_y), block_image)
        
        # 缩放图像
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class SideViewProcessor(AbstractRenderProcessor[Image.Image]):
    """侧视图渲染处理器"""
    
    def __init__(self) -> None:
        """初始化侧视图渲染处理器"""
        super().__init__("side_view")
    
    def process(self, context: RenderContext) -> Image.Image:
        """
        渲染侧视图
        
        Args:
            context: 渲染上下文，必须包含world、texture_manager、bounds对象
            
        Returns:
            渲染后的图像
        """
        world = cast(World, context.get("world"))
        texture_manager = cast(TextureManager, context.get("texture_manager"))
        bounds = cast(Tuple[int, int, int, int, int, int], context.get("bounds"))
        scale = cast(int, context.get("scale", 1))
        x_position = context.get("side_x")
        use_block_models = cast(bool, context.get("use_block_models", True))
        model_renderer = context.get("model_renderer")
        
        if not world or not texture_manager or not bounds:
            raise ValueError("上下文中缺少必要对象")
        
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        
        # 如果没有指定x位置，使用最大x
        if x_position is None:
            x_position = max_x
        
        # 创建图像
        width = (max_z - min_z + 1) * texture_manager.texture_size
        height = (max_y - min_y + 1) * texture_manager.texture_size
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 获取侧视图可见方块
        visible_blocks: List[Tuple[int, int, Block]] = []
        for block in world.blocks:
            x, y, z = block.position
            # 检查是否是最侧面方块
            if x == x_position:
                visible_blocks.append((z, y, block))
            
        # 渲染方块
        for z, y, block in visible_blocks:
            pos_z = (z - min_z) * texture_manager.texture_size
            pos_y = (max_y - y) * texture_manager.texture_size - texture_manager.texture_size
            
            # 尝试使用模型渲染
            block_image = None
            if use_block_models and model_renderer and hasattr(block, "model_data") and block.model_data:
                # 在这里复制model_data，并添加facing属性
                model_data = dict(block.model_data)
                if block.facing:
                    model_data["facing"] = block.facing
                block_image = model_renderer.render_model_face(model_data, "east")
            
            # 如果模型渲染失败，使用传统纹理
            if block_image is None:
                face = block.get_texture_face('side')
                block_image = texture_manager.get_texture(block.name, face)
            
            # 贴到图像上
            image.paste(block_image, (pos_z, pos_y), block_image)
        
        # 缩放图像
        if scale != 1:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.NEAREST)
        
        return image


class ViewCombinerProcessor(AbstractRenderProcessor[Image.Image]):
    """视图组合处理器"""
    
    def __init__(self, layout_name: str = "custom_combined", add_labels: bool = False) -> None:
        """初始化视图组合处理器
        
        Args:
            layout_name: 布局名称，默认为"custom_combined"
            add_labels: 是否添加标签
        """
        super().__init__("view_combiner")
        self.layout_name = layout_name
        self.add_labels = add_labels
        
        # 导入视图组合器
        from .view_combiner import ViewCombiner, CustomCombinedLayout
        self.view_combiner = ViewCombiner()
        
        # 如果需要标签，替换默认布局
        if self.add_labels:
            self.view_combiner.register_layout(CustomCombinedLayout(spacing=0, add_labels=True))
    
    def process(self, context: RenderContext) -> Image.Image:
        """
        组合多个视图
        
        Args:
            context: 渲染上下文，必须包含top_view、front_view、side_view三个图像
            
        Returns:
            组合后的图像
        """
        # 尝试从上下文获取视图
        top_view = context.get("result_top_view") 
        front_view = context.get("result_front_view")
        side_view = context.get("result_side_view")
        
        # 如果上下文中没有处理结果，尝试使用视图处理器生成
        if not top_view:
            top_processor = cast(Optional[TopViewProcessor], context.get("processor_top_view"))
            if top_processor:
                top_view = top_processor.process(context)
                context.set("result_top_view", top_view)
        
        if not front_view:
            front_processor = cast(Optional[FrontViewProcessor], context.get("processor_front_view"))
            if front_processor:
                front_view = front_processor.process(context)
                context.set("result_front_view", front_view)
        
        if not side_view:
            side_processor = cast(Optional[SideViewProcessor], context.get("processor_side_view"))
            if side_processor:
                side_view = side_processor.process(context)
                context.set("result_side_view", side_view)
        
        # 验证是否有所有必要的视图
        if not top_view or not front_view or not side_view:
            missing = []
            if not top_view: missing.append('top_view')
            if not front_view: missing.append('front_view')
            if not side_view: missing.append('side_view')
            raise ValueError(f"上下文中缺少必要的视图: {', '.join(missing)}")
        
        # 使用视图组合器组合视图
        views = {
            'top_view': top_view,
            'front_view': front_view,
            'side_view': side_view
        }
        
        # 添加额外的视图（如果有）
        for key, value in context._data.items():
            if key.startswith("result_") and key not in [
                "result_top_view", "result_front_view", "result_side_view"
            ] and isinstance(value, Image.Image):
                views[key.replace("result_", "")] = value
        
        # 组合视图
        return self.view_combiner.combine(views, self.layout_name, context)


class ModelRendererProcessor(AbstractRenderProcessor[Any]):
    """模型渲染处理器，用于加载和准备方块模型数据"""
    
    def __init__(self) -> None:
        """初始化模型渲染处理器"""
        super().__init__("model_renderer")
    
    def process(self, context: RenderContext) -> Any:
        """
        处理渲染上下文，应用模型渲染
        
        Args:
            context: 渲染上下文
            
        Returns:
            RenderContext: 处理后的上下文
        """
        # 获取必要数据
        world = context.get("world")
        texture_manager = context.get("texture_manager")
        resource_dir = context.get("resource_dir", "./resource")
        use_block_models = context.get("use_block_models", True)
        
        if not use_block_models or not world or not texture_manager:
            return context
        
        # 创建模型加载器
        model_loader = ModelLoader(resource_dir)
        context.set("model_loader", model_loader)
        
        # 创建模型渲染器
        model_renderer = ModelRenderer(texture_manager)
        context.set("model_renderer", model_renderer)
        
        # 为每个方块加载模型
        for block in world.blocks:
            if not hasattr(block, "model_data") or block.model_data is None:
                block.model_data = model_loader.load_model(block.name)
        
        return context 