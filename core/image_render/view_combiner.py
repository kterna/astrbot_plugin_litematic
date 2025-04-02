from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any, cast
from enum import Enum, auto
from PIL import Image, ImageDraw, ImageFont

from .interfaces import RenderContext


class LayoutType(Enum):
    """布局类型枚举"""
    VERTICAL = auto()        # 垂直布局
    HORIZONTAL = auto()      # 水平布局
    GRID = auto()            # 网格布局
    STACKED = auto()         # 堆叠布局
    CUSTOM_COMBINED = auto() # 自定义组合布局


class IViewLayout(ABC):
    """视图布局接口"""
    
    @abstractmethod
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        按照特定布局排列视图
        
        Args:
            views: 视图字典，键为视图名称，值为图像
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """布局名称"""
        pass


class VerticalLayout(IViewLayout):
    """垂直布局 - 将视图垂直排列"""
    
    def __init__(self, spacing: int = 0, align: str = 'center') -> None:
        """
        初始化垂直布局
        
        Args:
            spacing: 视图间距
            align: 对齐方式，可选 'left', 'center', 'right'
        """
        self.spacing = spacing
        self.align = align
    
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        垂直排列视图
        
        Args:
            views: 视图字典
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 计算总高度和最大宽度
        total_height = sum(view.height for view in views.values())
        total_height += self.spacing * (len(views) - 1)
        max_width = max(view.width for view in views.values())
        
        # 创建画布
        combined = Image.new('RGBA', (max_width, total_height), (0, 0, 0, 0))
        
        # 放置视图
        y_offset = 0
        for view_name, view in views.items():
            # 根据对齐方式计算x坐标
            if self.align == 'left':
                x_pos = 0
            elif self.align == 'right':
                x_pos = max_width - view.width
            else:  # center
                x_pos = (max_width - view.width) // 2
            
            combined.paste(view, (x_pos, y_offset), view)
            y_offset += view.height + self.spacing
        
        return combined
    
    @property
    def name(self) -> str:
        return "vertical"


class HorizontalLayout(IViewLayout):
    """水平布局 - 将视图水平排列"""
    
    def __init__(self, spacing: int = 0, align: str = 'middle') -> None:
        """
        初始化水平布局
        
        Args:
            spacing: 视图间距
            align: 对齐方式，可选 'top', 'middle', 'bottom'
        """
        self.spacing = spacing
        self.align = align
    
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        水平排列视图
        
        Args:
            views: 视图字典
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 计算总宽度和最大高度
        total_width = sum(view.width for view in views.values())
        total_width += self.spacing * (len(views) - 1)
        max_height = max(view.height for view in views.values())
        
        # 创建画布
        combined = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))
        
        # 放置视图
        x_offset = 0
        for view_name, view in views.items():
            # 根据对齐方式计算y坐标
            if self.align == 'top':
                y_pos = 0
            elif self.align == 'bottom':
                y_pos = max_height - view.height
            else:  # middle
                y_pos = (max_height - view.height) // 2
            
            combined.paste(view, (x_offset, y_pos), view)
            x_offset += view.width + self.spacing
        
        return combined
    
    @property
    def name(self) -> str:
        return "horizontal"


class GridLayout(IViewLayout):
    """网格布局 - 将视图按网格排列"""
    
    def __init__(self, rows: int = 2, cols: int = 2, 
                 h_spacing: int = 0, v_spacing: int = 0) -> None:
        """
        初始化网格布局
        
        Args:
            rows: 行数
            cols: 列数
            h_spacing: 水平间距
            v_spacing: 垂直间距
        """
        self.rows = rows
        self.cols = cols
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
    
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        网格排列视图
        
        Args:
            views: 视图字典
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        view_list = list(views.values())
        num_views = len(view_list)
        
        # 调整行列数
        if num_views < self.rows * self.cols:
            if num_views <= self.cols:
                self.rows = 1
                self.cols = num_views
            else:
                self.rows = (num_views + self.cols - 1) // self.cols
        
        # 计算单元格尺寸
        cell_width = max(view.width for view in view_list)
        cell_height = max(view.height for view in view_list)
        
        # 计算网格总尺寸
        grid_width = cell_width * self.cols + self.h_spacing * (self.cols - 1)
        grid_height = cell_height * self.rows + self.v_spacing * (self.rows - 1)
        
        # 创建画布
        combined = Image.new('RGBA', (grid_width, grid_height), (0, 0, 0, 0))
        
        # 放置视图
        for i, view in enumerate(view_list):
            if i >= self.rows * self.cols:
                break
                
            row = i // self.cols
            col = i % self.cols
            
            x = col * (cell_width + self.h_spacing)
            y = row * (cell_height + self.v_spacing)
            
            # 居中放置在单元格内
            x_offset = (cell_width - view.width) // 2
            y_offset = (cell_height - view.height) // 2
            
            combined.paste(view, (x + x_offset, y + y_offset), view)
        
        return combined
    
    @property
    def name(self) -> str:
        return "grid"


class StackedLayout(IViewLayout):
    """堆叠布局 - 将视图堆叠排列，可设置偏移"""
    
    def __init__(self, x_offset: int = 20, y_offset: int = 20, 
                 order: Optional[List[str]] = None) -> None:
        """
        初始化堆叠布局
        
        Args:
            x_offset: X轴偏移量
            y_offset: Y轴偏移量
            order: 视图叠放顺序，从下到上
        """
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.order = order
    
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        堆叠排列视图
        
        Args:
            views: 视图字典
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 确定视图顺序
        if self.order:
            ordered_views = []
            for name in self.order:
                if name in views:
                    ordered_views.append((name, views[name]))
            # 添加未指定顺序的视图
            for name, view in views.items():
                if name not in self.order:
                    ordered_views.append((name, view))
        else:
            ordered_views = list(views.items())
        
        # 计算总尺寸
        max_width = max(view.width for _, view in ordered_views)
        max_height = max(view.height for _, view in ordered_views)
        
        # 计算堆叠后的总尺寸
        total_width = max_width + self.x_offset * (len(ordered_views) - 1)
        total_height = max_height + self.y_offset * (len(ordered_views) - 1)
        
        # 创建画布
        combined = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        
        # 放置视图
        for i, (name, view) in enumerate(ordered_views):
            x = i * self.x_offset
            y = i * self.y_offset
            combined.paste(view, (x, y), view)
        
        return combined
    
    @property
    def name(self) -> str:
        return "stacked"


class CustomCombinedLayout(IViewLayout):
    """自定义组合布局 - 模拟原始3视图组合布局"""
    
    def __init__(self, spacing: int = 0, add_labels: bool = False) -> None:
        """
        初始化自定义组合布局
        
        Args:
            spacing: 视图间距
            add_labels: 是否添加标签
        """
        self.spacing = spacing
        self.add_labels = add_labels
    
    def arrange(self, views: Dict[str, Image.Image], context: RenderContext) -> Image.Image:
        """
        自定义排列视图
        
        Args:
            views: 视图字典，应包含'top_view'、'front_view'、'side_view'
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 获取各个视图
        top_view = views.get('top_view')
        front_view = views.get('front_view')
        side_view = views.get('side_view')
        
        if not all([top_view, front_view, side_view]):
            missing = []
            if not top_view: missing.append('top_view')
            if not front_view: missing.append('front_view')
            if not side_view: missing.append('side_view')
            raise ValueError(f"缺少必要的视图: {', '.join(missing)}")
        
        # 计算组合图像的尺寸
        max_width = max(top_view.width, front_view.width + side_view.width + self.spacing)
        height = top_view.height + max(front_view.height, side_view.height) + self.spacing
        
        # 创建组合图像
        combined = Image.new('RGBA', (max_width, height), (0, 0, 0, 0))
        
        # 添加标签
        if self.add_labels:
            draw = ImageDraw.Draw(combined)
            
            # 尝试加载字体，失败时使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except IOError:
                font = ImageFont.load_default()
            
            # 添加标签
            draw.text((5, 5), "俯视图", fill=(255, 255, 255), font=font)
            draw.text((5, top_view.height + self.spacing + 5), "正视图", fill=(255, 255, 255), font=font)
            draw.text((front_view.width + self.spacing + 5, top_view.height + self.spacing + 5), 
                     "侧视图", fill=(255, 255, 255), font=font)
        
        # 粘贴各个视图
        combined.paste(top_view, (0, 0), top_view)
        combined.paste(front_view, (0, top_view.height + self.spacing), front_view)
        combined.paste(side_view, (front_view.width + self.spacing, top_view.height + self.spacing), side_view)
        
        return combined
    
    @property
    def name(self) -> str:
        return "custom_combined"


class ViewCombiner:
    """视图组合器 - 组合多个视图"""
    
    def __init__(self) -> None:
        """初始化视图组合器"""
        self._layouts: Dict[str, IViewLayout] = {}
        
        # 注册默认布局
        self.register_layout(VerticalLayout())
        self.register_layout(HorizontalLayout())
        self.register_layout(GridLayout())
        self.register_layout(StackedLayout())
        self.register_layout(CustomCombinedLayout())
    
    def register_layout(self, layout: IViewLayout) -> None:
        """
        注册布局
        
        Args:
            layout: 布局实例
        """
        self._layouts[layout.name] = layout
    
    def get_layout(self, name: str) -> Optional[IViewLayout]:
        """
        获取布局
        
        Args:
            name: 布局名称
            
        Returns:
            布局实例
        """
        return self._layouts.get(name)
    
    def combine(self, views: Dict[str, Image.Image], layout_name: str = "custom_combined", 
                context: Optional[RenderContext] = None) -> Image.Image:
        """
        组合多个视图
        
        Args:
            views: 视图字典
            layout_name: 布局名称
            context: 渲染上下文
            
        Returns:
            组合后的图像
            
        Raises:
            ValueError: 布局不存在或缺少必要视图
        """
        if not context:
            context = RenderContext()
        
        layout = self.get_layout(layout_name)
        if not layout:
            raise ValueError(f"未找到名为 {layout_name} 的布局")
        
        return layout.arrange(views, context)
    
    def create_combined_view(self, top_view: Image.Image, front_view: Image.Image, 
                             side_view: Image.Image, layout_name: str = "custom_combined", 
                             context: Optional[RenderContext] = None) -> Image.Image:
        """
        创建组合视图的便捷方法
        
        Args:
            top_view: 俯视图
            front_view: 正视图
            side_view: 侧视图
            layout_name: 布局名称
            context: 渲染上下文
            
        Returns:
            组合后的图像
        """
        views = {
            'top_view': top_view,
            'front_view': front_view,
            'side_view': side_view
        }
        return self.combine(views, layout_name, context) 