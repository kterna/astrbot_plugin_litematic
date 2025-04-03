from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List, TypeVar, Generic, Callable
from PIL import Image

# 类型别名
BoundsType = Tuple[int, int, int, int, int, int]  # min_x, max_x, min_y, max_y, min_z, max_z

class IRenderer(ABC):
    """渲染器接口，定义渲染功能的基本接口"""
    
    @abstractmethod
    def render_top_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                       min_z: Optional[int] = None, max_z: Optional[int] = None, 
                       scale: int = 1) -> Image.Image:
        """渲染俯视图（从上向下看）"""
        pass
    
    @abstractmethod
    def render_front_view(self, min_x: Optional[int] = None, max_x: Optional[int] = None, 
                          min_y: Optional[int] = None, max_y: Optional[int] = None, 
                          z: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染正视图（从前向后看）"""
        pass
    
    @abstractmethod
    def render_side_view(self, min_z: Optional[int] = None, max_z: Optional[int] = None, 
                        min_y: Optional[int] = None, max_y: Optional[int] = None, 
                        x: Optional[int] = None, scale: int = 1) -> Image.Image:
        """渲染侧视图（从侧面看）"""
        pass
    
    @abstractmethod
    def render_all_views(self, scale: int = 1) -> Image.Image:
        """渲染所有视图（俯视图、正视图、侧视图）并拼接成一个图像"""
        pass
    
    @abstractmethod
    def get_structure_bounds(self) -> BoundsType:
        """获取结构的边界坐标"""
        pass


class IImageSaver(ABC):
    """图像保存接口，定义图像保存的基本接口"""
    
    @abstractmethod
    def save_image(self, image: Image.Image, output_path: str, format: str = 'PNG') -> bool:
        """保存图像到文件"""
        pass 

# 以下是渲染管道相关接口

T = TypeVar('T')  # 定义泛型类型变量

class RenderContext:
    """渲染上下文，用于在渲染管道中传递状态和数据"""
    
    def __init__(self) -> None:
        """初始化渲染上下文"""
        self._data: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> None:
        """
        设置上下文数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            数据值
        """
        return self._data.get(key, default)
    
    def has(self, key: str) -> bool:
        """
        检查上下文是否包含指定键
        
        Args:
            key: 数据键
            
        Returns:
            是否包含
        """
        return key in self._data
    
    def remove(self, key: str) -> None:
        """
        移除上下文数据
        
        Args:
            key: 数据键
        """
        if key in self._data:
            del self._data[key]
    
    def clear(self) -> None:
        """清空上下文数据"""
        self._data.clear()


class IRenderProcessor(Generic[T]):
    """渲染处理器接口，定义渲染管道中的处理步骤"""
    
    @abstractmethod
    def process(self, context: RenderContext) -> T:
        """
        处理渲染上下文
        
        Args:
            context: 渲染上下文
            
        Returns:
            处理结果
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """处理器名称"""
        pass


class IRenderPipeline(Generic[T]):
    """渲染管道接口，定义渲染管道的基本行为"""
    
    @abstractmethod
    def add_processor(self, processor: IRenderProcessor[Any]) -> 'IRenderPipeline[T]':
        """
        添加处理器到管道
        
        Args:
            processor: 渲染处理器
            
        Returns:
            管道实例（链式调用）
        """
        pass
    
    @abstractmethod
    def remove_processor(self, name: str) -> bool:
        """
        从管道中移除处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否成功移除
        """
        pass
    
    @abstractmethod
    def execute(self, context: RenderContext) -> T:
        """
        执行渲染管道
        
        Args:
            context: 渲染上下文
            
        Returns:
            渲染结果
        """
        pass 