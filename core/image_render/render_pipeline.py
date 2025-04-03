from typing import List, Dict, Any, Optional, Generic, TypeVar, Type, cast
from abc import abstractmethod

from .interfaces import IRenderPipeline, IRenderProcessor, RenderContext

T = TypeVar('T')  # 泛型类型变量
R = TypeVar('R')  # 处理器结果类型变量

class RenderPipeline(IRenderPipeline[T], Generic[T]):
    """
    渲染管道实现，用于协调多个渲染处理器的执行
    """
    
    def __init__(self) -> None:
        """初始化渲染管道"""
        self._processors: List[IRenderProcessor[Any]] = []
        self._processor_map: Dict[str, IRenderProcessor[Any]] = {}
    
    def add_processor(self, processor: IRenderProcessor[Any]) -> 'RenderPipeline[T]':
        """
        添加处理器到管道
        
        Args:
            processor: 渲染处理器
            
        Returns:
            管道实例（链式调用）
        """
        if processor.name in self._processor_map:
            raise ValueError(f"处理器名称重复: {processor.name}")
        
        self._processors.append(processor)
        self._processor_map[processor.name] = processor
        return self
    
    def remove_processor(self, name: str) -> bool:
        """
        从管道中移除处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            是否成功移除
        """
        if name not in self._processor_map:
            return False
        
        processor = self._processor_map[name]
        self._processors.remove(processor)
        del self._processor_map[name]
        return True
    
    def get_processor(self, name: str) -> Optional[IRenderProcessor[Any]]:
        """
        获取指定名称的处理器
        
        Args:
            name: 处理器名称
            
        Returns:
            处理器实例
        """
        return self._processor_map.get(name)
    
    def get_processors(self) -> List[IRenderProcessor[Any]]:
        """
        获取所有处理器
        
        Returns:
            处理器列表
        """
        return self._processors.copy()
    
    def execute(self, context: RenderContext) -> T:
        """
        执行渲染管道
        
        Args:
            context: 渲染上下文
            
        Returns:
            渲染结果
        """
        result: Any = None
        
        # 依次执行每个处理器
        for processor in self._processors:
            # 将上一个处理器的结果存入上下文
            if result is not None:
                context.set("last_result", result)
            
            # 执行当前处理器
            result = processor.process(context)
            
            # 将当前处理器的结果存入上下文
            context.set(f"result_{processor.name}", result)
        
        # 返回最终结果
        return cast(T, result)
    
    def clear(self) -> None:
        """清空管道中的所有处理器"""
        self._processors.clear()
        self._processor_map.clear()

class AbstractRenderProcessor(IRenderProcessor[R], Generic[R]):
    """
    渲染处理器抽象基类，提供基本实现
    """
    
    def __init__(self, name: str) -> None:
        """
        初始化渲染处理器
        
        Args:
            name: 处理器名称
        """
        self._name = name
    
    @property
    def name(self) -> str:
        """处理器名称"""
        return self._name
    
    @abstractmethod
    def process(self, context: RenderContext) -> R:
        """
        处理渲染上下文
        
        Args:
            context: 渲染上下文
            
        Returns:
            处理结果
        """
        pass 