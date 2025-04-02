import os
import json
from typing import Any, Dict, List, Optional, Union
from astrbot import logger
from astrbot.api.star import Context

class Config:
    """配置管理类，负责管理插件配置"""
    
    def __init__(self, context: Optional[Context] = None) -> None:
        """初始化配置管理器
        
        Args:
            context: AstrBot上下文对象
        """
        self.context: Optional[Context] = context
        
        # 通过文件路径确定插件目录，避免使用context.get_plugin_dir()
        self.plugin_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 设置litematic文件存储目录
        self.litematic_dir: str = os.path.join(os.path.dirname(self.plugin_dir), "litematic")
        
        # 设置分类配置文件路径
        self.categories_file: str = os.path.join(self.litematic_dir, "litematic_categories.json")
        
        # 创建必要的目录
        os.makedirs(self.litematic_dir, exist_ok=True)
        
        # 默认配置
        self.default_config: Dict[str, Union[List[str], int, str]] = {
            "default_categories": ["建筑", "红石"],
            "upload_timeout": 300,  # 秒
            "temp_dir": os.path.join(self.plugin_dir, "temp"),
            "max_workers": 3,
            "resource_dir": os.path.join(self.plugin_dir, "resource")
        }
        
        # 创建临时目录
        os.makedirs(self.default_config["temp_dir"], exist_ok=True)
    
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
        return self.default_config.get("resource_dir") 