import os
import json
from typing import Dict, List, Any, Optional, Union
from astrbot import logger
from ...utils.types import BlockModelData

class ModelLoader:
    """处理方块模型数据加载和解析"""
    
    def __init__(self, resource_dir: str) -> None:
        """初始化模型加载器
        
        Args:
            resource_dir: 资源根目录
        """
        self.resource_dir = resource_dir
        self.model_cache: Dict[str, Any] = {}
        self.models_dir = os.path.join(resource_dir, "models", "block")
        
    def load_model(self, block_id: str) -> Optional[Dict[str, Any]]:
        """加载方块模型数据
        
        Args:
            block_id: 方块ID，例如minecraft:stone
            
        Returns:
            Optional[Dict[str, Any]]: 处理后的模型数据，失败返回None
        """
        # 从block_id中提取模型名称
        model_name = self._get_model_name(block_id)
        
        # 检查缓存
        if model_name in self.model_cache:
            return self.model_cache[model_name]
            
        # 处理不同的变种模型
        variant_models = self._find_model_variants(model_name)
        if not variant_models:
            return None
            
        # 加载主模型
        model_data = self._load_model_file(variant_models[0])
        if not model_data:
            return None
            
        # 处理parent继承
        model_data = self._resolve_model_inheritance(model_data)
        
        # 缓存并返回
        self.model_cache[model_name] = model_data
        return model_data
    
    def _get_model_name(self, block_id: str) -> str:
        """从方块ID提取模型名称
        
        Args:
            block_id: 方块ID，例如minecraft:stone或stone
            
        Returns:
            str: 模型名称，如stone
        """
        if ":" in block_id:
            return block_id.split(":")[-1]
        return block_id
    
    def _find_model_variants(self, model_name: str) -> List[str]:
        """查找模型的所有变体
        
        Args:
            model_name: 基础模型名称
            
        Returns:
            List[str]: 变体模型文件路径列表
        """
        variants = []
        
        # 尝试直接匹配
        base_path = os.path.join(self.models_dir, f"{model_name}.json")
        if os.path.exists(base_path):
            variants.append(base_path)
            
        # 查找变体模型
        if os.path.exists(self.models_dir):
            for file in os.listdir(self.models_dir):
                if file.startswith(f"{model_name}_") and file.endswith(".json"):
                    variants.append(os.path.join(self.models_dir, file))
        
        return variants
    
    def _load_model_file(self, model_path: str) -> Optional[Dict[str, Any]]:
        """加载单个模型文件
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 模型数据，失败返回None
        """
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载模型文件失败: {model_path}, 错误: {e}")
            return None
    
    def _resolve_model_inheritance(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理模型继承关系
        
        Args:
            model_data: 原始模型数据
            
        Returns:
            Dict[str, Any]: 处理后的模型数据
        """
        # 处理parent继承
        if "parent" in model_data:
            parent_name = model_data["parent"]
            
            # 去掉minecraft:前缀
            if parent_name.startswith("minecraft:"):
                parent_name = parent_name[10:]
                
            # 去掉block/前缀
            if parent_name.startswith("block/"):
                parent_name = parent_name[6:]
                
            # 加载父模型
            parent_path = os.path.join(self.models_dir, f"{parent_name}.json")
            if os.path.exists(parent_path):
                parent_data = self._load_model_file(parent_path)
                if parent_data:
                    # 递归处理父模型的继承
                    parent_data = self._resolve_model_inheritance(parent_data)
                    
                    # 合并模型数据
                    return self._merge_model_data(parent_data, model_data)
        
        return model_data
    
    def _merge_model_data(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """合并父子模型数据
        
        Args:
            parent: 父模型数据
            child: 子模型数据
            
        Returns:
            Dict[str, Any]: 合并后的模型数据
        """
        result = parent.copy()
        
        # 合并顶层属性
        for key, value in child.items():
            if key == "textures" and "textures" in result:
                # 合并纹理，但不覆盖已有的
                result["textures"].update(value)
            elif key == "elements" or key not in result:
                # 元素或新属性直接覆盖
                result[key] = value
        
        return result 