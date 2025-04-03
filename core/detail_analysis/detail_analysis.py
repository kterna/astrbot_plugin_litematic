from litemapy import Schematic
import collections
from typing import List, Optional

class DetailAnalysis:
    def __init__(self, schematic: Schematic) -> None:
        self.schematic: Schematic = schematic
        self.details: List[str] = [] 

    def analyze_schematic(self, file_path: Optional[str] = None) -> List[str]:
        """
        分析schematic的详细信息

        Args:
            file_path: Litematic文件路径，可选，因为我们已经在初始化时传入了schematic
            
        Returns:
            List[str]: 详细信息列表
        """
        # 确保使用传入的schematic而不是重新加载
        # 注释掉这行，因为我们已经在初始化时传入了schematic
        # schem = Schematic.load(file_path)
        
        # 使用已加载的schematic
        schem = self.schematic
        
        # 确保details是一个列表
        self.details = []
        self.details.append(f"投影名称: {schem.name}")
        self.details.append(f"投影作者: {schem.author}")
        self.details.append(f"投影描述: {schem.description}")
        
        # 添加更多信息
        if hasattr(schem, 'regions') and schem.regions:
            self.details.append(f"区域数量: {len(schem.regions)}")
            
            # 添加区域信息
            for region_name, region in schem.regions.items():
                self.details.append(f"区域 {region_name}: {region.width}×{region.height}×{region.length}")
        
        return self.details


