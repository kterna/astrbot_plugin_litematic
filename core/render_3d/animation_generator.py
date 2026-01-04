import os
import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Iterable
from PIL import Image

class AnimationGenerator:
    """
    生成3D模型的动画序列
    """
    
    def __init__(self, renderer: Any) -> None:
        """
        初始化动画生成器
        
        Args:
            renderer: 3D渲染器对象
        """
        self.renderer = renderer
        self.frames: List[Image.Image] = []
    
    def iter_rotation_frames(self, n_frames: int = 36, elevation: float = 30.0,
                             distance_factor: float = 2.0,
                             window_size: Optional[Tuple[int, int]] = None) -> Iterable[Image.Image]:
        """
        流式生成围绕模型旋转的帧序列
        """
        try:
            bounds = self.renderer.model_data["bounds"]
            center_x = (bounds["min_x"] + bounds["max_x"]) / 2
            center_y = (bounds["min_y"] + bounds["max_y"]) / 2
            center_z = (bounds["min_z"] + bounds["max_z"]) / 2

            size_x = bounds["max_x"] - bounds["min_x"] + 1
            size_y = bounds["max_y"] - bounds["min_y"] + 1
            size_z = bounds["max_z"] - bounds["min_z"] + 1
            max_size = max(size_x, size_y, size_z)

            distance = max_size * distance_factor
            angle_increment = 360.0 / n_frames

            for i in range(n_frames):
                angle = i * angle_increment
                angle_rad = math.radians(angle)
                cam_x = center_x + distance * math.cos(angle_rad)
                cam_y = center_y + distance * math.sin(math.radians(elevation))
                cam_z = center_z + distance * math.sin(angle_rad)

                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )
                if frame is None:
                    raise RuntimeError(f"帧 {i+1} 渲染失败")
                yield frame
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def iter_orbit_frames(self, n_frames: int = 36, start_elevation: float = 0.0,
                          end_elevation: float = 90.0, distance_factor: float = 2.0,
                          window_size: Optional[Tuple[int, int]] = None) -> Iterable[Image.Image]:
        """
        流式生成轨道动画帧
        """
        try:
            bounds = self.renderer.model_data["bounds"]
            center_x = (bounds["min_x"] + bounds["max_x"]) / 2
            center_y = (bounds["min_y"] + bounds["max_y"]) / 2
            center_z = (bounds["min_z"] + bounds["max_z"]) / 2

            size_x = bounds["max_x"] - bounds["min_x"] + 1
            size_y = bounds["max_y"] - bounds["min_y"] + 1
            size_z = bounds["max_z"] - bounds["min_z"] + 1
            max_size = max(size_x, size_y, size_z)

            distance = max_size * distance_factor
            angle_increment = 360.0 / n_frames
            elevation_increment = (end_elevation - start_elevation) / n_frames

            for i in range(n_frames):
                angle = i * angle_increment
                elevation = start_elevation + i * elevation_increment
                angle_rad = math.radians(angle)
                elevation_rad = math.radians(elevation)
                cam_x = center_x + distance * math.cos(angle_rad) * math.cos(elevation_rad)
                cam_y = center_y + distance * math.sin(elevation_rad)
                cam_z = center_z + distance * math.sin(angle_rad) * math.cos(elevation_rad)

                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )
                if frame is None:
                    raise RuntimeError(f"帧 {i+1} 渲染失败")
                yield frame
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def iter_zoom_frames(self, n_frames: int = 24, start_factor: float = 3.0,
                         end_factor: float = 1.5,
                         window_size: Optional[Tuple[int, int]] = None) -> Iterable[Image.Image]:
        """
        流式生成缩放动画帧
        """
        try:
            bounds = self.renderer.model_data["bounds"]
            center_x = (bounds["min_x"] + bounds["max_x"]) / 2
            center_y = (bounds["min_y"] + bounds["max_y"]) / 2
            center_z = (bounds["min_z"] + bounds["max_z"]) / 2

            size_x = bounds["max_x"] - bounds["min_x"] + 1
            size_y = bounds["max_y"] - bounds["min_y"] + 1
            size_z = bounds["max_z"] - bounds["min_z"] + 1
            max_size = max(size_x, size_y, size_z)

            factor_increment = (end_factor - start_factor) / n_frames
            angle_rad = math.radians(45)
            elevation_rad = math.radians(30)

            for i in range(n_frames):
                factor = start_factor + i * factor_increment
                distance = max_size * factor
                cam_x = center_x + distance * math.cos(angle_rad) * math.cos(elevation_rad)
                cam_y = center_y + distance * math.sin(elevation_rad)
                cam_z = center_z + distance * math.sin(angle_rad) * math.cos(elevation_rad)

                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )
                if frame is None:
                    raise RuntimeError(f"帧 {i+1} 渲染失败")
                yield frame
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def generate_rotation_frames(self, n_frames: int = 36, elevation: float = 30.0,
                               distance_factor: float = 2.0,
                               window_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        生成围绕模型旋转的帧序列

        Args:
            n_frames: 帧数，默认为36（每10度一帧）
            elevation: 相机仰角，默认为30度
            distance_factor: 相机距离因子，默认为2.0
            window_size: 输出分辨率(width, height)

        Returns:
            bool: 是否成功生成帧
        """
        try:
            # 清空现有帧
            self.frames.clear()

            # 获取模型边界
            bounds = self.renderer.model_data['bounds']
            center_x = (bounds['min_x'] + bounds['max_x']) / 2
            center_y = (bounds['min_y'] + bounds['max_y']) / 2
            center_z = (bounds['min_z'] + bounds['max_z']) / 2

            # 计算模型尺寸的最大值
            size_x = bounds['max_x'] - bounds['min_x'] + 1
            size_y = bounds['max_y'] - bounds['min_y'] + 1
            size_z = bounds['max_z'] - bounds['min_z'] + 1
            max_size = max(size_x, size_y, size_z)

            # 计算相机距离
            distance = max_size * distance_factor

            # 角度增量
            angle_increment = 360.0 / n_frames

            # 生成每一帧
            for i in range(n_frames):
                # 计算当前角度
                angle = i * angle_increment

                # 将角度转换为弧度
                angle_rad = math.radians(angle)

                # 计算相机位置（水平旋转）
                cam_x = center_x + distance * math.cos(angle_rad)
                cam_y = center_y + distance * math.sin(math.radians(elevation))
                cam_z = center_z + distance * math.sin(angle_rad)

                # 渲染场景
                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )

                if frame is None:
                    print(f"帧 {i+1} 渲染失败")
                    return False

                # 添加到帧列表
                self.frames.append(frame)

            return True

        except Exception as e:
            print(f"生成旋转帧时出错: {e}")
            return False
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def generate_orbit_frames(self, n_frames: int = 36, start_elevation: float = 0.0,
                           end_elevation: float = 90.0, distance_factor: float = 2.0,
                           window_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        生成轨道动画帧，相机从低到高环绕模型

        Args:
            n_frames: 帧数
            start_elevation: 起始仰角（度）
            end_elevation: 结束仰角（度）
            distance_factor: 相机距离因子
            window_size: 输出分辨率(width, height)

        Returns:
            bool: 是否成功生成帧
        """
        try:
            # 清空现有帧
            self.frames.clear()

            # 获取模型边界
            bounds = self.renderer.model_data['bounds']
            center_x = (bounds['min_x'] + bounds['max_x']) / 2
            center_y = (bounds['min_y'] + bounds['max_y']) / 2
            center_z = (bounds['min_z'] + bounds['max_z']) / 2

            # 计算模型尺寸的最大值
            size_x = bounds['max_x'] - bounds['min_x'] + 1
            size_y = bounds['max_y'] - bounds['min_y'] + 1
            size_z = bounds['max_z'] - bounds['min_z'] + 1
            max_size = max(size_x, size_y, size_z)

            # 计算相机距离
            distance = max_size * distance_factor

            # 角度增量
            angle_increment = 360.0 / n_frames
            elevation_increment = (end_elevation - start_elevation) / n_frames

            # 生成每一帧
            for i in range(n_frames):
                # 计算当前角度和仰角
                angle = i * angle_increment
                elevation = start_elevation + i * elevation_increment

                # 将角度转换为弧度
                angle_rad = math.radians(angle)
                elevation_rad = math.radians(elevation)

                # 计算相机位置
                cam_x = center_x + distance * math.cos(angle_rad) * math.cos(elevation_rad)
                cam_y = center_y + distance * math.sin(elevation_rad)
                cam_z = center_z + distance * math.sin(angle_rad) * math.cos(elevation_rad)

                # 渲染场景
                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )

                if frame is None:
                    print(f"帧 {i+1} 渲染失败")
                    return False

                # 添加到帧列表
                self.frames.append(frame)

            return True

        except Exception as e:
            print(f"生成轨道帧时出错: {e}")
            return False
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def generate_zoom_frames(self, n_frames: int = 24, start_factor: float = 3.0,
                          end_factor: float = 1.5,
                          window_size: Optional[Tuple[int, int]] = None) -> bool:
        """
        生成缩放动画帧，相机从远到近

        Args:
            n_frames: 帧数
            start_factor: 起始距离因子
            end_factor: 结束距离因子
            window_size: 输出分辨率(width, height)

        Returns:
            bool: 是否成功生成帧
        """
        try:
            # 清空现有帧
            self.frames.clear()

            # 获取模型边界
            bounds = self.renderer.model_data['bounds']
            center_x = (bounds['min_x'] + bounds['max_x']) / 2
            center_y = (bounds['min_y'] + bounds['max_y']) / 2
            center_z = (bounds['min_z'] + bounds['max_z']) / 2

            # 计算模型尺寸的最大值
            size_x = bounds['max_x'] - bounds['min_x'] + 1
            size_y = bounds['max_y'] - bounds['min_y'] + 1
            size_z = bounds['max_z'] - bounds['min_z'] + 1
            max_size = max(size_x, size_y, size_z)

            # 距离因子增量
            factor_increment = (end_factor - start_factor) / n_frames

            # 固定角度（等距视角）
            angle_rad = math.radians(45)
            elevation_rad = math.radians(30)

            # 生成每一帧
            for i in range(n_frames):
                # 计算当前距离因子
                factor = start_factor + i * factor_increment

                # 计算相机距离
                distance = max_size * factor

                # 计算相机位置
                cam_x = center_x + distance * math.cos(angle_rad) * math.cos(elevation_rad)
                cam_y = center_y + distance * math.sin(elevation_rad)
                cam_z = center_z + distance * math.sin(angle_rad) * math.cos(elevation_rad)

                # 渲染场景
                frame = self.renderer.render_scene(
                    camera_position=[(cam_x, cam_y, cam_z), (center_x, center_y, center_z), (0, 1, 0)],
                    window_size=window_size,
                    reuse_plotter=True
                )

                if frame is None:
                    print(f"帧 {i+1} 渲染失败")
                    return False

                # 添加到帧列表
                self.frames.append(frame)

            return True

        except Exception as e:
            print(f"生成缩放帧时出错: {e}")
            return False
        finally:
            if hasattr(self.renderer, "close"):
                self.renderer.close()

    def get_frames(self) -> List[Image.Image]:
        """
        获取生成的所有帧
        
        Returns:
            List[Image.Image]: 帧列表
        """
        return self.frames
    
    def clear_frames(self) -> None:
        """清空帧列表"""
        self.frames.clear() 
