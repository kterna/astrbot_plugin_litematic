import os
import json
from typing import Dict, Tuple, Optional, Any

class ColorMapper:
    """将Minecraft方块ID映射到RGB颜色值"""
    
    # 默认颜色映射（基础方块）
    DEFAULT_COLORS = {
        # 常见方块
        "minecraft:stone": (128, 128, 128),           # 石头：灰色
        "minecraft:dirt": (134, 96, 67),              # 泥土：棕色
        "minecraft:grass_block": (120, 172, 84),      # 草方块：绿色
        "minecraft:cobblestone": (136, 136, 136),     # 圆石：深灰色
        "minecraft:glass": (210, 239, 243),           # 玻璃：透明色
        "minecraft:sand": (226, 219, 171),            # 沙子：浅黄色
        "minecraft:water": (39, 85, 233),             # 水：蓝色
        "minecraft:lava": (252, 102, 37),             # 岩浆：橙色
        
        # 矿石
        "minecraft:coal_ore": (57, 57, 57),           # 煤矿石：黑灰色
        "minecraft:iron_ore": (214, 190, 168),        # 铁矿石：浅灰褐色
        "minecraft:gold_ore": (246, 209, 63),         # 金矿石：金色
        "minecraft:diamond_ore": (99, 219, 213),      # 钻石矿石：青色
        "minecraft:emerald_ore": (63, 205, 119),      # 绿宝石矿石：绿色
        "minecraft:redstone_ore": (170, 44, 43),      # 红石矿石：红色
        "minecraft:lapis_ore": (39, 67, 138),         # 青金石矿石：深蓝色
        
        # 装饰方块
        "minecraft:bookshelf": (180, 144, 90),        # 书架：棕色
        "minecraft:torch": (245, 220, 50),            # 火把：黄色
        "minecraft:crafting_table": (162, 119, 79),   # 工作台：棕色
        "minecraft:furnace": (168, 168, 168),         # 熔炉：灰色
        "minecraft:chest": (184, 146, 90),            # 箱子：棕色
        
        # 红石组件
        "minecraft:redstone_wire": (220, 0, 0),       # 红石线：红色
        "minecraft:lever": (130, 130, 130),           # 拉杆：灰色
        "minecraft:redstone_torch": (220, 70, 43),    # 红石火把：红色
        "minecraft:piston": (180, 180, 180),          # 活塞：灰色
        
        # 下界植物
        "minecraft:warped_roots": (21, 180, 177),         # 诡异根
        "minecraft:warped_wart_block": (25, 151, 139),    # 诡异疣块
        "minecraft:weeping_vines": (153, 42, 47),         # 垂泪藤
        "minecraft:weeping_vines_plant": (148, 38, 43),   # 垂泪藤植物
        "minecraft:twisting_vines": (24, 120, 115),       # 扭曲藤
        "minecraft:twisting_vines_plant": (23, 110, 105), # 扭曲藤植物
        "minecraft:vine": (85, 130, 65),                  # 藤蔓
        
        # 特殊方块
        "minecraft:wet_sponge": (171, 167, 83),           # 湿海绵
        "minecraft:water_cauldron": (52, 79, 132),        # 装满水的炼药锅
        
        # 植物和作物
        "minecraft:white_tulip": (240, 240, 240),         # 白色郁金香
        "minecraft:wither_rose": (50, 50, 50),            # 凋零玫瑰
        "minecraft:wheat_stage0": (143, 156, 65),         # 小麦生长阶段0
        "minecraft:wheat_stage1": (160, 173, 72),         # 小麦生长阶段1
        "minecraft:wheat_stage2": (175, 185, 78),         # 小麦生长阶段2
        "minecraft:wheat_stage3": (190, 196, 82),         # 小麦生长阶段3
        "minecraft:wheat_stage4": (205, 208, 90),         # 小麦生长阶段4
        "minecraft:wheat_stage5": (216, 205, 79),         # 小麦生长阶段5
        "minecraft:wheat_stage6": (222, 198, 68),         # 小麦生长阶段6
        "minecraft:wheat_stage7": (229, 190, 56),         # 小麦生长阶段7 (成熟)
        
        # 默认值
        "minecraft:air": (0, 0, 0),                # 空气：透明
        "default": (200, 80, 200)                     # 默认颜色：紫色
    }
    
    def __init__(self, resource_dir: Optional[str] = None) -> None:
        """
        初始化颜色映射器
        
        Args:
            resource_dir: 资源目录路径，包含颜色配置文件
        """
        # 保留DEFAULT_COLORS字典用于初始化
        self.colors = self.DEFAULT_COLORS.copy()
        self.resource_dir = resource_dir
        
        # 构建正则匹配模式
        self._build_pattern_rules()
        
        # 如果提供了资源目录，尝试加载自定义颜色配置
        if resource_dir:
            self.load_color_map(resource_dir)
            
    def _build_pattern_rules(self):
        """构建正则匹配规则，从DEFAULT_COLORS中提取常见模式"""
        self.color_patterns = {
            # 基础颜色模式
            r'white_': (240, 240, 240),      # 白色方块
            r'orange_': (230, 120, 48),      # 橙色方块
            r'magenta_': (200, 80, 200),     # 品红色方块
            r'light_blue_': (120, 180, 225), # 淡蓝色方块
            r'yellow_': (255, 230, 74),      # 黄色方块
            r'lime_': (120, 200, 80),        # 黄绿色方块
            r'pink_': (230, 150, 165),       # 粉红色方块
            r'gray_': (85, 85, 85),          # 灰色方块
            r'light_gray_': (160, 160, 160), # 淡灰色方块
            r'cyan_': (40, 140, 165),        # 青色方块
            r'purple_': (130, 60, 190),      # 紫色方块
            r'blue_': (50, 60, 170),         # 蓝色方块
            r'brown_': (115, 75, 40),        # 棕色方块
            r'green_': (55, 120, 30),        # 绿色方块
            r'red_': (180, 60, 60),          # 红色方块
            r'black_': (40, 40, 40),         # 黑色方块
            
            # 材质类型匹配
            r'oak_': (186, 151, 96),         # 橡木系列
            r'spruce_': (114, 84, 48),       # 云杉木系列
            r'birch_': (231, 221, 171),      # 白桦木系列
            r'jungle_': (160, 115, 80),      # 丛林木系列
            r'acacia_': (169, 92, 51),       # 金合欢木系列
            r'dark_oak_': (86, 67, 41),      # 深色橡木系列
            r'warped_': (43, 104, 99),       # 诡异系列
            r'crimson_': (148, 52, 58),      # 绯红系列
            r'stone_': (128, 128, 128),      # 石头系列
            r'brick': (154, 89, 74),         # 砖块系列
            r'sandstone': (226, 219, 171),   # 砂岩系列
            r'nether_brick': (48, 24, 27),   # 下界砖系列
            r'quartz': (237, 232, 226),      # 石英系列
            r'prismarine': (100, 171, 158),  # 海晶石系列
            r'coral_block': (180, 180, 180), # 珊瑚块系列
            r'coral$': (170, 170, 170),      # 珊瑚系列
            r'coral_fan': (175, 175, 175),   # 珊瑚扇系列
            r'dead_': (130, 122, 115),       # 死亡珊瑚系列
            
            # 特殊方块类型细化匹配
            r'tube_coral': (51, 121, 198),   # 管珊瑚系列
            r'brain_coral': (226, 136, 186), # 脑珊瑚系列
            r'bubble_coral': (161, 75, 175), # 气泡珊瑚系列
            r'fire_coral': (196, 54, 53),    # 火珊瑚系列
            r'horn_coral': (225, 197, 24),   # 角珊瑚系列
            r'turtle_egg': (216, 226, 215),  # 海龟蛋
            r'froglight': (190, 190, 190),   # 蛙光
            r'verdant_froglight': (180, 212, 146), # 青翠蛙光
            r'ochre_froglight': (216, 197, 100),   # 赭色蛙光
            r'pearlescent_froglight': (213, 213, 223), # 珠光蛙光
            r'vault': (190, 190, 190),       # 金库
            r'trial_spawner': (160, 160, 160), # 试炼刷怪笼
            r'tuff': (109, 106, 97),         # 凝灰岩系列
            
            # 特殊方块匹配
            r'log': (114, 84, 48),           # 原木
            r'planks': (160, 115, 80),       # 木板
            r'leaves': (65, 102, 48),        # 树叶
            r'glass': (210, 239, 243),       # 玻璃
            r'ice': (150, 200, 255),         # 冰块
            r'door': (160, 115, 80),         # 门
            r'trapdoor': (160, 115, 80),     # 活板门
            r'slab': (160, 115, 80),         # 台阶
            r'stairs': (160, 115, 80),       # 楼梯
            r'fence': (160, 115, 80),        # 栅栏
            r'wall': (128, 128, 128),        # 墙
            r'ore': (128, 128, 128),         # 矿石
        }
    
    def load_color_map(self, resource_dir: str) -> bool:
        """
        从配置文件加载颜色映射
        
        Args:
            resource_dir: 资源目录路径
            
        Returns:
            bool: 是否成功加载配置
        """
        try:
            color_config_path = os.path.join(resource_dir, 'block_colors.json')
            if os.path.exists(color_config_path):
                with open(color_config_path, 'r', encoding='utf-8') as f:
                    custom_colors = json.load(f)
                    
                    # 更新颜色映射
                    for block_id, color in custom_colors.items():
                        if isinstance(color, list) and len(color) >= 3:
                            self.colors[block_id] = tuple(color)
                            
                return True
            return False
        except Exception as e:
            print(f"加载颜色配置时出错: {e}")
            return False
    
    def get_block_color(self, block_id: str) -> Tuple[int, int, int]:
        """
        获取方块类型对应的颜色
        
        Args:
            block_id: 方块ID，例如"minecraft:stone"
            
        Returns:
            Tuple[int, int, int]: RGB颜色元组
        """
        # 先尝试使用正则模式匹配
        pattern_color = self._try_pattern_match(block_id)
        
        # 如果正则匹配返回的不是默认颜色，说明匹配成功，直接返回
        if pattern_color != self.colors['default']:
            return pattern_color
            
        # 如果正则匹配不成功，再尝试精确匹配
        if block_id in self.colors:
            return self.colors[block_id]
            
        # 最后都失败则返回默认颜色
        return self.colors['default']

    def _try_pattern_match(self, block_id: str) -> Tuple[int, int, int]:
        """
        尝试基于方块ID中的规律进行颜色匹配
        
        Args:
            block_id: 方块ID
            
        Returns:
            Tuple[int, int, int]: RGB颜色元组
        """
        import re
        
        # 提取方块名称部分（去掉命名空间）
        if ':' in block_id:
            block_name = block_id.split(':')[1]
        else:
            block_name = block_id
            
        # 尝试匹配规则
        for pattern, color in self.color_patterns.items():
            if re.search(pattern, block_name):
                return color
                
        # 如果所有规则都不匹配，返回默认颜色
        return self.colors['default']
    
    def get_face_color(self, block_id: str, face: str) -> Tuple[int, int, int]:
        """
        获取方块特定面的颜色，针对不同面可以返回不同的颜色
        
        Args:
            block_id: 方块ID
            face: 面名称 (top, bottom, north, south, east, west)
            
        Returns:
            Tuple[int, int, int]: RGB颜色元组
        """
        base_color = self.get_block_color(block_id)
        
        # 为不同面应用不同的明暗调整
        if face == 'top':
            # 顶面最亮
            return self._brighten_color(base_color, 1.2)
        elif face == 'bottom':
            # 底面最暗
            return self._darken_color(base_color, 0.7)
        elif face in ['north', 'south']:
            # 北/南面稍暗
            return self._darken_color(base_color, 0.9)
        else:  # east/west
            # 东/西面中间亮度
            return self._darken_color(base_color, 0.8)
    
    def _brighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """增亮颜色"""
        r, g, b = color
        return (
            min(255, int(r * factor)),
            min(255, int(g * factor)),
            min(255, int(b * factor))
        )
    
    def _darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """降暗颜色"""
        r, g, b = color
        return (
            max(0, int(r * factor)),
            max(0, int(g * factor)),
            max(0, int(b * factor))
        )
    
    def get_texture_interface(self, block_id: str) -> Dict[str, Any]:
        """
        获取兼容纹理系统的接口(只返回纯色)
        
        这个接口允许未来扩展为真实纹理
        
        Args:
            block_id: 方块ID
            
        Returns:
            Dict[str, Any]: 表示纹理的字典对象
        """
        color = self.get_block_color(block_id)
        
        # 创建简化的纹理接口
        return {
            'type': 'color',
            'color': color,
            'face_colors': {
                'top': self.get_face_color(block_id, 'top'),
                'bottom': self.get_face_color(block_id, 'bottom'),
                'north': self.get_face_color(block_id, 'north'),
                'south': self.get_face_color(block_id, 'south'),
                'east': self.get_face_color(block_id, 'east'),
                'west': self.get_face_color(block_id, 'west')
            }
        } 