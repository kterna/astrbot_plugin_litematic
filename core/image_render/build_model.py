from litemapy import Schematic
from collections import defaultdict

class Block:
    """表示Minecraft世界中的一个方块，包含位置、类型、朝向和材质信息"""
    
    def __init__(self, name, position, facing=None, texture=None):
        self.name = name
        self.position = position  # [x, y, z]
        self.facing = facing
        self.texture = texture
        
        # 材质面映射关系
        self.texture_mappings = {}
        
        self._set_default_mappings()
        self._apply_special_block_mappings()
    
    def _set_default_mappings(self):
        """设置默认的材质面映射关系"""
        self.texture_mappings = {
            'top': 'top',         # 顶视图使用top材质
            'front': 'side',      # 前视图使用side材质
            'side': 'side',       # 侧视图使用side材质
            'bottom': 'bottom'    # 底视图使用bottom材质
        }
    
    def _apply_special_block_mappings(self):
        """为特殊方块应用材质映射关系"""
        if not self.facing:
            return
            
        block_type_handlers = {
            "stairs": self._apply_stairs_mappings,
            "door": self._apply_door_mappings,
            "piston": self._apply_piston_mappings,
            "comparator": self._apply_redstone_component_mappings,
            "repeater": self._apply_redstone_component_mappings
        }
        
        for keyword, handler in block_type_handlers.items():
            if keyword in self.name:
                handler()
                break
    
    def _apply_stairs_mappings(self):
        """应用楼梯方块的材质映射"""
        facing_mappings = {
            "north": {'front': 'front', 'side': 'side'},
            "south": {'front': 'back', 'side': 'side'},
            "east": {'front': 'side', 'side': 'front'},
            "west": {'front': 'side', 'side': 'back'}
        }
        
        if self.facing in facing_mappings:
            self.texture_mappings.update(facing_mappings[self.facing])
    
    def _apply_door_mappings(self):
        """应用门类方块的材质映射"""
        facing_mappings = {
            "north": {'front': 'front'},
            "south": {'front': 'back'},
            "east": {'side': 'front'},
            "west": {'side': 'back'}
        }
        
        if self.facing in facing_mappings:
            self.texture_mappings.update(facing_mappings[self.facing])
    
    def _apply_piston_mappings(self):
        """应用活塞类方块的材质映射"""
        facing_mappings = {
            "up": {'top': 'front'},
            "down": {'bottom': 'front'},
            "north": {'front': 'front'},
            "south": {'front': 'back'},
            "east": {'side': 'front'},
            "west": {'side': 'back'}
        }
        
        if self.facing in facing_mappings:
            self.texture_mappings.update(facing_mappings[self.facing])
    
    def _apply_redstone_component_mappings(self):
        """应用红石元件的材质映射"""
        self.texture_mappings['top'] = f'top_{self.facing}'
    
    def get_texture_face(self, view):
        """获取指定视图对应的材质面"""
        return self.texture_mappings.get(view, view)


class World:
    """表示一个Minecraft世界，包含方块集合和索引结构"""
    
    def __init__(self):
        self.blocks = []
        self.block_map_xzy = defaultdict(lambda: defaultdict(dict))
        self.block_map_yzx = defaultdict(lambda: defaultdict(dict))
        self.block_map_zyx = defaultdict(lambda: defaultdict(dict))
    
    def add_blocks(self, schem: Schematic):
        """从Schematic中添加方块到世界"""
        for region_name, region in schem.regions.items():
            for x, y, z in region.block_positions():
                block = region[x, y, z]
                
                # 跳过空气方块
                if block is None or block.id == "minecraft:air":
                    continue
                
                # 获取方块方向属性
                facing = self._get_block_facing(block)
                
                new_block = Block(
                    name=block.id,
                    position=[x, y, z],
                    facing=facing,
                    texture=None
                )
                
                self.blocks.append(new_block)
                self._add_block_to_indices(new_block, x, y, z)
    
    def _get_block_facing(self, block):
        """从方块对象中提取朝向信息"""
        if not hasattr(block, '_BlockState__properties'):
            return None
            
        facing_properties = ['facing', 'rotation', 'axis']
        for prop in facing_properties:
            if prop in block._BlockState__properties:
                return block[prop]
        
        return None
    
    def _add_block_to_indices(self, block, x, y, z):
        """将方块添加到各个索引结构中"""
        self.block_map_xzy[x][z][y] = block
        self.block_map_yzx[y][z][x] = block
        self.block_map_zyx[z][y][x] = block
    
    def get_min_y_at(self, x, z):
        """获取指定x,z坐标上的最小y值的方块"""
        if x in self.block_map_xzy and z in self.block_map_xzy[x]:
            y_values = self.block_map_xzy[x][z].keys()
            if y_values:
                min_y = min(y_values)
                return self.block_map_xzy[x][z][min_y]
        return None
    
    def get_max_y_at(self, x, z):
        """获取指定x,z坐标上的最大y值的方块"""
        if x in self.block_map_xzy and z in self.block_map_xzy[x]:
            y_values = self.block_map_xzy[x][z].keys()
            if y_values:
                max_y = max(y_values)
                return self.block_map_xzy[x][z][max_y]
        return None
    
    def get_min_x_at(self, y, z):
        """获取指定y,z坐标上的最小x值的方块"""
        if y in self.block_map_yzx and z in self.block_map_yzx[y]:
            x_values = self.block_map_yzx[y][z].keys()
            if x_values:
                min_x = min(x_values)
                return self.block_map_yzx[y][z][min_x]
        return None
    
    def get_max_x_at(self, y, z):
        """获取指定y,z坐标上的最大x值的方块"""
        if y in self.block_map_yzx and z in self.block_map_yzx[y]:
            x_values = self.block_map_yzx[y][z].keys()
            if x_values:
                max_x = max(x_values)
                return self.block_map_yzx[y][z][max_x]
        return None
    
    def get_min_z_at(self, x, y):
        """获取指定x,y坐标上的最小z值的方块"""
        if y in self.block_map_yzx and x in self.block_map_yzx[y]:
            z_values = []
            for z in self.block_map_yzx[y]:
                if x in self.block_map_yzx[y][z]:
                    z_values.append(z)
            
            if z_values:
                min_z = min(z_values)
                return self.block_map_yzx[y][min_z][x]
        return None
    
    def get_max_z_at(self, x, y):
        """获取指定x,y坐标上的最大z值的方块"""
        if y in self.block_map_yzx and x in self.block_map_yzx[y]:
            z_values = []
            for z in self.block_map_yzx[y]:
                if x in self.block_map_yzx[y][z]:
                    z_values.append(z)
            
            if z_values:
                max_z = max(z_values)
                return self.block_map_yzx[y][max_z][x]
        return None