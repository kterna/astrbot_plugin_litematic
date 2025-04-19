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
        "minecraft:oak_planks": (186, 151, 96),       # 橡木木板：浅棕色
        "minecraft:spruce_planks": (114, 84, 48),     # 云杉木板：深棕色
        "minecraft:birch_planks": (231, 221, 171),    # 白桦木板：米色
        "minecraft:jungle_planks": (160, 115, 80),    # 丛林木板：棕色
        "minecraft:acacia_planks": (169, 92, 51),     # 金合欢木板：橙棕色
        "minecraft:dark_oak_planks": (86, 67, 41),    # 深色橡木木板：深棕色
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
        
        # 羊毛
        "minecraft:white_wool": (240, 240, 240),      # 白色羊毛
        "minecraft:orange_wool": (230, 120, 48),      # 橙色羊毛
        "minecraft:magenta_wool": (200, 80, 200),     # 品红色羊毛
        "minecraft:light_blue_wool": (120, 180, 225), # 淡蓝色羊毛
        "minecraft:yellow_wool": (255, 230, 74),      # 黄色羊毛
        "minecraft:lime_wool": (120, 200, 80),        # 黄绿色羊毛
        "minecraft:pink_wool": (230, 150, 165),       # 粉红色羊毛
        "minecraft:gray_wool": (85, 85, 85),          # 灰色羊毛
        "minecraft:light_gray_wool": (160, 160, 160), # 淡灰色羊毛
        "minecraft:cyan_wool": (40, 140, 165),        # 青色羊毛
        "minecraft:purple_wool": (130, 60, 190),      # 紫色羊毛
        "minecraft:blue_wool": (50, 60, 170),         # 蓝色羊毛
        "minecraft:brown_wool": (115, 75, 40),        # 棕色羊毛
        "minecraft:green_wool": (55, 120, 30),        # 绿色羊毛
        "minecraft:red_wool": (180, 60, 60),          # 红色羊毛
        "minecraft:black_wool": (40, 40, 40),         # 黑色羊毛
        
        # 混凝土
        "minecraft:white_concrete": (237, 237, 237),  # 白色混凝土
        "minecraft:orange_concrete": (225, 97, 0),    # 橙色混凝土
        "minecraft:magenta_concrete": (170, 50, 160), # 品红色混凝土
        "minecraft:light_blue_concrete": (40, 140, 210), # 淡蓝色混凝土
        "minecraft:yellow_concrete": (235, 197, 37),  # 黄色混凝土
        "minecraft:lime_concrete": (95, 170, 25),     # 黄绿色混凝土
        "minecraft:pink_concrete": (215, 130, 145),   # 粉红色混凝土
        "minecraft:gray_concrete": (55, 58, 62),      # 灰色混凝土
        "minecraft:light_gray_concrete": (126, 126, 116), # 淡灰色混凝土
        "minecraft:cyan_concrete": (20, 120, 140),    # 青色混凝土
        "minecraft:purple_concrete": (100, 40, 160),  # 紫色混凝土
        "minecraft:blue_concrete": (40, 50, 145),     # 蓝色混凝土
        "minecraft:brown_concrete": (100, 65, 35),    # 棕色混凝土
        "minecraft:green_concrete": (55, 75, 25),     # 绿色混凝土
        "minecraft:red_concrete": (145, 40, 40),      # 红色混凝土
        "minecraft:black_concrete": (8, 10, 15),      # 黑色混凝土
        
        # 混凝土粉末
        "minecraft:white_concrete_powder": (230, 230, 230),  # 白色混凝土粉末
        "minecraft:orange_concrete_powder": (220, 118, 45),  # 橙色混凝土粉末
        "minecraft:magenta_concrete_powder": (177, 76, 173), # 品红色混凝土粉末
        "minecraft:light_blue_concrete_powder": (76, 155, 206), # 淡蓝色混凝土粉末
        "minecraft:yellow_concrete_powder": (228, 195, 70),  # 黄色混凝土粉末
        "minecraft:lime_concrete_powder": (123, 185, 57),    # 黄绿色混凝土粉末
        "minecraft:pink_concrete_powder": (222, 148, 157),   # 粉红色混凝土粉末
        "minecraft:gray_concrete_powder": (78, 78, 78),      # 灰色混凝土粉末
        "minecraft:light_gray_concrete_powder": (152, 152, 147), # 淡灰色混凝土粉末
        "minecraft:cyan_concrete_powder": (35, 137, 157),    # 青色混凝土粉末
        "minecraft:purple_concrete_powder": (120, 70, 170),  # 紫色混凝土粉末
        "minecraft:blue_concrete_powder": (60, 70, 160),     # 蓝色混凝土粉末
        "minecraft:brown_concrete_powder": (114, 77, 48),    # 棕色混凝土粉末
        "minecraft:green_concrete_powder": (85, 108, 45),    # 绿色混凝土粉末
        "minecraft:red_concrete_powder": (162, 75, 68),      # 红色混凝土粉末
        "minecraft:black_concrete_powder": (25, 24, 26),     # 黑色混凝土粉末
        
        # 陶瓦
        "minecraft:white_terracotta": (210, 178, 161),     # 白色陶瓦
        "minecraft:orange_terracotta": (162, 84, 38),      # 橙色陶瓦
        "minecraft:magenta_terracotta": (150, 88, 109),    # 品红色陶瓦
        "minecraft:light_blue_terracotta": (114, 109, 138),# 淡蓝色陶瓦
        "minecraft:yellow_terracotta": (183, 133, 41),     # 黄色陶瓦
        "minecraft:lime_terracotta": (104, 118, 53),       # 黄绿色陶瓦
        "minecraft:pink_terracotta": (162, 78, 79),        # 粉红色陶瓦
        "minecraft:gray_terracotta": (58, 42, 36),         # 灰色陶瓦
        "minecraft:light_gray_terracotta": (136, 108, 98), # 淡灰色陶瓦
        "minecraft:cyan_terracotta": (87, 91, 91),         # 青色陶瓦
        "minecraft:purple_terracotta": (119, 71, 86),      # 紫色陶瓦
        "minecraft:blue_terracotta": (74, 60, 91),         # 蓝色陶瓦
        "minecraft:brown_terracotta": (77, 51, 36),        # 棕色陶瓦
        "minecraft:green_terracotta": (76, 84, 42),        # 绿色陶瓦
        "minecraft:red_terracotta": (143, 61, 47),         # 红色陶瓦
        "minecraft:black_terracotta": (37, 23, 16),        # 黑色陶瓦
        
        # 带釉陶瓦
        "minecraft:white_glazed_terracotta": (235, 238, 239),  # 白色带釉陶瓦
        "minecraft:orange_glazed_terracotta": (236, 120, 55),  # 橙色带釉陶瓦
        "minecraft:magenta_glazed_terracotta": (191, 84, 179), # 品红色带釉陶瓦
        "minecraft:light_blue_glazed_terracotta": (94, 169, 205), # 淡蓝色带釉陶瓦
        "minecraft:yellow_glazed_terracotta": (245, 220, 83),  # 黄色带釉陶瓦
        "minecraft:lime_glazed_terracotta": (118, 190, 86),    # 黄绿色带釉陶瓦
        "minecraft:pink_glazed_terracotta": (238, 155, 172),   # 粉红色带釉陶瓦
        "minecraft:gray_glazed_terracotta": (72, 68, 84),      # 灰色带釉陶瓦
        "minecraft:light_gray_glazed_terracotta": (159, 166, 166), # 淡灰色带釉陶瓦
        "minecraft:cyan_glazed_terracotta": (55, 136, 150),    # 青色带釉陶瓦
        "minecraft:purple_glazed_terracotta": (130, 75, 158),  # 紫色带釉陶瓦
        "minecraft:blue_glazed_terracotta": (35, 100, 160),    # 蓝色带釉陶瓦
        "minecraft:brown_glazed_terracotta": (140, 95, 65),    # 棕色带釉陶瓦
        "minecraft:green_glazed_terracotta": (100, 160, 45),   # 绿色带釉陶瓦
        "minecraft:red_glazed_terracotta": (195, 85, 85),      # 红色带釉陶瓦
        "minecraft:black_glazed_terracotta": (25, 25, 30),     # 黑色带釉陶瓦
        
        # 地毯
        "minecraft:white_carpet": (240, 240, 240),    # 白色地毯
        "minecraft:orange_carpet": (230, 120, 48),    # 橙色地毯
        "minecraft:magenta_carpet": (200, 80, 200),   # 品红色地毯
        "minecraft:light_blue_carpet": (120, 180, 225), # 淡蓝色地毯
        "minecraft:yellow_carpet": (255, 230, 74),    # 黄色地毯
        "minecraft:lime_carpet": (120, 200, 80),      # 黄绿色地毯
        "minecraft:pink_carpet": (230, 150, 165),     # 粉红色地毯
        "minecraft:gray_carpet": (85, 85, 85),        # 灰色地毯
        "minecraft:light_gray_carpet": (160, 160, 160), # 淡灰色地毯
        "minecraft:cyan_carpet": (40, 140, 165),      # 青色地毯
        "minecraft:purple_carpet": (130, 60, 190),    # 紫色地毯
        "minecraft:blue_carpet": (50, 60, 170),       # 蓝色地毯
        "minecraft:brown_carpet": (115, 75, 40),      # 棕色地毯
        "minecraft:green_carpet": (55, 120, 30),      # 绿色地毯
        "minecraft:red_carpet": (180, 60, 60),        # 红色地毯
        "minecraft:black_carpet": (40, 40, 40),       # 黑色地毯
        
        # 玻璃和玻璃板
        "minecraft:white_stained_glass": (220, 220, 220),  # 白色染色玻璃
        "minecraft:orange_stained_glass": (205, 140, 40),  # 橙色染色玻璃
        "minecraft:magenta_stained_glass": (170, 75, 180), # 品红色染色玻璃
        "minecraft:light_blue_stained_glass": (110, 150, 200), # 淡蓝色染色玻璃
        "minecraft:yellow_stained_glass": (205, 205, 60),  # 黄色染色玻璃
        "minecraft:lime_stained_glass": (140, 205, 75),    # 黄绿色染色玻璃
        "minecraft:pink_stained_glass": (200, 150, 170),   # 粉红色染色玻璃
        "minecraft:gray_stained_glass": (75, 75, 75),      # 灰色染色玻璃
        "minecraft:light_gray_stained_glass": (150, 150, 150), # 淡灰色染色玻璃
        "minecraft:cyan_stained_glass": (40, 150, 150),    # 青色染色玻璃
        "minecraft:purple_stained_glass": (120, 60, 170),  # 紫色染色玻璃
        "minecraft:blue_stained_glass": (40, 50, 190),    # 蓝色染色玻璃
        "minecraft:brown_stained_glass": (120, 85, 55),    # 棕色染色玻璃
        "minecraft:green_stained_glass": (80, 120, 45),   # 绿色染色玻璃
        "minecraft:red_stained_glass": (180, 50, 50),      # 红色染色玻璃
        "minecraft:black_stained_glass": (35, 35, 35),     # 黑色染色玻璃
        
        "minecraft:white_stained_glass_pane": (220, 220, 220),  # 白色染色玻璃板
        "minecraft:orange_stained_glass_pane": (205, 140, 40),  # 橙色染色玻璃板
        "minecraft:magenta_stained_glass_pane": (170, 75, 180), # 品红色染色玻璃板
        "minecraft:light_blue_stained_glass_pane": (110, 150, 200), # 淡蓝色染色玻璃板
        "minecraft:yellow_stained_glass_pane": (205, 205, 60),  # 黄色染色玻璃板
        "minecraft:lime_stained_glass_pane": (140, 205, 75),    # 黄绿色染色玻璃板
        "minecraft:pink_stained_glass_pane": (200, 150, 170),   # 粉红色染色玻璃板
        "minecraft:gray_stained_glass_pane": (75, 75, 75),      # 灰色染色玻璃板
        "minecraft:light_gray_stained_glass_pane": (150, 150, 150), # 淡灰色染色玻璃板
        "minecraft:cyan_stained_glass_pane": (40, 150, 150),    # 青色染色玻璃板
        "minecraft:purple_stained_glass_pane": (120, 60, 170),  # 紫色染色玻璃板
        "minecraft:blue_stained_glass_pane": (40, 50, 190),    # 蓝色染色玻璃板
        "minecraft:brown_stained_glass_pane": (120, 85, 55),    # 棕色染色玻璃板
        "minecraft:green_stained_glass_pane": (80, 120, 45),   # 绿色染色玻璃板
        "minecraft:red_stained_glass_pane": (180, 50, 50),      # 红色染色玻璃板
        "minecraft:black_stained_glass_pane": (35, 35, 35),     # 黑色染色玻璃板
        
        # 潜影盒
        "minecraft:white_shulker_box": (230, 230, 230),   # 白色潜影盒
        "minecraft:orange_shulker_box": (220, 110, 40),   # 橙色潜影盒
        "minecraft:magenta_shulker_box": (190, 70, 190),  # 品红色潜影盒
        "minecraft:light_blue_shulker_box": (110, 170, 220), # 淡蓝色潜影盒
        "minecraft:yellow_shulker_box": (223, 191, 53),   # 黄色潜影盒
        "minecraft:lime_shulker_box": (110, 185, 70),     # 黄绿色潜影盒
        "minecraft:pink_shulker_box": (215, 130, 150),    # 粉红色潜影盒
        "minecraft:gray_shulker_box": (75, 75, 75),       # 灰色潜影盒
        "minecraft:light_gray_shulker_box": (150, 150, 150), # 淡灰色潜影盒
        "minecraft:cyan_shulker_box": (30, 130, 155),     # 青色潜影盒
        "minecraft:purple_shulker_box": (120, 50, 180),   # 紫色潜影盒
        "minecraft:blue_shulker_box": (40, 50, 160),      # 蓝色潜影盒
        "minecraft:brown_shulker_box": (100, 65, 35),     # 棕色潜影盒
        "minecraft:green_shulker_box": (45, 110, 25),     # 绿色潜影盒
        "minecraft:red_shulker_box": (170, 55, 55),       # 红色潜影盒
        "minecraft:black_shulker_box": (30, 30, 30),      # 黑色潜影盒
        
        # 蜡烛
        "minecraft:white_candle": (240, 240, 240),        # 白色蜡烛
        "minecraft:orange_candle": (230, 120, 48),        # 橙色蜡烛
        "minecraft:magenta_candle": (200, 80, 200),       # 品红色蜡烛
        "minecraft:light_blue_candle": (120, 180, 225),   # 淡蓝色蜡烛
        "minecraft:yellow_candle": (255, 230, 74),        # 黄色蜡烛
        "minecraft:lime_candle": (120, 200, 80),          # 黄绿色蜡烛
        "minecraft:pink_candle": (230, 150, 165),         # 粉红色蜡烛
        "minecraft:gray_candle": (85, 85, 85),            # 灰色蜡烛
        "minecraft:light_gray_candle": (160, 160, 160),   # 淡灰色蜡烛
        "minecraft:cyan_candle": (40, 140, 165),          # 青色蜡烛
        "minecraft:purple_candle": (130, 60, 190),        # 紫色蜡烛
        "minecraft:blue_candle": (50, 60, 170),           # 蓝色蜡烛
        "minecraft:brown_candle": (115, 75, 40),          # 棕色蜡烛
        "minecraft:green_candle": (55, 120, 30),          # 绿色蜡烛
        "minecraft:red_candle": (180, 60, 60),            # 红色蜡烛
        "minecraft:black_candle": (40, 40, 40),           # 黑色蜡烛
        "minecraft:white_candle_lit": (255, 245, 240),    # 点燃的白色蜡烛
        "minecraft:orange_candle_lit": (255, 150, 60),    # 点燃的橙色蜡烛
        "minecraft:magenta_candle_lit": (220, 100, 220),  # 点燃的品红色蜡烛
        "minecraft:light_blue_candle_lit": (140, 200, 245), # 点燃的淡蓝色蜡烛
        "minecraft:yellow_candle_lit": (255, 240, 100),   # 点燃的黄色蜡烛
        "minecraft:lime_candle_lit": (140, 220, 100),     # 点燃的黄绿色蜡烛
        "minecraft:pink_candle_lit": (250, 170, 185),     # 点燃的粉红色蜡烛
        "minecraft:gray_candle_lit": (105, 105, 105),     # 点燃的灰色蜡烛
        "minecraft:light_gray_candle_lit": (180, 180, 180), # 点燃的淡灰色蜡烛
        "minecraft:cyan_candle_lit": (60, 160, 185),      # 点燃的青色蜡烛
        "minecraft:purple_candle_lit": (150, 80, 210),    # 点燃的紫色蜡烛
        "minecraft:blue_candle_lit": (70, 80, 190),       # 点燃的蓝色蜡烛
        "minecraft:brown_candle_lit": (135, 95, 60),      # 点燃的棕色蜡烛
        "minecraft:green_candle_lit": (75, 140, 50),      # 点燃的绿色蜡烛
        "minecraft:red_candle_lit": (200, 80, 80),        # 点燃的红色蜡烛
        "minecraft:black_candle_lit": (60, 60, 60),       # 点燃的黑色蜡烛
        
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
        
        # 下界植物
        "minecraft:warped_roots": (21, 180, 177),         # 诡异根
        "minecraft:warped_wart_block": (25, 151, 139),    # 诡异疣块
        "minecraft:weeping_vines": (153, 42, 47),         # 垂泪藤
        "minecraft:weeping_vines_plant": (148, 38, 43),   # 垂泪藤植物
        "minecraft:twisting_vines": (24, 120, 115),       # 扭曲藤
        "minecraft:twisting_vines_plant": (23, 110, 105), # 扭曲藤植物
        "minecraft:vine": (85, 130, 65),                  # 藤蔓
        
        # 铜块及其氧化变体
        "minecraft:weathered_copper": (108, 154, 91),     # 风化的铜块
        "minecraft:weathered_chiseled_copper": (112, 159, 95),  # 风化的錾制铜块
        "minecraft:weathered_cut_copper": (108, 150, 91),   # 风化的切制铜块
        "minecraft:weathered_copper_bulb": (110, 156, 93),  # 风化的铜灯泡
        "minecraft:weathered_copper_bulb_lit": (120, 166, 103),  # 点亮的风化铜灯泡
        "minecraft:weathered_copper_grate": (107, 148, 90),  # 风化的铜栅格
        "minecraft:weathered_copper_trapdoor": (109, 152, 92),  #.风化的铜活板门
        "minecraft:weathered_copper_door_bottom": (109, 153, 92),  # 风化的铜门底部
        "minecraft:weathered_copper_door_top": (110, 155, 93),     # 风化的铜门顶部
        
        # 诡异木材
        "minecraft:warped_stem": (43, 104, 99),           # 诡异木
        "minecraft:warped_slab": (40, 97, 95),            # 诡异木台阶
        "minecraft:warped_stairs": (42, 100, 97),         # 诡异木楼梯
        "minecraft:warped_trapdoor": (41, 98, 94),        # 诡异木活板门
        "minecraft:warped_door_bottom": (43, 101, 97),    # 诡异木门底部
        "minecraft:warped_door_top": (44, 103, 98),       # 诡异木门顶部
        "minecraft:warped_planks": (43, 104, 99),         # 诡异木板
        "minecraft:warped_stem_top": (55, 110, 105),      # 诡异木顶端
        "minecraft:warped_nylium": (41, 100, 98),         # 诡异菌岩
        "minecraft:warped_nylium_side": (47, 104, 100),   # 诡异菌岩侧面
        "minecraft:warped_fungus": (28, 120, 120),        # 诡异菌
        
        # 特殊方块
        "minecraft:wet_sponge": (171, 167, 83),           # 湿海绵
        "minecraft:water_cauldron": (52, 79, 132),        # 装满水的炼药锅
        
        # 珊瑚方块
        "minecraft:tube_coral_block": (51, 121, 198),     # 管珊瑚块
        "minecraft:tube_coral": (45, 118, 191),           # 管珊瑚
        "minecraft:tube_coral_fan": (49, 120, 195),       # 管珊瑚扇
        "minecraft:brain_coral_block": (226, 136, 186),   # 脑珊瑚块
        "minecraft:brain_coral": (220, 130, 180),         # 脑珊瑚
        "minecraft:brain_coral_fan": (223, 133, 183),     # 脑珊瑚扇
        "minecraft:bubble_coral_block": (161, 75, 175),   # 气泡珊瑚块
        "minecraft:bubble_coral": (155, 70, 170),         # 气泡珊瑚
        "minecraft:bubble_coral_fan": (158, 72, 172),     # 气泡珊瑚扇
        "minecraft:fire_coral_block": (196, 54, 53),      # 火珊瑚块
        "minecraft:fire_coral": (190, 50, 50),            # 火珊瑚
        "minecraft:fire_coral_fan": (193, 52, 51),        # 火珊瑚扇
        "minecraft:horn_coral_block": (225, 197, 24),     # 角珊瑚块
        "minecraft:horn_coral": (220, 193, 20),           # 角珊瑚
        "minecraft:horn_coral_fan": (222, 195, 22),       # 角珊瑚扇
        "minecraft:dead_tube_coral_block": (131, 123, 116), # 死亡管珊瑚块
        "minecraft:dead_brain_coral_block": (129, 121, 114), # 死亡脑珊瑚块
        "minecraft:dead_bubble_coral_block": (130, 122, 115), # 死亡气泡珊瑚块
        "minecraft:dead_fire_coral_block": (132, 124, 117),   # 死亡火珊瑚块
        "minecraft:dead_horn_coral_block": (133, 125, 118),   # 死亡角珊瑚块
        
        # 海龟蛋
        "minecraft:turtle_egg": (216, 226, 215),          # 海龟蛋
        "minecraft:turtle_egg_slightly_cracked": (214, 224, 213), # 轻微破裂的海龟蛋
        "minecraft:turtle_egg_very_cracked": (212, 222, 211),    # 严重破裂的海龟蛋
        
        # 发光蛙晶体
        "minecraft:verdant_froglight_top": (180, 212, 146), # 青翠蛙光顶部
        "minecraft:verdant_froglight_side": (170, 205, 136), # 青翠蛙光侧面
        "minecraft:ochre_froglight_top": (216, 197, 100),   # 赭色蛙光顶部
        "minecraft:ochre_froglight_side": (206, 187, 95),   # 赭色蛙光侧面
        "minecraft:pearlescent_froglight_top": (213, 213, 223), # 珠光蛙光顶部
        "minecraft:pearlescent_froglight_side": (203, 203, 213), # 珠光蛙光侧面
        
        # 金库与试炼刷怪笼
        "minecraft:vault_top": (210, 210, 210),           # 金库顶部
        "minecraft:vault_bottom": (120, 120, 120),        # 金库底部
        "minecraft:vault_front_off": (190, 190, 190),     # 关闭的金库前端
        "minecraft:vault_front_on": (210, 210, 210),      # 开启的金库前端
        "minecraft:vault_side_off": (180, 180, 180),      # 关闭的金库侧面
        "minecraft:vault_side_on": (200, 200, 200),       # 开启的金库侧面
        "minecraft:vault_top_ominous": (190, 170, 170),   # 不祥金库顶部
        "minecraft:vault_bottom_ominous": (110, 90, 90),  # 不祥金库底部
        "minecraft:vault_front_off_ominous": (170, 150, 150), # 关闭的不祥金库前端
        "minecraft:vault_front_on_ominous": (190, 170, 170),  # 开启的不祥金库前端
        "minecraft:trial_spawner_top_inactive": (160, 160, 160), # 未激活的试炼刷怪笼顶部
        "minecraft:trial_spawner_top_active": (180, 160, 160),   # 激活的试炼刷怪笼顶部
        "minecraft:trial_spawner_top_inactive_ominous": (150, 130, 130), # 不祥未激活的试炼刷怪笼顶部
        "minecraft:trial_spawner_top_active_ominous": (170, 150, 150),   # 不祥激活的试炼刷怪笼顶部
        
        # 凝灰岩
        "minecraft:tuff": (109, 106, 97),                # 凝灰岩
        "minecraft:tuff_bricks": (114, 111, 102),        # 凝灰岩砖
        "minecraft:chiseled_tuff": (117, 114, 105),      # 錾制凝灰岩
        "minecraft:tuff_slab": (112, 109, 100),          # 凝灰岩台阶
        "minecraft:tuff_stairs": (110, 107, 98),         # 凝灰岩楼梯
        
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
        self.colors = self.DEFAULT_COLORS.copy()
        self.resource_dir = resource_dir
        
        # 如果提供了资源目录，尝试加载自定义颜色配置
        if resource_dir:
            self.load_color_map(resource_dir)
    
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
        # 先直接查询颜色字典
        if block_id in self.colors:
            return self.colors[block_id]
        
        # 如果找不到精确匹配，尝试使用正则模式匹配
        return self._try_pattern_match(block_id)

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
            
        # 颜色正则匹配规则
        color_patterns = {
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
            r'terracotta$': (160, 84, 49),   # 陶瓦系统
            r'coral': (180, 180, 180),       # 珊瑚系列
            
            # 特殊方块匹配
            r'log': (114, 84, 48),           # 原木
            r'planks': (160, 115, 80),       # 木板
            r'leaves': (65, 102, 48),        # 树叶
            r'glass': (210, 239, 243),       # 玻璃
            r'ice': (150, 200, 255),         # 冰块
            r'wool': (240, 240, 240),        # 羊毛
            r'concrete': (128, 128, 128),    # 混凝土
            r'shulker': (140, 100, 160),     # 潜影盒
            r'door': (160, 115, 80),         # 门
            r'trapdoor': (160, 115, 80),     # 活板门
            r'slab': (160, 115, 80),         # 台阶
            r'stairs': (160, 115, 80),       # 楼梯
            r'fence': (160, 115, 80),        # 栅栏
            r'wall': (128, 128, 128),        # 墙
            r'ore': (128, 128, 128),         # 矿石
        }
        
        # 尝试匹配规则
        for pattern, color in color_patterns.items():
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