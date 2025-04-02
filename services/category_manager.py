import os
import json
from typing import List, Optional
from astrbot import logger
from ..utils.config import Config

class CategoryManager:
    """分类管理器，负责litematic文件分类的管理"""
    
    def __init__(self, config: Config) -> None:
        """初始化分类管理器
        
        Args:
            config: 配置对象
        """
        self.config: Config = config
        self.categories_file: str = config.get_categories_file()
        self.categories: List[str] = []
        self.load_categories()
    
    def load_categories(self) -> None:
        """加载分类列表，如果不存在则创建默认分类"""
        try:
            if os.path.exists(self.categories_file) and os.path.getsize(self.categories_file) > 0:
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    self.categories = json.loads(f.read())
            else:
                # 创建默认分类
                self.categories = self.config.get_config_value("default_categories", ["建筑", "红石"])
                self.save_categories()
                logger.info(f"创建默认分类列表: {self.categories}")
        except Exception as e:
            logger.error(f"加载分类列表失败: {e}")
            self.categories = self.config.get_config_value("default_categories", ["建筑", "红石"])
    
    def save_categories(self) -> None:
        """保存分类列表到JSON文件"""
        try:
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
            logger.info(f"保存分类列表: {self.categories}")
        except Exception as e:
            logger.error(f"保存分类列表失败: {e}")
    
    def get_categories(self) -> List[str]:
        """获取所有分类列表
        
        Returns:
            List[str]: 分类列表
        """
        return self.categories
    
    def category_exists(self, category: str) -> bool:
        """检查分类是否存在
        
        Args:
            category: 分类名
            
        Returns:
            bool: 是否存在
        """
        return category in self.categories
    
    def create_category(self, category: str) -> bool:
        """创建新的分类
        
        Args:
            category: 分类名
            
        Returns:
            bool: 是否成功创建
        """
        if category not in self.categories:
            self.categories.append(category)
            self.save_categories()
            # 创建分类目录
            category_dir = os.path.join(self.config.get_litematic_dir(), category)
            os.makedirs(category_dir, exist_ok=True)
            logger.info(f"创建了新分类: {category}")
            return True
        return False
    
    def delete_category(self, category: str) -> bool:
        """删除分类
        
        Args:
            category: 分类名
            
        Returns:
            bool: 是否成功删除
        """
        if category in self.categories:
            self.categories.remove(category)
            self.save_categories()
            return True
        return False 