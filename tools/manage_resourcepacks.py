#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from pathlib import Path
import re
from PIL import Image
import shutil
import glob

# 添加父目录到路径中，以便导入模块
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from core.image_render.config_loader import ConfigLoader

def get_resource_path():
    """获取资源路径"""
    return os.path.join(parent_dir, "resource")

def get_config_loader():
    """获取ConfigLoader单例实例"""
    return ConfigLoader()

def load_resourcepack_config():
    """加载资源包配置"""
    config_loader = get_config_loader()
    return config_loader.load_resourcepack_config()

def save_resourcepack_config(config):
    """保存资源包配置"""
    with open(get_resourcepack_path(), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_resourcepack_path():
    """获取资源包配置文件路径"""
    config_loader = get_config_loader()
    return config_loader.get_resourcepack_path()

def scan_resourcepacks():
    """扫描资源包目录，查找并添加新资源包"""
    config = load_resourcepack_config()
    current_resourcepacks = set(rp["path"] for rp in config["resourcepacks"])
    
    # 获取资源包目录
    base_dir = config.get("resource_base_path", "./resource")
    
    # 查找所有可能的资源包
    potential_paths = []
    
    # 查找子文件夹
    for dirpath, dirnames, filenames in os.walk(base_dir):
        # 查找包含assets/minecraft/textures/block的目录
        block_textures_path = os.path.join(dirpath, "assets", "minecraft", "textures", "block")
        if os.path.exists(block_textures_path):
            relative_path = os.path.relpath(dirpath, os.getcwd())
            relative_path = relative_path.replace("\\", "/")
            potential_paths.append(relative_path)
    
    # 添加新的资源包
    new_resourcepacks = []
    for path in potential_paths:
        if path not in current_resourcepacks:
            name = os.path.basename(path)
            # 尝试查找pack.mcmeta文件以获取更准确的名称
            mcmeta_path = os.path.join(path, "pack.mcmeta")
            if os.path.exists(mcmeta_path):
                try:
                    with open(mcmeta_path, 'r', encoding='utf-8') as f:
                        mcmeta = json.load(f)
                        if "pack" in mcmeta and "description" in mcmeta["pack"]:
                            name = mcmeta["pack"]["description"]
                            # 删除颜色代码
                            name = re.sub(r'§[0-9a-fk-or]', '', name)
                except Exception:
                    pass
            
            # 估计纹理大小
            texture_size = estimate_texture_size(path)
            
            new_resourcepack = {
                "name": name,
                "path": path,
                "texture_size": texture_size
            }
            
            new_resourcepacks.append(new_resourcepack)
            config["resourcepacks"].append(new_resourcepack)
    
    # 保存更新后的配置
    if new_resourcepacks:
        save_resourcepack_config(config)
    
    return new_resourcepacks

def estimate_texture_size(resourcepack_path):
    """估计资源包的材质大小"""
    # 查找方块材质目录
    block_textures_path = os.path.join(resourcepack_path, "assets", "minecraft", "textures", "block")
    if not os.path.exists(block_textures_path):
        return 16  # 默认值
    
    # 查找所有PNG文件
    texture_files = glob.glob(os.path.join(block_textures_path, "*.png"))
    
    # 如果找不到材质文件，返回默认值
    if not texture_files:
        return 16
    
    # 采样一些材质文件来估计大小
    sizes = []
    for texture_file in texture_files[:10]:  # 只检查前10个文件
        try:
            with Image.open(texture_file) as img:
                width, height = img.size
                sizes.append(width)
        except Exception:
            continue
    
    # 如果没有成功加载任何材质文件，返回默认值
    if not sizes:
        return 16
    
    # 返回最常见的尺寸
    return max(set(sizes), key=sizes.count)

def select_resourcepack_by_name(name):
    """根据名称选择资源包"""
    config = load_resourcepack_config()
    
    for rp in config["resourcepacks"]:
        if rp["name"].lower() == name.lower():
            config["selected_resourcepack"] = rp["path"]
            config["texture_size"] = rp["texture_size"]
            save_resourcepack_config(config)
            return True
    
    return False

def select_resourcepack_by_index(index):
    """根据索引选择资源包"""
    config = load_resourcepack_config()
    
    try:
        index = int(index)
        if 0 <= index < len(config["resourcepacks"]):
            rp = config["resourcepacks"][index]
            config["selected_resourcepack"] = rp["path"]
            config["texture_size"] = rp["texture_size"]
            save_resourcepack_config(config)
            return True
    except ValueError:
        pass
    
    return False

def list_resourcepacks():
    """列出所有可用的资源包"""
    config = load_resourcepack_config()
    
    active_path = config.get("selected_resourcepack", None)
    
    return config["resourcepacks"], active_path

def main():
    parser = argparse.ArgumentParser(description="管理Minecraft材质包")
    parser.add_argument("--scan", action="store_true", help="扫描并添加新的材质包")
    parser.add_argument("--list", action="store_true", help="列出所有可用的材质包")
    parser.add_argument("--select", help="根据名称选择材质包")
    parser.add_argument("--index", help="根据索引选择材质包")
    
    args = parser.parse_args()
    
    if args.scan:
        new_packs = scan_resourcepacks()
        if new_packs:
            print(f"发现{len(new_packs)}个新材质包:")
            for pack in new_packs:
                print(f"  - {pack['name']} ({pack['path']}, 纹理大小: {pack['texture_size']})")
        else:
            print("没有发现新的材质包")
        
    elif args.list:
        resourcepacks, active_path = list_resourcepacks()
        print("可用的材质包:")
        for i, rp in enumerate(resourcepacks):
            active = " [激活]" if rp["path"] == active_path else ""
            print(f"{i}. {rp['name']} ({rp['path']}, 纹理大小: {rp['texture_size']}){active}")
        
    elif args.select:
        if select_resourcepack_by_name(args.select):
            print(f"已选择材质包: {args.select}")
        else:
            print(f"找不到材质包: {args.select}")
        
    elif args.index is not None:
        if select_resourcepack_by_index(args.index):
            config = load_resourcepack_config()
            selected_index = int(args.index)
            selected_name = config["resourcepacks"][selected_index]["name"]
            print(f"已选择材质包: {selected_name}")
        else:
            print(f"无效的材质包索引: {args.index}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 