import os
import json
from PIL import Image
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from astrbot import logger  # 添加logger导入

class TextureManager:
    """材质管理器，负责加载、缓存和处理Minecraft方块材质"""
    
    def __init__(self, resource_base_path: str = "./resource", 
                 texture_path: Optional[str] = None, 
                 texture_size: Optional[int] = None) -> None:
        self.resource_base_path: str = resource_base_path
        logger.debug(f"初始化纹理管理器: resource_base_path={resource_base_path}")
        self.resourcepack_config: Dict[str, Any] = self._load_resourcepack_config()
        self._setup_texture_paths(texture_path)
        self._setup_texture_size(texture_size)
        self.texture_cache: Dict[str, Image.Image] = {}
        self.default_texture: Image.Image = self._create_default_texture()
        self.available_textures: Dict[str, str] = self._load_available_textures()
        logger.debug(f"纹理管理器初始化完成: 找到 {len(self.available_textures)} 个纹理")
    
    def _setup_texture_paths(self, texture_path: Optional[str]) -> None:
        """设置材质包路径"""
        if texture_path is None:
            selected_pack = self.resourcepack_config.get("selected_pack")
            if selected_pack:
                self.texture_paths: List[str] = []
                
                first_path = os.path.join(self.resource_base_path, "textures", "block", selected_pack)
                if os.path.exists(first_path):
                    self.texture_paths.append(first_path)
                    logger.debug(f"添加主要纹理路径: {first_path}")
                else:
                    logger.warning(f"选定的材质包路径不存在: {first_path}")
                
                available_packs = self.resourcepack_config.get("available_packs", [])
                for pack in available_packs:
                    if pack != selected_pack:
                        pack_path = os.path.join(self.resource_base_path, "textures", "block", pack)
                        if os.path.exists(pack_path):
                            self.texture_paths.append(pack_path)
                            logger.debug(f"添加备选纹理路径: {pack_path}")
                
                self.texture_path: str = self.texture_paths[0] if self.texture_paths else os.path.join(self.resource_base_path, "textures", "block")
            else:
                self.texture_path = os.path.join(self.resource_base_path, "textures", "block")
                self.texture_paths = [self.texture_path]
                logger.debug(f"使用默认纹理路径: {self.texture_path}")
        else:
            self.texture_path = texture_path
            self.texture_paths = [texture_path]
            logger.debug(f"使用指定的纹理路径: {self.texture_path}")
    
    def _setup_texture_size(self, texture_size: Optional[int]) -> None:
        """设置材质尺寸"""
        if texture_size is None:
            selected_pack = self.resourcepack_config.get("selected_pack")
            self.texture_size: int = self.resourcepack_config.get("texture_size", {}).get(selected_pack, 16)
        else:
            self.texture_size = texture_size
        logger.debug(f"纹理尺寸设置为: {self.texture_size}x{self.texture_size}")
    
    def _load_resourcepack_config(self) -> Dict[str, Any]:
        """加载资源包配置文件"""
        config_path = os.path.join(self.resource_base_path, "resourcepack.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.debug(f"成功加载资源包配置: {config_path}")
                    return config
            logger.warning(f"资源包配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_resourcepack_config()
        except Exception as e:
            logger.error(f"加载资源包配置失败: {str(e)}，使用默认配置")
            return self._get_default_resourcepack_config()
    
    def _get_default_resourcepack_config(self) -> Dict[str, Any]:
        """返回默认的材质包配置"""
        default_config = {
            "selected_pack": "",
            "available_packs": [],
            "texture_size": {}
        }
        logger.debug(f"使用默认资源包配置: {default_config}")
        return default_config
    
    def _load_available_textures(self) -> Dict[str, str]:
        """加载可用的材质文件列表"""
        available_textures: Dict[str, str] = {}
        texture_count = 0
        
        for texture_path in self.texture_paths:
            if os.path.exists(texture_path):
                path_texture_count = 0
                for file_name in os.listdir(texture_path):
                    if file_name.endswith('.png'):
                        block_name = os.path.splitext(file_name)[0]
                        if block_name not in available_textures:
                            available_textures[block_name] = os.path.join(texture_path, file_name)
                            path_texture_count += 1
                logger.debug(f"从路径 {texture_path} 加载了 {path_texture_count} 个纹理")
                texture_count += path_texture_count
            else:
                logger.warning(f"纹理路径不存在: {texture_path}")
        
        logger.debug(f"总共加载了 {texture_count} 个纹理")
        return available_textures
    
    def _create_default_texture(self, size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """创建默认材质"""
        if size is None:
            size = (self.texture_size, self.texture_size)
        img = Image.new('RGBA', size, (128, 128, 128, 255))
        logger.debug(f"创建默认纹理，尺寸: {size}")
        return img
    
    def _resize_texture(self, texture: Image.Image, 
                        target_size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """调整材质尺寸"""
        try:
            if target_size is None:
                target_size = (self.texture_size, self.texture_size)
            
            if texture.size == target_size:
                return texture
                
            return texture.resize(target_size, Image.Resampling.NEAREST)
        except Exception as e:
            logger.error(f"调整纹理尺寸失败: {str(e)}, 原尺寸: {texture.size}, 目标尺寸: {target_size}")
            return self.default_texture
    
    def get_texture(self, block_name: str, face: str = "side") -> Image.Image:
        """获取指定方块和面的材质"""
        try:
            cache_key = f"{block_name}:{face}"
            
            if cache_key in self.texture_cache:
                return self.texture_cache[cache_key]
            
            texture = self._load_texture(block_name, face)
            
            if texture is not None:
                texture = self._resize_texture(texture)
            else:
                logger.warning(f"找不到材质: {block_name} ({face})，使用默认材质")
                texture = self.default_texture.copy()
                
            self.texture_cache[cache_key] = texture
            
            return texture
        except Exception as e:
            logger.error(f"获取纹理时出错: {str(e)}, block_name={block_name}, face={face}")
            return self.default_texture
    
    def _load_texture(self, block_name: str, face: str = "side") -> Optional[Image.Image]:
        """加载指定方块面的材质"""
        try:
            if ":" in block_name:
                block_name = block_name.split(":")[-1]
            
            texture_names = self._generate_texture_names(block_name, face)
            
            for name in texture_names:
                if name in self.available_textures:
                    try:
                        texture_path = self.available_textures[name]
                        logger.debug(f"加载纹理: {name} -> {texture_path}")
                        return Image.open(texture_path).convert("RGBA")
                    except Exception as e:
                        logger.error(f"加载纹理文件失败: {texture_path}, 错误: {str(e)}")
            
            if block_name in self.available_textures:
                try:
                    texture_path = self.available_textures[block_name]
                    logger.debug(f"加载基础纹理: {block_name} -> {texture_path}")
                    return Image.open(texture_path).convert("RGBA")
                except Exception as e:
                    logger.error(f"加载基础纹理文件失败: {texture_path}, 错误: {str(e)}")
            
            logger.warning(f"找不到匹配的纹理: {block_name} ({face}), 尝试过的名称: {texture_names}")
            return None
        except Exception as e:
            logger.error(f"加载纹理过程中出错: {str(e)}, block_name={block_name}, face={face}")
            return None
    
    def _generate_texture_names(self, block_name: str, face: str) -> List[str]:
        """生成可能的材质名称列表"""
        texture_names: List[str] = []
        
        texture_names.append(f"{block_name}_{face}")
        
        if face == "side":
            texture_names.append(f"{block_name}_all")
        elif face == "front":
            texture_names.append(f"{block_name}_front")
            texture_names.append(f"{block_name}_side")
        elif face == "bottom":
            texture_names.append(f"{block_name}_bottom")
            texture_names.append(f"{block_name}_down")
        elif face == "top":
            texture_names.append(f"{block_name}_top")
            texture_names.append(f"{block_name}_up")
        
        texture_names.append(block_name)
        
        return texture_names
    
    def clear_cache(self) -> None:
        """清除材质缓存"""
        self.texture_cache = {}
        logger.debug("清除纹理缓存") 