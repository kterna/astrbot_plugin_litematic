import os
import tempfile
from typing import List, Dict, Any, Optional, Iterable, Tuple
from PIL import Image
import numpy as np

class GifExporter:
    """
    将图像帧序列导出为GIF动画
    """
    
    def __init__(self) -> None:
        """初始化GIF导出器"""
        self.config = {
            'duration': 100,       # 每帧持续时间（毫秒）
            'loop': 0,             # 循环次数（0表示无限循环）
            'optimize': True,      # 优化GIF
            'quality': 80,         # 质量（越高越好，但文件也越大）
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
    
    def export_gif_stream(self, frames: Iterable[Image.Image], output_path: str,
                          duration: Optional[int] = None, loop: Optional[int] = None,
                          optimize: Optional[bool] = None, quality: Optional[int] = None,
                          resize_to: Optional[Tuple[int, int]] = None) -> bool:
        """
        将帧序列以流式方式导出为GIF

        Args:
            frames: 图像帧迭代器
            output_path: 输出文件路径
            duration: 每帧持续时间（毫秒）
            loop: 循环次数（0表示无限循环）
            optimize: 是否优化GIF
            quality: 质量（1-100）
            resize_to: 目标分辨率(width, height)

        Returns:
            bool: 是否成功导出
        """
        try:
            frames_iter = iter(frames)
            first_frame = next(frames_iter)
        except StopIteration:
            print("没有帧可以导出")
            return False
        except Exception as e:
            print(f"读取帧时出错: {e}")
            return False

        try:
            # 更新配置
            config = self.config.copy()
            if duration is not None:
                config["duration"] = duration
            if loop is not None:
                config["loop"] = loop
            if optimize is not None:
                config["optimize"] = optimize
            if quality is not None:
                config["quality"] = quality

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            if resize_to:
                first_frame = first_frame.resize(resize_to, Image.LANCZOS)

            imageio_result = self._export_with_imageio(
                first_frame, frames_iter, output_path,
                config["duration"], config["loop"], resize_to
            )
            if imageio_result is True:
                return True
            if imageio_result is False:
                return False

            def iter_frames() -> Iterable[Image.Image]:
                for frame in frames_iter:
                    if resize_to:
                        frame = frame.resize(resize_to, Image.LANCZOS)
                    yield frame

            first_frame.save(
                output_path,
                format="GIF",
                append_images=iter_frames(),
                save_all=True,
                duration=config["duration"],
                loop=config["loop"],
                optimize=config["optimize"],
                quality=config["quality"],
                disposal=config["disposal"]
            )

            return True

        except Exception as e:
            print(f"导出GIF时出错: {e}")
            return False

    def _export_with_imageio(self, first_frame: Image.Image, frames_iter: Iterable[Image.Image],
                             output_path: str, duration: int, loop: int,
                             resize_to: Optional[Tuple[int, int]] = None) -> Optional[bool]:
        try:
            import imageio.v2 as imageio
        except Exception:
            return None

        try:
            duration_sec = max(0.01, duration / 1000.0)
            with imageio.get_writer(output_path, mode="I", duration=duration_sec, loop=loop) as writer:
                writer.append_data(np.array(first_frame.convert("RGBA")))
                for frame in frames_iter:
                    if resize_to:
                        frame = frame.resize(resize_to, Image.LANCZOS)
                    writer.append_data(np.array(frame.convert("RGBA")))
            return True
        except Exception:
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
    
    def export_gif_with_temp_stream(self, frames: Iterable[Image.Image],
                                    duration: int = 100,
                                    resize_to: Optional[Tuple[int, int]] = None) -> Optional[str]:
        """
        将帧序列导出为临时GIF文件（流式写入）

        Args:
            frames: 图像帧迭代器
            duration: 每帧持续时间（毫秒）
            resize_to: 目标分辨率(width, height)

        Returns:
            Optional[str]: 临时文件路径，如果失败则返回None
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
                temp_path = tmp.name

            success = self.export_gif_stream(
                frames, temp_path, duration=duration, resize_to=resize_to
            )

            if success:
                return temp_path

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
    
    def estimate_scaled_size(self, width: int, height: int, frame_count: int,
                             max_size: int) -> Optional[Tuple[int, int]]:
        """
        根据目标大小估算缩放后的分辨率
        """
        if frame_count <= 0:
            return None

        bytes_per_pixel = 0.25
        estimated_size = width * height * bytes_per_pixel * frame_count
        if estimated_size <= max_size:
            return None

        scale_factor = (max_size / estimated_size) ** 0.5
        new_width = max(1, int(width * scale_factor))
        new_height = max(1, int(height * scale_factor))
        return (new_width, new_height)

    def optimize_gif_size(self, frames: List[Image.Image], max_size: int) -> List[Image.Image]:
        """
        优化GIF大小

        如果预计的GIF大小超过max_size（以字节为单位），
        则尝试通过降低分辨率来减小大小

        Args:
            frames: 图像帧列表
            max_size: 最大文件大小（字节）

        Returns:
            List[Image.Image]: 优化后的帧列表
        """
        if not frames:
            return []

        width, height = frames[0].size
        resize_to = self.estimate_scaled_size(width, height, len(frames), max_size)
        if not resize_to:
            return frames

        return self.resize_frames(frames, resize_to[0], resize_to[1])

    def set_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config: 新的配置字典
        """
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value 