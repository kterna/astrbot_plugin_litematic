import os
import json
from typing import Any, Dict, List, Optional, Union
from astrbot import logger
from astrbot.api.star import Context
from astrbot.core.star.star_tools import StarTools
from astrbot.core import AstrBotConfig

class Config:
    """配置管理类，负责管理插件配置"""
    
    def __init__(self, context: Optional[Context] = None, astrbot_config: Optional[AstrBotConfig] = None) -> None:
        """初始化配置管理器

        Args:
            context: AstrBot上下文对象
            astrbot_config: AstrBot配置对象
        """
        self.context: Optional[Context] = context
        self.astrbot_config: Optional[AstrBotConfig] = astrbot_config
        
        # 通过文件路径确定插件目录，避免使用context.get_plugin_dir()
        self.plugin_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 使用StarTools的get_data_dir方法获取插件数据目录
        data_dir = StarTools.get_data_dir("litematic")
        self.litematic_dir: str = str(data_dir)
        
        # 设置分类配置文件路径
        self.categories_file: str = os.path.join(self.litematic_dir, "litematic_categories.json")
        
        # 创建必要的目录
        os.makedirs(self.litematic_dir, exist_ok=True)

        # 从 astrbot_config 加载配置（如果可用），否则使用默认值
        if self.astrbot_config:
            self.default_config: Dict[str, Union[List[str], int, str, bool]] = {
                "default_categories": ["建筑", "红石"],
                "upload_timeout": self.astrbot_config.get("upload_timeout", 300),
                "temp_dir": os.path.join(self.plugin_dir, "temp"),
                "max_workers": self.astrbot_config.get("max_workers", 3),
                "resource_dir": os.path.join(self.plugin_dir, "resource"),
                "use_block_models": self.astrbot_config.get("use_block_models", True),
                "max_gif_size_bytes": self.astrbot_config.get("max_gif_size_bytes", 5 * 1024 * 1024)
            }
        else:
            # 默认配置（向后兼容）
            self.default_config: Dict[str, Union[List[str], int, str, bool]] = {
                "default_categories": ["建筑", "红石"],
                "upload_timeout": 300,  # 秒
                "temp_dir": os.path.join(self.plugin_dir, "temp"),
                "max_workers": 3,
                "resource_dir": os.path.join(self.plugin_dir, "resource"),
                "use_block_models": True,  # 默认启用方块模型
                "max_gif_size_bytes": 5 * 1024 * 1024  # 最大GIF文件大小（字节），默认5MB
            }
        
        # 创建临时目录
        temp_dir = self.default_config["temp_dir"]
        if isinstance(temp_dir, str):
            os.makedirs(temp_dir, exist_ok=True)
    
    def get_litematic_dir(self) -> str:
        """获取litematic文件存储目录路径
        
        Returns:
            str: 目录路径
        """
        return self.litematic_dir
    
    def get_categories_file(self) -> str:
        """获取分类配置文件路径
        
        Returns:
            str: 文件路径
        """
        return self.categories_file
    
    def get_plugin_dir(self) -> str:
        """获取插件目录路径
        
        Returns:
            str: 目录路径
        """
        return self.plugin_dir
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.default_config.get(key, default)
    
    def get_resource_dir(self) -> str:
        """获取资源目录
        
        Returns:
            str: 资源目录路径
        """
        resource_dir = self.default_config.get("resource_dir")
        if isinstance(resource_dir, str):
            return resource_dir
        return os.path.join(self.plugin_dir, "resource")  # 默认值
    
    def get_models_dir(self) -> str:
        """获取模型目录路径
        
        Returns:
            str: 模型目录路径
        """
        return os.path.join(self.get_resource_dir(), "models", "block")
    
    def use_block_models(self) -> bool:
        """检查是否使用方块模型
        
        Returns:
            bool: 是否启用方块模型
        """
        return self.get_config_value("use_block_models", True) 