from typing import Dict, List, Tuple, Optional, Union, TypedDict, Any, AsyncGenerator, Literal

# 基本类型别名
CategoryType = str
FilePath = str
BlockId = str
RegionName = str

# 坐标相关类型
Coordinate = int
Position = Tuple[Coordinate, Coordinate, Coordinate]
BlockPosition = Position  # x, y, z坐标

# 方块映射类型
BlockMap = Dict[int, Dict[int, Dict[int, Any]]]  # 三维坐标索引到方块的映射

# 状态跟踪相关类型
class UploadStatus(TypedDict):
    """上传状态类型定义"""
    category: str
    expire_time: float

UserKey = str  # 用户标识，通常为 session_id + sender_id

# 方块统计相关类型
BlockCounts = Dict[BlockId, int]
EntityCounts = Dict[str, int]

# 消息回复类型
MessageResponse = AsyncGenerator[Any, None]

# 配置相关类型
class ResourcePack(TypedDict):
    """资源包配置类型"""
    name: str
    path: str
    texture_size: int

# 文件信息类型
class FileInfo(TypedDict):
    """文件信息类型"""
    name: str
    path: str
    category: str

# 模型数据结构
BlockModelElement = Dict[str, Any]  # 表示模型中的一个几何元素
BlockModelFace = Dict[str, Any]     # 表示元素的一个面
BlockModelData = Dict[str, Any]     # 整个模型数据

# 渲染相关类型
ViewType = Literal["top", "front", "side", "north", "south", "east", "west", "combined"]
LayoutType = Literal["vertical", "horizontal", "grid", "stacked", "combined", "v", "h", "g", "s", "c"] 