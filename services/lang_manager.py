import os
import json
from typing import Dict, Optional
from astrbot import logger


class LangManager:
    """语言翻译管理器，负责加载和提供Minecraft物品/方块的翻译"""
    
    def __init__(self, plugin_dir: str, lang_code: str = "zh_cn") -> None:
        """
        初始化语言管理器
        
        Args:
            plugin_dir: 插件根目录
            lang_code: 语言代码，默认为"zh_cn"
        """
        self.plugin_dir: str = plugin_dir
        self.lang_code: str = lang_code
        self.translations: Dict[str, str] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """加载语言翻译文件"""
        try:
            lang_file_path = os.path.join(self.plugin_dir, "lang", f"{self.lang_code}.json")
            
            if not os.path.exists(lang_file_path):
                logger.warning(f"语言文件不存在: {lang_file_path}")
                return
            
            with open(lang_file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            logger.info(f"成功加载语言文件: {lang_file_path}, 共 {len(self.translations)} 条翻译")
            
        except Exception as e:
            logger.error(f"加载语言文件失败: {e}")
            self.translations = {}
    
    def translate_block(self, block_id: str) -> str:
        """
        翻译方块ID为中文名称
        
        Args:
            block_id: 方块ID，格式如 "minecraft:nether_portal"
            
        Returns:
            翻译后的中文名称，如果找不到翻译则返回原ID
        """
        if not block_id:
            return block_id
        
        # 移除 minecraft: 前缀
        if block_id.startswith("minecraft:"):
            block_key = block_id[10:]  # 移除 "minecraft:" 前缀
        else:
            block_key = block_id
        
        # 尝试查找翻译
        translation_key = f"block.minecraft.{block_key}"
        
        if translation_key in self.translations:
            return self.translations[translation_key]
        
        # 如果没有找到翻译，返回原ID
        return block_id
    
    def translate_item(self, item_id: str) -> str:
        """
        翻译物品ID为中文名称
        
        Args:
            item_id: 物品ID，格式如 "minecraft:diamond"
            
        Returns:
            翻译后的中文名称，如果找不到翻译则返回原ID
        """
        if not item_id:
            return item_id
        
        # 移除 minecraft: 前缀
        if item_id.startswith("minecraft:"):
            item_key = item_id[10:]
        else:
            item_key = item_id
        
        # 尝试查找翻译
        translation_key = f"item.minecraft.{item_key}"
        
        if translation_key in self.translations:
            return self.translations[translation_key]
        
        # 如果没有找到翻译，返回原ID
        return item_id
    
    def translate_entity(self, entity_id: str) -> str:
        """
        翻译实体ID为中文名称
        
        Args:
            entity_id: 实体ID，格式如 "minecraft:zombie"
            
        Returns:
            翻译后的中文名称，如果找不到翻译则返回原ID
        """
        if not entity_id:
            return entity_id
        
        # 移除 minecraft: 前缀
        if entity_id.startswith("minecraft:"):
            entity_key = entity_id[10:]
        else:
            entity_key = entity_id
        
        # 尝试查找翻译
        translation_key = f"entity.minecraft.{entity_key}"
        
        if translation_key in self.translations:
            return self.translations[translation_key]
        
        # 如果没有找到翻译，返回原ID
        return entity_id
    
    def translate(self, key: str) -> str:
        """
        根据翻译键查找对应的翻译
        
        Args:
            key: 翻译键，如 "block.minecraft.nether_portal"
            
        Returns:
            翻译后的文本，如果找不到则返回原键
        """
        if not key:
            return key
        
        if key in self.translations:
            return self.translations[key]
        
        return key