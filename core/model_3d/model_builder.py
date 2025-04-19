from typing import Dict, List, Tuple, Any, Optional
from litemapy import Schematic
import numpy as np

class ModelBuilder:
    """
    从Litematic文件构建3D模型数据结构
    """
    
    def __init__(self) -> None:
        """初始化3D模型构建器"""
        self.blocks: Dict[Tuple[int, int, int], Dict[str, Any]] = {}  # 方块坐标到方块数据的映射
        self.min_x: int = 0
        self.max_x: int = 0
        self.min_y: int = 0
        self.max_y: int = 0
        self.min_z: int = 0
        self.max_z: int = 0
    
    def build_from_litematic(self, schematic: Schematic) -> bool:
        """
        从litematic文件构建3D模型
        
        Args:
            schematic: litemapy的Schematic对象
            
        Returns:
            bool: 是否成功构建模型
        """
        try:
            # 清空现有数据
            self.blocks.clear()
            
            # 重置边界
            self.min_x, self.max_x = float('inf'), float('-inf')
            self.min_y, self.max_y = float('inf'), float('-inf')
            self.min_z, self.max_z = float('inf'), float('-inf')
            
            # 遍历每个区域
            for region_name, region in schematic.regions.items():
                for x, y, z in region.block_positions():
                    block = region[x, y, z]
                    
                    # 跳过空气方块
                    if block is None or block.id == "minecraft:air":
                        continue
                    
                    # 更新边界
                    self.min_x = min(self.min_x, x)
                    self.max_x = max(self.max_x, x)
                    self.min_y = min(self.min_y, y)
                    self.max_y = max(self.max_y, y)
                    self.min_z = min(self.min_z, z)
                    self.max_z = max(self.max_z, z)
                    
                    # 获取方块属性
                    properties = {}
                    if hasattr(block, '_BlockState__properties'):
                        for prop in block._BlockState__properties:
                            properties[prop] = block[prop]
                    
                    # 存储方块数据
                    self.blocks[(x, y, z)] = {
                        'id': block.id,
                        'properties': properties,
                        'position': (x, y, z)
                    }
            
            return True
        except Exception as e:
            print(f"构建模型时出错: {e}")
            return False
    
    def get_model_data(self) -> Dict[str, Any]:
        """
        获取构建的模型数据
        
        Returns:
            Dict[str, Any]: 包含方块和边界信息的模型数据
        """
        return {
            'blocks': self.blocks,
            'bounds': {
                'min_x': self.min_x,
                'max_x': self.max_x,
                'min_y': self.min_y,
                'max_y': self.max_y,
                'min_z': self.min_z,
                'max_z': self.max_z,
            },
            'dimensions': {
                'width': self.max_x - self.min_x + 1,
                'height': self.max_y - self.min_y + 1,
                'length': self.max_z - self.min_z + 1,
            }
        }
    
    def get_block_at(self, x: int, y: int, z: int) -> Optional[Dict[str, Any]]:
        """
        获取指定坐标的方块信息
        
        Args:
            x: X坐标
            y: Y坐标
            z: Z坐标
            
        Returns:
            Optional[Dict[str, Any]]: 方块数据，如果不存在则返回None
        """
        return self.blocks.get((x, y, z))
    
    def get_block_count(self) -> int:
        """
        获取模型中的方块数量
        
        Returns:
            int: 方块数量
        """
        return len(self.blocks) 