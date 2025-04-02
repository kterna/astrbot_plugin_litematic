"""
工具模块，包含各种通用工具函数和类
"""

from .config import Config
from .types import (
    CategoryType, FilePath, BlockId, RegionName, 
    Coordinate, Position, BlockPosition, BlockMap,
    UploadStatus, UserKey, BlockCounts, EntityCounts,
    MessageResponse, ResourcePack, FileInfo
)
from .exceptions import (
    LitematicPluginError,
    # 分类异常
    CategoryError, CategoryNotFoundError, CategoryCreateError,
    CategoryDeleteError, CategoryAlreadyExistsError,
    # 文件异常
    FileError, FileNotFoundError, FileSaveError,
    FileDeleteError, MultipleFilesFoundError,
    # 渲染异常
    RenderError, TextureNotFoundError, InvalidViewTypeError,
    # 配置异常
    ConfigError, ConfigLoadError, ConfigSaveError,
    # 通用异常
    InvalidOperationError, InvalidArgumentError
)
from .logging_utils import (
    log_error, log_exception, log_operation
)

__all__ = [
    'Config',
    # 类型别名
    'CategoryType', 'FilePath', 'BlockId', 'RegionName',
    'Coordinate', 'Position', 'BlockPosition', 'BlockMap',
    'UploadStatus', 'UserKey', 'BlockCounts', 'EntityCounts',
    'MessageResponse', 'ResourcePack', 'FileInfo',
    # 异常类
    'LitematicPluginError',
    'CategoryError', 'CategoryNotFoundError', 'CategoryCreateError',
    'CategoryDeleteError', 'CategoryAlreadyExistsError',
    'FileError', 'FileNotFoundError', 'FileSaveError',
    'FileDeleteError', 'MultipleFilesFoundError',
    'RenderError', 'TextureNotFoundError', 'InvalidViewTypeError',
    'ConfigError', 'ConfigLoadError', 'ConfigSaveError',
    'InvalidOperationError', 'InvalidArgumentError',
    # 日志工具
    'log_error', 'log_exception', 'log_operation'
] 