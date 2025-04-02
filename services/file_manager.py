import os
import shutil
import asyncio
from typing import List, Optional, Tuple, Union
from astrbot import logger
from ..utils.config import Config
from .category_manager import CategoryManager
from ..utils.exceptions import FileNotFoundError, FileDeleteError, MultipleFilesFoundError, CategoryNotFoundError, CategoryDeleteError, FileSaveError
from ..utils.logging_utils import log_error, log_operation

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
    
    def get_litematic_dir(self) -> str:
        """获取litematic文件存储根目录
        
        Returns:
            str: 存储根目录路径
        """
        return self.litematic_dir
    
    def get_litematic_file(self, category: str, filename: str) -> str:
        """获取指定的litematic文件路径，支持模糊匹配
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 文件路径
            
        Raises:
            CategoryNotFoundError: 分类不存在
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
        """
        return self._sync_get_litematic_file(category, filename)
    
    async def get_litematic_file_async(self, category: str, filename: str) -> str:
        """异步获取指定的litematic文件路径，支持模糊匹配
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 文件路径
            
        Raises:
            CategoryNotFoundError: 分类不存在
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
        """
        return await asyncio.to_thread(self._sync_get_litematic_file, category, filename)
    
    def _sync_get_litematic_file(self, category: str, filename: str) -> str:
        """同步获取指定的litematic文件路径（内部方法）
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 文件路径
            
        Raises:
            CategoryNotFoundError: 分类不存在
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
        """
        category_dir = os.path.join(self.litematic_dir, category)
        
        if not os.path.exists(category_dir):
            raise CategoryNotFoundError(category)
            
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
            # 多个匹配时不再自动选择第一个，而是抛出异常
            logger.warning(f"文件名'{filename}'在'{category}'中有多个匹配: {matches}")
            raise MultipleFilesFoundError(category, filename, matches)
        
        # 没有找到匹配的文件
        raise FileNotFoundError(category, filename)
    
    def save_litematic_file(self, source_path: str, category: str, filename: str) -> str:
        """保存litematic文件到指定分类目录
        
        Args:
            source_path: 源文件路径
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 目标文件路径
            
        Raises:
            FileSaveError: 文件保存失败
        """
        return self._sync_save_litematic_file(source_path, category, filename)
    
    async def save_litematic_file_async(self, source_path: str, category: str, filename: str) -> str:
        """异步保存litematic文件到指定分类目录
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            source_path: 源文件路径
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 目标文件路径
            
        Raises:
            FileSaveError: 文件保存失败
        """
        return await asyncio.to_thread(self._sync_save_litematic_file, source_path, category, filename)
    
    def _sync_save_litematic_file(self, source_path: str, category: str, filename: str) -> str:
        """同步保存litematic文件到指定分类目录（内部方法）
        
        Args:
            source_path: 源文件路径
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 目标文件路径
            
        Raises:
            FileSaveError: 文件保存失败
        """
        try:
            category_dir = self._get_category_dir(category)
            os.makedirs(category_dir, exist_ok=True)
            
            target_path = os.path.join(category_dir, os.path.basename(filename))
            shutil.copy2(source_path, target_path)
            log_operation("保存文件", True, {"category": category, "filename": filename})
            return target_path
        except Exception as e:
            error = FileSaveError(filename, str(e))
            log_error(error)
            raise error
    
    def delete_litematic_file(self, category: str, filename: str) -> str:
        """删除指定分类下的litematic文件
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 删除的文件名
            
        Raises:
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
            FileDeleteError: 删除文件失败
        """
        return self._sync_delete_litematic_file(category, filename)
    
    async def delete_litematic_file_async(self, category: str, filename: str) -> str:
        """异步删除指定分类下的litematic文件
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 删除的文件名
            
        Raises:
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
            FileDeleteError: 删除文件失败
        """
        return await asyncio.to_thread(self._sync_delete_litematic_file, category, filename)
    
    def _sync_delete_litematic_file(self, category: str, filename: str) -> str:
        """同步删除指定分类下的litematic文件（内部方法）
        
        Args:
            category: 分类名
            filename: 文件名
            
        Returns:
            str: 删除的文件名
            
        Raises:
            FileNotFoundError: 文件不存在
            MultipleFilesFoundError: 找到多个匹配的文件
            FileDeleteError: 删除文件失败
        """
        category_dir = self._get_category_dir(category)
        file_path = os.path.join(category_dir, filename)
        
        if not os.path.exists(file_path):
            # 尝试模糊匹配
            matches = self._sync_find_files_by_pattern(category, filename)
            if not matches:
                raise FileNotFoundError(category, filename)
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                raise MultipleFilesFoundError(category, filename, matches)
        
        try:
            os.remove(file_path)
            deleted_filename = os.path.basename(file_path)
            log_operation("删除文件", True, {"category": category, "filename": deleted_filename})
            return deleted_filename
        except Exception as e:
            error_msg = f"删除文件失败: {e}"
            error = FileDeleteError(category, os.path.basename(file_path), str(e))
            log_error(error)
            raise error
    
    def delete_category(self, category: str) -> None:
        """删除整个分类及其文件
        
        Args:
            category: 分类名
            
        Raises:
            CategoryNotFoundError: 分类不存在
            CategoryDeleteError: 删除分类失败
        """
        self._sync_delete_category(category)
    
    async def delete_category_async(self, category: str) -> None:
        """异步删除整个分类及其文件
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            category: 分类名
            
        Raises:
            CategoryNotFoundError: 分类不存在
            CategoryDeleteError: 删除分类失败
        """
        await asyncio.to_thread(self._sync_delete_category, category)
    
    def _sync_delete_category(self, category: str) -> None:
        """同步删除整个分类及其文件（内部方法）
        
        Args:
            category: 分类名
            
        Raises:
            CategoryNotFoundError: 分类不存在
            CategoryDeleteError: 删除分类失败
        """
        category_dir = self._get_category_dir(category)
        
        if not os.path.exists(category_dir):
            raise CategoryNotFoundError(category)
            
        try:
            shutil.rmtree(category_dir)
            log_operation("删除分类", True, {"category": category})
        except Exception as e:
            error = CategoryDeleteError(category, str(e))
            log_error(error)
            raise error
    
    def find_files_by_pattern(self, category: str, pattern: str) -> List[str]:
        """在指定分类下查找匹配模式的文件
        
        Args:
            category: 分类名
            pattern: 匹配模式
            
        Returns:
            List[str]: 匹配的文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        return self._sync_find_files_by_pattern(category, pattern)
    
    async def find_files_by_pattern_async(self, category: str, pattern: str) -> List[str]:
        """异步在指定分类下查找匹配模式的文件
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            category: 分类名
            pattern: 匹配模式
            
        Returns:
            List[str]: 匹配的文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        return await asyncio.to_thread(self._sync_find_files_by_pattern, category, pattern)
    
    def _sync_find_files_by_pattern(self, category: str, pattern: str) -> List[str]:
        """同步在指定分类下查找匹配模式的文件（内部方法）
        
        Args:
            category: 分类名
            pattern: 匹配模式
            
        Returns:
            List[str]: 匹配的文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        category_dir = self._get_category_dir(category)
        if not os.path.exists(category_dir):
            raise CategoryNotFoundError(category)
            
        return [f for f in os.listdir(category_dir) 
                if f.endswith('.litematic') and pattern.lower() in f.lower()]
    
    def list_files(self, category: str) -> List[str]:
        """列出指定分类下的所有litematic文件
        
        Args:
            category: 分类名
            
        Returns:
            List[str]: 文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        return self._sync_list_files(category)
    
    async def list_files_async(self, category: str) -> List[str]:
        """异步列出指定分类下的所有litematic文件
        
        此方法是异步的，调用时需要使用await。
        
        Args:
            category: 分类名
            
        Returns:
            List[str]: 文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        return await asyncio.to_thread(self._sync_list_files, category)
    
    def _sync_list_files(self, category: str) -> List[str]:
        """同步列出指定分类下的所有litematic文件（内部方法）
        
        Args:
            category: 分类名
            
        Returns:
            List[str]: 文件列表
            
        Raises:
            CategoryNotFoundError: 分类不存在
        """
        category_dir = self._get_category_dir(category)
        if not os.path.exists(category_dir):
            raise CategoryNotFoundError(category)
            
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
        """析构函数"""
        pass 