from PIL import Image, ImageDraw

class SpecialBlockRenderer:
    """特殊方块渲染器，用于处理需要特殊变换的方块材质"""
    
    def __init__(self):
        self._init_transform_methods()
        
    def _init_transform_methods(self):
        """初始化变换方法映射表"""
        self._transform_methods = {
            "transform_hopper_side": self.transform_hopper_side,
            "transform_hopper_bottom": self.transform_hopper_bottom,
            "transform_observer_front": self.transform_observer_front,
            "transform_piston_extended": self.transform_piston_extended,
            "transform_comparator_top": self.transform_comparator_top,
            "transform_ore_block": self.transform_ore_block,
            "transform_door_top": self.transform_door_top,
        }
    
    def get_transform_method(self, method_name):
        """根据方法名获取对应的变换方法"""
        return self._transform_methods.get(method_name)
    
    @staticmethod
    def transform_hopper_side(source_image):
        """变换漏斗侧面材质 - 裁剪出倒三角形区域"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
                
            width, height = source_image.size
            
            result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            mask = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(mask)
            
            draw.polygon([(0, 0), (width, 0), (width//2, height)], fill=255)
            
            result.paste(source_image, (0, 0), mask)
            
            return result
        except Exception:
            return source_image if source_image else None
    
    @staticmethod
    def transform_hopper_bottom(source_image):
        """变换漏斗底部材质 - 创建一个简单的漏斗底部图案"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
            
            width, height = source_image.size
            
            result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            
            center_size = min(width, height) // 3
            center_box = (
                (width - center_size) // 2,
                (height - center_size) // 2,
                (width + center_size) // 2,
                (height + center_size) // 2
            )
            
            center = (width // 2, height // 2)
            
            top_mid = (width // 2, 0)
            right_mid = (width, height // 2)
            bottom_mid = (width // 2, height)
            left_mid = (0, height // 2)
            
            top_left = (0, 0)
            top_right = (width, 0)
            bottom_right = (width, height)
            bottom_left = (0, height)
            
            mask = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(mask)
            
            triangles = [
                (center, top_left, top_mid, 192),
                (center, top_mid, top_right, 192),
                (center, top_right, right_mid, 160),
                (center, right_mid, bottom_right, 160),
                (center, bottom_right, bottom_mid, 128),
                (center, bottom_mid, bottom_left, 128),
                (center, bottom_left, left_mid, 96),
                (center, left_mid, top_left, 96)
            ]
            
            for points in triangles:
                draw.polygon(points[:-1], fill=points[-1])
            
            triangle_source = source_image.copy()
            result.paste(triangle_source, (0, 0), mask)
            
            center_mask = Image.new("L", (width, height), 0)
            center_draw = ImageDraw.Draw(center_mask)
            center_draw.rectangle(center_box, fill=255)
            
            center_image = source_image.resize((center_size, center_size), Image.Resampling.NEAREST)
            result.paste(center_image, (center_box[0], center_box[1]), center_mask)
            
            return result.convert("RGBA")
        except Exception:
            return source_image.convert("RGBA") if source_image.mode != "RGBA" else source_image

    @staticmethod
    def transform_observer_front(source_image):
        """变换观察者方块前端材质"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
                
            return source_image
        except Exception:
            return source_image
    
    @staticmethod
    def transform_piston_extended(source_image):
        """变换活塞伸展状态材质"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
            
            return source_image
        except Exception:
            return source_image

    @staticmethod
    def transform_comparator_top(source_image, is_powered=False):
        """变换红石比较器顶部材质"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
            
            return source_image
        except Exception:
            return source_image

    @staticmethod
    def transform_ore_block(source_image, ore_type=None):
        """处理矿石方块的特殊材质效果"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
            
            return source_image
        except Exception:
            return source_image
    
    @staticmethod
    def transform_door_top(source_image):
        """变换门顶部材质"""
        try:
            if source_image.mode != "RGBA":
                source_image = source_image.convert("RGBA")
            
            return source_image
        except Exception:
            return source_image
