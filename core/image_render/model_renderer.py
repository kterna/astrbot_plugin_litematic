import math
from PIL import Image, ImageDraw
from typing import Dict, List, Tuple, Any, Optional
from .texture_manager import TextureManager
from astrbot import logger  # 添加logger导入

class ModelRenderer:
    """方块模型渲染器"""
    
    def __init__(self, texture_manager: TextureManager) -> None:
        """初始化渲染器
        
        Args:
            texture_manager: 纹理管理器
        """
        self.texture_manager = texture_manager
        
    def render_model_face(self, model_data: Dict[str, Any], face_name: str,
                         scale: int = 1) -> Optional[Image.Image]:
        """渲染模型的指定面
        
        Args:
            model_data: 模型数据
            face_name: 面名称(north/south/east/west/up/down)
            scale: 缩放比例
            
        Returns:
            Optional[Image.Image]: 渲染的图像，失败返回None
        """
        try:
            if "elements" not in model_data:
                logger.debug(f"模型数据中缺少elements字段: {str(model_data)[:100]}...")
                return None
                
            # 创建透明画布
            size = 16 * scale
            image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            
            # 处理每个元素
            for idx, element in enumerate(model_data["elements"]):
                try:
                    if "faces" not in element:
                        logger.debug(f"元素{idx}中缺少faces字段")
                        continue
                        
                    if face_name not in element["faces"]:
                        continue
                        
                    face_data = element["faces"][face_name]
                    
                    # 获取纹理
                    texture_ref = face_data.get("texture", "")
                    if not texture_ref:
                        logger.debug(f"元素{idx}的{face_name}面缺少texture字段")
                        continue
                        
                    # 获取纹理图像
                    try:
                        texture = self.get_texture_from_model(model_data, texture_ref)
                    except Exception as tex_err:
                        logger.error(f"获取纹理失败 [{texture_ref}]: {str(tex_err)}")
                        continue
                    
                    # 获取UV坐标，默认为整个纹理
                    uv = face_data.get("uv", [0, 0, 16, 16])
                    
                    # 获取元素几何信息
                    from_coords = element.get("from", [0, 0, 0])
                    to_coords = element.get("to", [16, 16, 16])
                    
                    # 根据面方向计算绘制区域
                    draw_area = self._calculate_face_area(face_name, from_coords, to_coords)
                    
                    # 剪裁纹理
                    try:
                        cropped_texture = self._crop_texture(texture, uv)
                    except Exception as crop_err:
                        logger.error(f"裁剪纹理失败: {str(crop_err)}, UV={uv}")
                        continue
                    
                    # 获取方块朝向（如果有）
                    block_facing = model_data.get("facing", None)
                    
                    # 应用旋转：根据视图类型和方块朝向计算旋转角度，不再直接从face_data获取
                    rotation = self._calculate_rotation(face_name, block_facing)
                    if rotation != 0:
                        try:
                            cropped_texture = cropped_texture.rotate(-rotation, expand=True)
                        except Exception as rot_err:
                            logger.error(f"旋转纹理失败: {str(rot_err)}, rotation={rotation}")
                            continue
                    
                    # 缩放纹理
                    if scale != 1:
                        try:
                            target_size = (
                                round((draw_area[2] - draw_area[0]) * scale),
                                round((draw_area[3] - draw_area[1]) * scale)
                            )
                            if target_size[0] <= 0 or target_size[1] <= 0:
                                logger.error(f"无效的目标尺寸: {target_size}, draw_area={draw_area}, scale={scale}")
                                continue
                            cropped_texture = cropped_texture.resize(target_size, Image.Resampling.NEAREST)
                            draw_area = [c * scale for c in draw_area]
                        except Exception as scale_err:
                            logger.error(f"缩放纹理失败: {str(scale_err)}, target_size={target_size}")
                            continue
                    
                    # 合成到画布上
                    try:
                        image.paste(
                            cropped_texture,
                            (round(draw_area[0]), round(draw_area[1])),
                            cropped_texture
                        )
                    except Exception as paste_err:
                        logger.error(f"粘贴纹理失败: {str(paste_err)}, 位置=({round(draw_area[0])}, {round(draw_area[1])})")
                        continue
                except Exception as element_err:
                    logger.error(f"处理元素{idx}时发生错误: {str(element_err)}")
                    continue
            
            return image
        except Exception as render_err:
            logger.error(f"渲染模型面失败[{face_name}]: {str(render_err)}")
            return None
    
    def get_texture_from_model(self, model_data: Dict[str, Any], texture_var: str) -> Image.Image:
        """根据模型数据获取纹理
        
        Args:
            model_data: 模型数据
            texture_var: 纹理变量，如#top或top
            
        Returns:
            Image.Image: 纹理图像
        """
        try:
            # 检查纹理变量是否以#开头(引用其他纹理)
            if texture_var.startswith("#"):
                texture_var = texture_var[1:]
                
            # 从模型纹理映射中获取实际纹理名
            if "textures" in model_data and texture_var in model_data["textures"]:
                texture_path = model_data["textures"][texture_var]
                
                # 再次检查是否是引用
                if texture_path.startswith("#"):
                    return self.get_texture_from_model(model_data, texture_path)
                    
                # 处理minecraft:命名空间
                if texture_path.startswith("minecraft:"):
                    texture_path = texture_path[10:]
                    
                # 处理block/前缀
                if texture_path.startswith("block/"):
                    texture_name = texture_path[6:]
                else:
                    texture_name = texture_path
                    
                # 加载纹理
                return self.texture_manager.get_texture(texture_name)
            
            # 如果找不到匹配的纹理，返回默认纹理
            logger.debug(f"找不到纹理变量 [{texture_var}] 的映射，使用默认纹理")
            return self.texture_manager.default_texture
        except Exception as err:
            logger.error(f"获取模型纹理时出错 [{texture_var}]: {str(err)}")
            return self.texture_manager.default_texture
    
    def _crop_texture(self, texture: Image.Image, uv: List[float]) -> Image.Image:
        """根据UV坐标剪裁纹理
        
        Args:
            texture: 原始纹理
            uv: UV坐标 [u1, v1, u2, v2]
            
        Returns:
            Image.Image: 剪裁后的纹理
        """
        try:
            # 归一化UV坐标到纹理大小
            texture_size = texture.width
            u1 = (uv[0] / 16.0) * texture_size
            v1 = (uv[1] / 16.0) * texture_size
            u2 = (uv[2] / 16.0) * texture_size
            v2 = (uv[3] / 16.0) * texture_size
            
            # 确保坐标有效
            u1, u2 = min(u1, u2), max(u1, u2)
            v1, v2 = min(v1, v2), max(v1, v2)
            
            # 确保坐标在纹理范围内
            u1 = max(0, min(texture_size-1, u1))
            v1 = max(0, min(texture_size-1, v1))
            u2 = max(0, min(texture_size, u2))
            v2 = max(0, min(texture_size, v2))
            
            # 确保剪裁区域有效
            if u2 <= u1 or v2 <= v1:
                logger.warning(f"无效的UV坐标: {uv}, 调整后: [{u1}, {v1}, {u2}, {v2}]")
                return texture
            
            # 剪裁纹理
            return texture.crop((int(u1), int(v1), int(u2), int(v2)))
        except Exception as e:
            logger.error(f"裁剪纹理失败: {str(e)}, UV={uv}, 纹理尺寸={texture.size if texture else 'None'}")
            return texture
    
    def _calculate_face_area(self, face_name: str, from_coords: List[float],
                           to_coords: List[float]) -> List[float]:
        """计算面在2D平面上的绘制区域
        
        Args:
            face_name: 面名称
            from_coords: 元素起始坐标 [x, y, z]
            to_coords: 元素结束坐标 [x, y, z]
            
        Returns:
            List[float]: 绘制区域 [x1, y1, x2, y2]
        """
        try:
            if face_name == "north":
                return [from_coords[0], 16 - to_coords[1], to_coords[0], 16 - from_coords[1]]
            elif face_name == "south":
                return [16 - to_coords[0], 16 - to_coords[1], 16 - from_coords[0], 16 - from_coords[1]]
            elif face_name == "east":
                return [16 - to_coords[2], 16 - to_coords[1], 16 - from_coords[2], 16 - from_coords[1]]
            elif face_name == "west":
                return [from_coords[2], 16 - to_coords[1], to_coords[2], 16 - from_coords[1]]
            elif face_name == "up":
                return [from_coords[0], from_coords[2], to_coords[0], to_coords[2]]
            elif face_name == "down":
                return [from_coords[0], 16 - to_coords[2], to_coords[0], 16 - from_coords[2]]
            logger.warning(f"未知的面名称: {face_name}")
            return [0, 0, 16, 16]  # 默认占满整个区域
        except Exception as e:
            logger.error(f"计算面区域失败: {str(e)}, face={face_name}, from={from_coords}, to={to_coords}")
            return [0, 0, 16, 16]  # 出错时返回默认区域 
    
    def _calculate_rotation(self, view: str, facing: Optional[str]) -> int:
        """计算纹理旋转角度
        
        Args:
            view: 视图类型 (north/south/east/west/up/down)
            facing: 方块朝向 (north/south/east/west/up/down)
            
        Returns:
            int: 旋转角度（顺时针度数）
        """
        # 如果没有朝向，不旋转
        if facing is None:
            return 0
            
        # 用于计算最终旋转角度的映射
        rotation_mapping = {
            # 俯视图 (top view)
            'up': {
                'north': 0,    # 北向方块不旋转
                'east': 90,    # 东向方块顺时针旋转90度
                'south': 180,  # 南向方块顺时针旋转180度
                'west': 270,   # 西向方块顺时针旋转270度
            },
            # 底视图 (bottom view)
            'down': {
                'north': 180,  # 北向方块顺时针旋转180度
                'east': 270,   # 东向方块顺时针旋转270度
                'south': 0,    # 南向方块不旋转
                'west': 90,    # 西向方块顺时针旋转90度
            },
            # 北视图 (north view)
            'north': {
                'up': 0,      # 上向方块不旋转
                'east': 90,   # 东向方块顺时针旋转90度
                'down': 180,  # 下向方块顺时针旋转180度
                'west': 270,  # 西向方块顺时针旋转270度
            },
            # 南视图 (south view)
            'south': {
                'up': 0,      # 上向方块不旋转
                'west': 90,   # 西向方块顺时针旋转90度
                'down': 180,  # 下向方块顺时针旋转180度
                'east': 270,  # 东向方块顺时针旋转270度
            },
            # 东视图 (east view)
            'east': {
                'up': 0,      # 上向方块不旋转
                'south': 90,  # 南向方块顺时针旋转90度
                'down': 180,  # 下向方块顺时针旋转180度
                'north': 270, # 北向方块顺时针旋转270度
            },
            # 西视图 (west view)
            'west': {
                'up': 0,      # 上向方块不旋转
                'north': 90,  # 北向方块顺时针旋转90度
                'down': 180,  # 下向方块顺时针旋转180度
                'south': 270, # 南向方块顺时针旋转270度
            }
        }
        
        # 特殊处理：MC常见的面映射
        view_mapping = {
            'top': 'up',
            'front': 'north',
            'side': 'east'
        }
        
        # 应用视图映射
        mapped_view = view_mapping.get(view, view)
        
        # 如果视图类型和朝向组合存在于映射中，返回对应旋转角度
        if mapped_view in rotation_mapping and facing in rotation_mapping[mapped_view]:
            return rotation_mapping[mapped_view][facing]
            
        # 默认不旋转
        return 0 