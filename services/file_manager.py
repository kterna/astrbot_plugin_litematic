import os
import shutil
from typing import List, Optional, Tuple, Union
from astrbot import logger
from concurrent.futures import ThreadPoolExecutor
from ..utils.config import Config
from .category_manager import CategoryManager

class FileManager:
    """文件管理器，负责litematic文件的管理"""
    
    def __init__(self, config: Config, category_manager: Optional[CategoryManager] = None) -> None:
        """初始化文件管理器
        
        Args:
            config: 配置对象
            category_manager: 分类管理器对象
        """
        self.config: Config = config
        self.category_manager: Optional[CategoryManager] = category_manager
        self.litematic_dir: str = config.get_litematic_dir()
        os.makedirs(self.litematic_dir, exist_ok=True)
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=config.get_config_value("max_workers", 3))
    
    def get_litematic_dir(self) -> str:
        """获取litematic文件存储根目录
        
        Returns:
            str: 存储根目录路径
        """
        return self.litematic_dir
    
    def get_litematic_file(self, category: str, filename: str) -> Optional[str]:
        """获取指定的litematic文件路径，支持模糊匹配
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            Optional[str]: 文件路径，未找到时返回None
        """
        category_dir = os.path.join(self.litematic_dir, category)
        
        if not os.path.exists(category_dir):
            return None
            
        # 精确匹配
        file_path = os.path.join(category_dir, filename)
        if os.path.exists(file_path):
            return file_path
            
        # 模糊匹配
        matches = [f for f in os.listdir(category_dir) 
                  if f.endswith('.litematic') and filename.lower() in f.lower()]
        
        if len(matches) == 1:
            return os.path.join(category_dir, matches[0])
        elif len(matches) > 1:
            # 多个匹配时返回第一个，实际应用中可能需要更复杂的处理
            logger.warning(f"文件名'{filename}'在'{category}'中有多个匹配: {matches}")
            return os.path.join(category_dir, matches[0])
        
        return None
    
    def save_litematic_file(self, source_path: str, category: str, filename: str) -> str:
        """保存litematic文件到指定分类目录
        
        Args:
            source_path: 源文件路径
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 目标文件路径
            
        Raises:
            Exception: 文件保存失败
        """
        category_dir = self._get_category_dir(category)
        os.makedirs(category_dir, exist_ok=True)
        
        target_path = os.path.join(category_dir, os.path.basename(filename))
        shutil.copy2(source_path, target_path)
        logger.info(f"已保存litematic文件: {target_path}")
        return target_path
    
    def delete_litematic_file(self, category: str, filename: str) -> Tuple[Optional[Union[str, List[str]]], Optional[str]]:
        """删除指定分类下的litematic文件
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            Tuple[Optional[Union[str, List[str]]], Optional[str]]: (删除的文件名或匹配列表, 错误信息)
        """
        category_dir = self._get_category_dir(category)
        file_path = os.path.join(category_dir, filename)
        
        if not os.path.exists(file_path):
            # 尝试模糊匹配
            matches = self.find_files_by_pattern(category, filename)
            if not matches:
                return None, f"在分类 {category} 下找不到文件 {filename}"
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                return matches, "找到多个匹配的文件"
        
        try:
            os.remove(file_path)
            return os.path.basename(file_path), None
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return None, f"删除文件失败: {e}"
    
    def delete_category(self, category: str) -> Tuple[bool, Optional[str]]:
        """删除整个分类及其文件
        
        Args:
            category: 分类名
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        category_dir = self._get_category_dir(category)
        
        if not os.path.exists(category_dir):
            return False, f"分类目录 {category} 不存在"
            
        try:
            shutil.rmtree(category_dir)
            return True, None
        except Exception as e:
            logger.error(f"删除分类失败: {e}")
            return False, f"删除分类失败: {e}"
    
    def find_files_by_pattern(self, category: str, pattern: str) -> List[str]:
        """在指定分类下查找匹配模式的文件
        
        Args:
            category: 分类名
            pattern: 匹配模式
            
        Returns:
            List[str]: 匹配的文件列表
        """
        category_dir = self._get_category_dir(category)
        if not os.path.exists(category_dir):
            return []
            
        return [f for f in os.listdir(category_dir) 
                if f.endswith('.litematic') and pattern.lower() in f.lower()]
    
    def list_files(self, category: str) -> List[str]:
        """列出指定分类下的所有litematic文件
        
        Args:
            category: 分类名
            
        Returns:
            List[str]: 文件列表
        """
        category_dir = self._get_category_dir(category)
        if not os.path.exists(category_dir):
            return []
            
        return [f for f in os.listdir(category_dir) if f.endswith('.litematic')]
    
    def _get_category_dir(self, category: str) -> str:
        """获取分类目录路径
        
        Args:
            category: 分类名
            
        Returns:
            str: 目录路径
        """
        return os.path.join(self.litematic_dir, category)
    
    def __del__(self) -> None:
        """析构函数，确保线程池正确关闭"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False) 