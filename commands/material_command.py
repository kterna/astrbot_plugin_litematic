import os
import traceback
from typing import Dict, Optional, Tuple, List
from astrbot import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from litemapy import Schematic
from ..services.file_manager import FileManager
from ..services.category_manager import CategoryManager
from ..core.material.material import Material
from ..utils.types import CategoryType, FilePath, BlockCounts, EntityCounts, MessageResponse, BlockId
from ..utils.exceptions import (
    CategoryNotFoundError, 
    FileNotFoundError, 
    LitematicPluginError,
    InvalidArgumentError
)
from ..utils.logging_utils import log_error, log_operation

class MaterialCommand:
    def __init__(self, file_manager: FileManager, category_manager: CategoryManager) -> None:
        self.file_manager: FileManager = file_manager
        self.category_manager: CategoryManager = category_manager
    
    async def execute(self, event: AstrMessageEvent, category: CategoryType = "", filename: str = "") -> MessageResponse:
        """
        分析litematic文件所需材料
        使用方法：
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
        
        Args:
            event: 消息事件
            category: 分类名称，默认为空字符串
            filename: 文件名，默认为空字符串
            
        Yields:
            MessageChain: 响应消息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影材料 建筑 house.litematic")
            return
        
        try:
            # 加载litematic文件
            yield event.plain_result("正在分析材料清单，请稍候...")
            
            # 获取文件路径
            file_path: FilePath = self.file_manager.get_litematic_file(category, filename)
            
            # 使用Material类分析文件
            schematic: Schematic = Schematic.load(file_path)
            material_analyzer: Material = Material("材料分析", 0)
            
            # 获取方块和实体统计
            block_counts: BlockCounts = material_analyzer.block_collection(schematic)
            entity_counts: EntityCounts = material_analyzer.entity_collection(schematic)
            tile_counts: Dict[str, int] = material_analyzer.tile_collection(schematic)
            
            # 格式化结果
            result: str = f"【{os.path.basename(file_path)}】材料清单：\n\n"
            
            # 添加方块信息
            if block_counts:
                result += "方块材料：\n"
                sorted_blocks: List[Tuple[BlockId, int]] = sorted(block_counts.items(), key=lambda item: item[1], reverse=True)
                for block_id, count in sorted_blocks:
                    result += f"- {block_id[10:]}: {count}个\n"
            else:
                result += "无方块材料\n"
            
            # 添加实体信息
            if entity_counts:
                result += "\n实体：\n"
                sorted_entities: List[Tuple[str, int]] = sorted(entity_counts.items(), key=lambda item: item[1], reverse=True)
                for entity_id, count in sorted_entities:
                    result += f"- {entity_id}: {count}个\n"
            
            # 添加方块实体信息
            if tile_counts:
                result += "\n方块实体：\n"
                sorted_tiles: List[Tuple[str, int]] = sorted(tile_counts.items(), key=lambda item: item[1], reverse=True)
                for tile_id, count in sorted_tiles:
                    # 确保正确显示，处理不同类型的tile_id
                    if isinstance(tile_id, tuple) and len(tile_id) > 0:
                        result += f"- {tile_id[0]}: {count}个\n"
                    else:
                        result += f"- {tile_id}: {count}个\n"
            
            log_operation("分析材料", True, {"category": category, "filename": filename})
            yield event.plain_result(result)
            
        except FileNotFoundError as e:
            log_error(e)
            yield event.plain_result(e.message)
        except CategoryNotFoundError as e:
            log_error(e)
            yield event.plain_result(e.message)
        except InvalidArgumentError as e:
            log_error(e)
            yield event.plain_result(e.message)
        except LitematicPluginError as e:
            log_error(e, extra_info={"category": category, "filename": filename})
            yield event.plain_result(f"分析材料失败: {e.message}")
        except Exception as e:
            error_details = {"category": category, "filename": filename, "error": str(e), "traceback": traceback.format_exc()}
            log_error(e, extra_info=error_details)
            yield event.plain_result(f"分析材料时出现错误: {str(e)}") 