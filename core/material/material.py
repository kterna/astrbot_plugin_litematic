from litemapy import Schematic
import collections
from typing import Dict, Any

class Material:
    def __init__(self, name: str, count: int) -> None:
        self.name: str = name
        self.count: int = count

    def block_collection(self, schematic: Schematic) -> Dict[str, int]:
        """
        统计schematic中所有region的方块数量
        
        Args:
            schematic: Litematic格式的示意图
            
        Returns:
            Dict[str, int]: 包含每种方块ID及其数量的字典
        """
        block_counts = collections.Counter()
        
        # 遍历所有区域
        for region_name, region in schematic.regions.items():
            # 遍历区域中的每个方块
            for x, y, z in region.block_positions():
                block = region[x, y, z]
                
                # 跳过空气方块
                if block is None or block.id == "minecraft:air":
                    continue
                
                # 直接使用原始的block.id
                block_counts[block.id] += 1
        
        return dict(block_counts)

    def entity_collection(self, schematic: Schematic) -> Dict[str, int]:
        """
        统计schematic中所有region的实体数量
        
        Args:
            schematic: Litematic格式的示意图
            
        Returns:
            Dict[str, int]: 包含每种实体ID及其数量的字典
        """
        entity_counts = collections.Counter()
        
        # 遍历所有区域
        for region_name, region in schematic.regions.items():
            # 遍历区域中的每个实体
            if not hasattr(region, 'entities') or not region.entities:
                continue
                
            for entity in region.entities:
                # 直接使用原始的entity.id
                entity_counts[entity.id] += 1
        
        return dict(entity_counts)

    def tile_collection(self, schematic: Schematic) -> Dict[str, int]:
        """
        统计schematic中所有方块实体的数据

        Args:
            schematic: Litematic格式的示意图
            
        Returns:
            Dict[str, int]: 包含每种方块实体ID及其数量的字典
        """
        tile_entity_counts = collections.Counter()
        
        # 遍历所有区域
        for region_name, region in schematic.regions.items():
            # 遍历区域中的每个方块位置
            for x, y, z in region.block_positions():
                block = region[x, y, z]
                
                # 跳过空气方块
                if block is None or block.id == "minecraft:air":
                    continue
                
                # 检查是否有NBT数据，这可能表明它是一个方块实体
                if hasattr(block, "nbt") and block.nbt:
                    # 直接使用原始的block.id
                    tile_entity_counts[block.id] += 1
        
        return dict(tile_entity_counts)
        

