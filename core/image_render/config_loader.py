import os
import json

class ConfigLoader:
    """
    配置加载器，负责加载和处理各种配置文件，
    包括资源包配置和特殊方块配置等。
    """
    
    def __init__(self, resource_base_path="./resource"):
        """
        初始化配置加载器。
        
        参数:
            resource_base_path (str): 资源基础路径，默认为"./resource"
        """
        self.resource_base_path = resource_base_path
        self._instance = None
    
    @classmethod
    def get_instance(cls, resource_base_path="./resource"):
        """
        获取配置加载器的单例实例。
        
        参数:
            resource_base_path (str): 资源基础路径
            
        返回:
            ConfigLoader: 配置加载器实例
        """
        if not hasattr(cls, '_instance') or cls._instance is None:
            cls._instance = cls(resource_base_path)
        return cls._instance
    
    def load_resourcepack_config(self):
        """
        加载资源包配置文件。
        
        返回:
            dict: 资源包配置信息
        """
        config_path = os.path.join(self.resource_base_path, "resourcepack.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self._get_default_resourcepack_config()
        except Exception:
            return self._get_default_resourcepack_config()
    
    def _get_default_resourcepack_config(self):
        """
        返回默认的材质包配置。
        
        返回:
            dict: 默认的资源包配置
        """
        return {
            "selected_pack": "",
            "available_packs": [],
            "texture_size": {}
        }
    
    def load_special_blocks_config(self, config_path="./core/image_render/Special_blocks.json"):
        """
        加载特殊方块配置文件。
        
        参数:
            config_path (str): 配置文件路径
            
        返回:
            dict: 特殊方块配置信息
        """
        try:
            # 尝试相对路径和绝对路径
            if not os.path.isabs(config_path) and not os.path.exists(config_path):
                # 基于当前文件路径尝试
                current_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(current_dir, os.path.basename(config_path))
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self._get_default_special_blocks_config()
        except Exception:
            return self._get_default_special_blocks_config()
    
    def _get_default_special_blocks_config(self):
        """
        返回默认的特殊方块配置。
        
        返回:
            dict: 默认的特殊方块配置
        """
        return {
            "version": "1.0",
            "block_types": {},
            "default_mapping": {
                "top": "top",
                "front": "side",
                "side": "side",
                "bottom": "bottom"
            }
        }
    
    def validate_config(self, config, config_type):
        """
        验证配置文件的有效性。
        
        参数:
            config (dict): 配置数据
            config_type (str): 配置类型 ('resourcepack', 'special_blocks')
            
        返回:
            bool: 配置是否有效
        """
        if config_type == 'resourcepack':
            # 检查关键字段是否存在
            if 'selected_pack' not in config:
                return False
                
            if 'available_packs' not in config:
                return False
                
            if 'texture_size' not in config:
                return False
                
            return True
            
        elif config_type == 'special_blocks':
            # 检查关键字段是否存在
            if 'version' not in config:
                return False
                
            if 'block_types' not in config:
                return False
                
            return True
            
        return False 