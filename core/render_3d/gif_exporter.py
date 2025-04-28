import os
import tempfile
from typing import List, Dict, Any, Optional
from PIL import Image

class GifExporter:
    """
    将图像帧序列导出为GIF动画
    """
    
    def __init__(self) -> None:
        """初始化GIF导出器"""
        self.config = {
            'duration': 100,       # 每帧持续时间（毫秒）
            'loop': 0,             # 循环次数（0表示无限循环）
            'optimize': False,      # 优化GIF
            'quality': 100,         # 质量（越高越好，但文件也越大）
            'disposal': 2          # 帧处理方式（2表示恢复到背景）
        }
    
    def export_gif(self, frames: List[Image.Image], output_path: str,
                  duration: Optional[int] = None, loop: Optional[int] = None,
                  optimize: Optional[bool] = None, quality: Optional[int] = None) -> bool:
        """
        将帧序列导出为GIF
        
        Args:
            frames: 图像帧列表
            output_path: 输出文件路径
            duration: 每帧持续时间（毫秒）
            loop: 循环次数（0表示无限循环）
            optimize: 是否优化GIF
            quality: 质量（1-100）
            
        Returns:
            bool: 是否成功导出
        """
        try:
            if not frames or len(frames) == 0:
                print("没有帧可以导出")
                return False
            
            # 更新配置
            config = self.config.copy()
            if duration is not None:
                config['duration'] = duration
            if loop is not None:
                config['loop'] = loop
            if optimize is not None:
                config['optimize'] = optimize
            if quality is not None:
                config['quality'] = quality
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 导出GIF
            frames[0].save(
                output_path,
                format='GIF',
                append_images=frames[1:],
                save_all=True,
                duration=config['duration'],
                loop=config['loop'],
                optimize=config['optimize'],
                quality=config['quality'],
                disposal=config['disposal']
            )
            
            return True
            
        except Exception as e:
            print(f"导出GIF时出错: {e}")
            return False
    
    def export_gif_with_temp(self, frames: List[Image.Image], duration: int = 100) -> Optional[str]:
        """
        将帧序列导出为临时GIF文件
        
        Args:
            frames: 图像帧列表
            duration: 每帧持续时间（毫秒）
            
        Returns:
            Optional[str]: 临时文件路径，如果失败则返回None
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp:
                temp_path = tmp.name
            
            # 导出到临时文件
            success = self.export_gif(frames, temp_path, duration=duration)
            
            if success:
                return temp_path
            else:
                # 如果失败，删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
                
        except Exception as e:
            print(f"创建临时GIF文件时出错: {e}")
            return None
    
    def resize_frames(self, frames: List[Image.Image], width: int, height: int) -> List[Image.Image]:
        """
        调整所有帧的大小
        
        Args:
            frames: 图像帧列表
            width: 新宽度
            height: 新高度
            
        Returns:
            List[Image.Image]: 调整大小后的帧列表
        """
        resized_frames = []
        
        for frame in frames:
            resized = frame.resize((width, height), Image.LANCZOS)
            resized_frames.append(resized)
            
        return resized_frames
    
    def optimize_gif_size(self, frames: List[Image.Image], max_size: int) -> List[Image.Image]:
        """
        优化GIF大小
        
        根据最大文件大小限制，将所有帧调整为固定的最大尺寸
        
        Args:
            frames: 图像帧列表
            max_size: 最大文件大小（字节）
            
        Returns:
            List[Image.Image]: 优化后的帧列表
        """
        if not frames:
            return []
        
        # 固定输出尺寸
        FIXED_WIDTH = 1920
        FIXED_HEIGHT = 1080
        
        # 调整所有帧的大小为固定尺寸
        return self.resize_frames(frames, FIXED_WIDTH, FIXED_HEIGHT)
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config: 新的配置字典
        """
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value 