"""
定义插件使用的异常类层次结构
"""
from typing import Optional, Union, List, Dict, Any


class LitematicPluginError(Exception):
    """插件基础异常类"""
    
    def __init__(self, message: str = "插件操作失败", code: int = 1000, details: Optional[Dict[str, Any]] = None) -> None:
        """初始化异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 详细错误信息
        """
        self.message: str = message
        self.code: int = code
        self.details: Dict[str, Any] = details or {}
        super().__init__(self.message)


# 分类相关异常
class CategoryError(LitematicPluginError):
    """分类操作异常基类"""
    
    def __init__(self, message: str = "分类操作失败", code: int = 2000, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code, details)


class CategoryNotFoundError(CategoryError):
    """分类不存在异常"""
    
    def __init__(self, category: str, code: int = 2001, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"分类 {category} 不存在"
        super_details = {"category": category}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class CategoryCreateError(CategoryError):
    """创建分类失败异常"""
    
    def __init__(self, category: str, reason: str, code: int = 2002, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"创建分类 {category} 失败: {reason}"
        super_details = {"category": category, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class CategoryDeleteError(CategoryError):
    """删除分类失败异常"""
    
    def __init__(self, category: str, reason: str, code: int = 2003, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"删除分类 {category} 失败: {reason}"
        super_details = {"category": category, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class CategoryAlreadyExistsError(CategoryError):
    """分类已存在异常"""
    
    def __init__(self, category: str, code: int = 2004, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"分类 {category} 已存在"
        super_details = {"category": category}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


# 文件相关异常
class FileError(LitematicPluginError):
    """文件操作异常基类"""
    
    def __init__(self, message: str = "文件操作失败", code: int = 3000, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code, details)


class FileNotFoundError(FileError):
    """文件不存在异常"""
    
    def __init__(self, category: str, filename: str, code: int = 3001, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"在分类 {category} 下找不到文件 {filename}"
        super_details = {"category": category, "filename": filename}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class FileSaveError(FileError):
    """保存文件失败异常"""
    
    def __init__(self, filename: str, reason: str, code: int = 3002, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"保存文件 {filename} 失败: {reason}"
        super_details = {"filename": filename, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class FileDeleteError(FileError):
    """删除文件失败异常"""
    
    def __init__(self, category: str, filename: str, reason: str, code: int = 3003, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"删除文件 {filename} 失败: {reason}"
        super_details = {"category": category, "filename": filename, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class MultipleFilesFoundError(FileError):
    """找到多个匹配文件异常"""
    
    def __init__(self, category: str, pattern: str, matches: List[str], code: int = 3004, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"在分类 {category} 下找到多个与 {pattern} 匹配的文件"
        super_details = {"category": category, "pattern": pattern, "matches": matches}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


# 渲染相关异常
class RenderError(LitematicPluginError):
    """渲染相关异常基类"""
    
    def __init__(self, message: str = "渲染失败", code: int = 4000, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code, details)


class TextureNotFoundError(RenderError):
    """材质不存在异常"""
    
    def __init__(self, texture_name: str, code: int = 4001, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"找不到材质 {texture_name}"
        super_details = {"texture_name": texture_name}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class InvalidViewTypeError(RenderError):
    """无效的视图类型异常"""
    
    def __init__(self, message: str = "无效的视图类型", code: int = 4002, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code, details)


# 配置相关异常
class ConfigError(LitematicPluginError):
    """配置相关异常基类"""
    
    def __init__(self, message: str = "配置错误", code: int = 5000, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, code, details)


class ConfigLoadError(ConfigError):
    """配置加载失败异常"""
    
    def __init__(self, config_name: str, reason: str, code: int = 5001, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"加载配置 {config_name} 失败: {reason}"
        super_details = {"config_name": config_name, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class ConfigSaveError(ConfigError):
    """配置保存失败异常"""
    
    def __init__(self, config_name: str, reason: str, code: int = 5002, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"保存配置 {config_name} 失败: {reason}"
        super_details = {"config_name": config_name, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


# 通用业务逻辑异常
class InvalidOperationError(LitematicPluginError):
    """无效操作异常"""
    
    def __init__(self, operation: str, reason: str, code: int = 6001, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"无效操作 {operation}: {reason}"
        super_details = {"operation": operation, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details)


class InvalidArgumentError(LitematicPluginError):
    """无效参数异常"""
    
    def __init__(self, argument: str, reason: str, code: int = 6002, details: Optional[Dict[str, Any]] = None) -> None:
        message = f"无效参数 {argument}: {reason}"
        super_details = {"argument": argument, "reason": reason}
        if details:
            super_details.update(details)
        super().__init__(message, code, super_details) 