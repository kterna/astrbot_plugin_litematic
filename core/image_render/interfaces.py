from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, List, TypeVar, Generic, Callable
from PIL import Image

# 类型别名
BoundsType = Tuple[int, int, int, int, int, int]  # min_x, max_x, min_y, max_y, min_z, max_z

class RenderContext:
    """简化的渲染上下文，用于在渲染过程中传递数据"""
    
    def __init__(self) -> None:
        """初始化渲染上下文"""
        self._data: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据，如不存在返回默认值"""
        return self._data.get(key, default)
    
    def has(self, key: str) -> bool:
        """检查上下文是否包含指定键"""
        return key in self._data
    
    def remove(self, key: str) -> None:
        """移除上下文数据"""
        if key in self._data:
            del self._data[key]
    
    def clear(self) -> None:
        """清空上下文数据"""
        self._data.clear()

# 使用泛型类型变量T
T = TypeVar('T')

class IRenderProcessor(Generic[T]):
    """渲染处理器接口，定义单个渲染步骤"""
    
    @abstractmethod
    def process(self, context: RenderContext) -> T:
        """处理渲染上下文并返回结果"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """处理器名称"""
        pass

class IRenderPipeline(Generic[T]):
    """简化的渲染管道接口"""
    
    @abstractmethod
    def add_processor(self, processor: IRenderProcessor[Any]) -> 'IRenderPipeline[T]':
        """添加处理器到管道"""
        pass
    
    @abstractmethod
    def execute(self, context: RenderContext) -> T:
        """执行渲染管道并返回结果"""
        pass 