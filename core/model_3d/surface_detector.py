from typing import Dict, List, Tuple, Set, Any, Optional
import numpy as np

class SurfaceDetector:
    """检测3D模型中需要渲染的方块表面"""
    
    # 定义方块的六个面
    FACES = {
        'top': (0, 1, 0),     # +Y方向
        'bottom': (0, -1, 0),  # -Y方向
        'north': (0, 0, -1),   # -Z方向
        'south': (0, 0, 1),    # +Z方向
        'east': (1, 0, 0),     # +X方向
        'west': (-1, 0, 0)     # -X方向
    }
    
    def __init__(self, model_data: Dict[str, Any]) -> None:
        """
        初始化表面检测器
        
        Args:
            model_data: 3D模型数据，包含方块和边界信息
        """
        self.model_data = model_data
        self.blocks = model_data.get('blocks', {})
        self.visible_surfaces: Dict[Tuple[int, int, int], Dict[str, bool]] = {}
    
    def detect_visible_surfaces(self) -> None:
        """检测所有可见的方块表面"""
        self.visible_surfaces.clear()
        
        # 遍历每个方块
        for position, block_data in self.blocks.items():
            x, y, z = position
            self.visible_surfaces[position] = {}
            
            # 检查每个面是否可见
            for face_name, face_dir in self.FACES.items():
                dx, dy, dz = face_dir
                adjacent_pos = (x + dx, y + dy, z + dz)
                
                # 如果相邻位置没有方块，则当前面可见
                is_visible = adjacent_pos not in self.blocks
                
                # 存储可见性信息
                self.visible_surfaces[position][face_name] = is_visible
    
    def get_visible_surfaces(self) -> Dict[Tuple[int, int, int], Dict[str, bool]]:
        """
        获取所有可见表面的数据
        
        Returns:
            Dict: 方块位置到面可见性的映射
        """
        return self.visible_surfaces
    
    def get_surface_data_for_rendering(self) -> List[Dict[str, Any]]:
        """
        获取用于渲染的表面数据列表
        
        Returns:
            List[Dict[str, Any]]: 表面数据列表，每个表面包含位置、方向和方块ID信息
        """
        surface_data = []
        
        for position, faces in self.visible_surfaces.items():
            block_data = self.blocks.get(position)
            if not block_data:
                continue
                
            for face_name, is_visible in faces.items():
                if is_visible:
                    face_dir = self.FACES[face_name]
                    
                    surface_data.append({
                        'position': position,
                        'face': face_name,
                        'direction': face_dir,
                        'block_id': block_data['id'],
                        'properties': block_data.get('properties', {})
                    })
        
        return surface_data
    
    def count_visible_surfaces(self) -> int:
        """
        计算可见表面的总数
        
        Returns:
            int: 可见表面数量
        """
        count = 0
        for position, faces in self.visible_surfaces.items():
            for face_name, is_visible in faces.items():
                if is_visible:
                    count += 1
        return count 