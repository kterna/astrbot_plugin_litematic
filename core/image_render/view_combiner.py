from enum import Enum, auto
from typing import List, Dict, Any, Optional
from PIL import Image

class LayoutType(Enum):
    """布局类型枚举"""
    VERTICAL = "vertical"      # 垂直布局
    HORIZONTAL = "horizontal"  # 水平布局
    GRID = "grid"              # 网格布局
    STACKED = "stacked"        # 堆叠布局
    CUSTOM_COMBINED = "custom_combined" # 自定义组合布局

class ViewCombiner:
    """简化的视图组合器"""
    
    def __init__(self) -> None:
        """初始化视图组合器"""
        self.default_layout = "custom_combined"
    
    def combine_views(self, views: List[Image.Image], layout_type: str = "custom_combined", 
                spacing: int = 0, align: str = "center") -> Image.Image:
        """
        组合多个视图
        
        Args:
            views: 要组合的视图列表
            layout_type: 布局类型
            spacing: 视图间距
            align: 对齐方式
            
        Returns:
            组合后的图像
        """
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 选择布局类型
        layout_type = layout_type.lower()
        if layout_type == "vertical":
            return self._arrange_vertical(views, spacing, align)
        elif layout_type == "horizontal":
            return self._arrange_horizontal(views, spacing, align)
        elif layout_type == "grid":
            return self._arrange_grid(views, spacing)
        elif layout_type == "stacked":
            return self._arrange_stacked(views, 20, 20)
        else:  # default to custom_combined
            return self._arrange_custom_combined(views, spacing)
    
    def _arrange_vertical(self, views: List[Image.Image], spacing: int = 0, 
                         align: str = "center") -> Image.Image:
        """垂直排列视图"""
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 计算总高度和最大宽度
        total_height = sum(view.height for view in views)
        total_height += spacing * (len(views) - 1)
        max_width = max(view.width for view in views)
        
        # 创建画布
        combined = Image.new('RGBA', (max_width, total_height), (0, 0, 0, 0))
        
        # 放置视图
        y_offset = 0
        for view in views:
            # 根据对齐方式计算x坐标
            if align == 'left':
                x_pos = 0
            elif align == 'right':
                x_pos = max_width - view.width
            else:  # center
                x_pos = (max_width - view.width) // 2
            
            combined.paste(view, (x_pos, y_offset), view)
            y_offset += view.height + spacing
        
        return combined
    
    def _arrange_horizontal(self, views: List[Image.Image], spacing: int = 0, 
                           align: str = "middle") -> Image.Image:
        """水平排列视图"""
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 计算总宽度和最大高度
        total_width = sum(view.width for view in views)
        total_width += spacing * (len(views) - 1)
        max_height = max(view.height for view in views)
        
        # 创建画布
        combined = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))
        
        # 放置视图
        x_offset = 0
        for view in views:
            # 根据对齐方式计算y坐标
            if align == 'top':
                y_pos = 0
            elif align == 'bottom':
                y_pos = max_height - view.height
            else:  # middle
                y_pos = (max_height - view.height) // 2
            
            combined.paste(view, (x_offset, y_pos), view)
            x_offset += view.width + spacing
        
        return combined
    
    def _arrange_grid(self, views: List[Image.Image], spacing: int = 0) -> Image.Image:
        """网格排列视图"""
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        num_views = len(views)
        
        # 确定行列数
        if num_views <= 2:
            rows, cols = 1, num_views
        else:
            rows = cols = int(num_views ** 0.5 + 0.5)  # 取最接近平方根的整数
            if rows * cols < num_views:
                cols += 1
        
        # 计算单元格尺寸
        cell_width = max(view.width for view in views)
        cell_height = max(view.height for view in views)
        
        # 创建画布
        total_width = cols * cell_width + (cols - 1) * spacing
        total_height = rows * cell_height + (rows - 1) * spacing
        combined = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        
        # 放置视图
        for i, view in enumerate(views):
            if i >= rows * cols:
                break
                
            row = i // cols
            col = i % cols
            
            x = col * (cell_width + spacing) + (cell_width - view.width) // 2
            y = row * (cell_height + spacing) + (cell_height - view.height) // 2
            
            combined.paste(view, (x, y), view)
        
        return combined
    
    def _arrange_stacked(self, views: List[Image.Image], x_offset: int = 20, 
                        y_offset: int = 20) -> Image.Image:
        """堆叠排列视图"""
        if not views:
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        
        # 计算总尺寸
        width = max(view.width for view in views) + x_offset * (len(views) - 1)
        height = max(view.height for view in views) + y_offset * (len(views) - 1)
        
        # 创建画布
        combined = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # 反向放置视图（后面的视图在下面）
        for i, view in enumerate(reversed(views)):
            x = x_offset * i
            y = y_offset * i
            combined.paste(view, (x, y), view)
        
        return combined
    
    def _arrange_custom_combined(self, views: List[Image.Image], spacing: int = 0) -> Image.Image:
        """自定义组合布局（默认布局）"""
        if len(views) < 3:
            return self._arrange_vertical(views, spacing)
        
        # 假设视图顺序为：顶视图、正视图、侧视图
        top_view = views[0]
        front_view = views[1]
        side_view = views[2]
        
        # 计算布局尺寸
        total_width = max(top_view.width, front_view.width + side_view.width + spacing)
        total_height = top_view.height + spacing + max(front_view.height, side_view.height)
        
        # 创建画布
        combined = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
        
        # 放置顶视图
        top_x = (total_width - top_view.width) // 2
        combined.paste(top_view, (top_x, 0), top_view)
        
        # 放置正视图
        front_y = top_view.height + spacing
        combined.paste(front_view, (0, front_y), front_view)
        
        # 放置侧视图
        side_x = front_view.width + spacing
        side_y = top_view.height + spacing
        combined.paste(side_view, (side_x, side_y), side_view)
        
        return combined 