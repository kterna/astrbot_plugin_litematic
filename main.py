import os
import time
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
import tempfile

from astrbot import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Star, register, Context
from astrbot.api.message_components import File, Image as MessageImage
from astrbot.api.event import MessageChain

# 导入处理litematic的核心模块
from .core.material.material import Material
from .core.detail_analysis.detail_analysis import DetailAnalysis
from litemapy import Schematic

# 导入图像渲染相关模块
from .core.image_render.build_model import World
from .core.image_render.render2D import Render2D

@register("litematic", "kterna", "读取处理Litematic文件", "1.1.0", "https://github.com/kterna/astrbot_plugin_litematic")
class LitematicPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.litematic_dir = os.path.join(os.path.dirname(plugin_dir), "litematic")
        os.makedirs(self.litematic_dir, exist_ok=True)
        os.makedirs("temp", exist_ok=True)
        
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.categories_file = os.path.join(self.litematic_dir, "litematic_categories.json")
        self.litematic_categories = []
        os.makedirs(os.path.dirname(self.categories_file), exist_ok=True)
        
        self.load_categories()
        self.litematic_download = {}  # 文件上传状态跟踪
    
    def load_categories(self):
        """加载分类列表，如果不存在则创建默认分类"""
        try:
            if os.path.exists(self.categories_file) and os.path.getsize(self.categories_file) > 0:
                with open(self.categories_file, "r", encoding="utf-8") as f:
                    self.litematic_categories = json.loads(f.read())
            else:
                # 创建默认分类
                self.litematic_categories = ["建筑", "红石"]
                self.save_categories()
                logger.info(f"创建默认分类列表: {self.litematic_categories}")
        except Exception as e:
            logger.error(f"加载分类列表失败: {e}")
            self.litematic_categories = ["建筑", "红石"]
    
    def save_categories(self):
        """保存分类列表到JSON文件"""
        try:
            with open(self.categories_file, "w", encoding="utf-8") as f:
                json.dump(self.litematic_categories, f, ensure_ascii=False, indent=2)
            logger.info(f"保存分类列表: {self.litematic_categories}")
        except Exception as e:
            logger.error(f"保存分类列表失败: {e}")
    
    @filter.command("投影",alias=["litematic"])
    async def litematic(self, event: AstrMessageEvent, category: str = "default"):
        """
        上传litematic到指定分类文件夹下
        使用方法：
        /投影 - 查看帮助
        /投影 分类名 - 上传文件到指定分类
        """
        # 显示帮助信息
        if not category or category == "default":
            categories_text = "\n".join([f"- {cat}" for cat in self.litematic_categories])
            yield event.plain_result(
                f"Litematic文件管理器\n"
                f"请提供分类名称,例如: /litematic 建筑\n"
                f"当前可用分类：\n{categories_text}"
            )
            return
        
        # 处理新分类    
        if category not in self.litematic_categories:
            category_dir = os.path.join(self.litematic_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            self.litematic_categories.append(category)
            self.save_categories()
            yield event.plain_result(f"创建了新分类: {category}")

        # 记录用户上传状态
        user_key = f"{event.session_id}_{event.get_sender_id()}"
        self.litematic_download[user_key] = {
            "category": category,
            "expire_time": time.time() + 300
        }
        
        yield event.plain_result(f"请在5分钟内上传.litematic文件到{category}分类")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_upload_litematic(self, event: AstrMessageEvent):
        """处理上传的.litematic文件"""
        user_key = f"{event.session_id}_{event.get_sender_id()}"
        
        # 验证上传状态
        if user_key not in self.litematic_download:
            return
            
        # 检查是否超时
        if time.time() > self.litematic_download[user_key].get("expire_time", 0):
            del self.litematic_download[user_key]
            return
        
        # 处理文件上传
        for comp in event.message_obj.message:
            if isinstance(comp, File) and comp.name.endswith('.litematic'):
                file_path = comp.file
                category = self.litematic_download[user_key].get("category", "default")
                
                # 确保目录存在并保存文件
                category_dir = os.path.join(self.litematic_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                target_path = os.path.join(category_dir, os.path.basename(comp.name))
                
                try:
                    shutil.copy2(file_path, target_path)
                    logger.info(f"已保存litematic文件: {target_path}")
                    yield event.plain_result(f"已成功保存litematic文件到{category}分类: {comp.name}")
                except Exception as e:
                    logger.error(f"保存litematic文件失败: {e}")
                    yield event.plain_result(f"保存litematic文件失败: {e}")
                
                # 清理用户状态
                del self.litematic_download[user_key]
                return
                
        # 未找到文件时的提示
        yield event.plain_result("未检测到litematic文件，请直接发送.litematic格式的文件")
    
    @filter.command("投影列表",alias=["litematic_list"])
    async def litematic_list(self, event: AstrMessageEvent, category: str = ""):
        """
        列出litematic文件
        使用方法：
        /投影列表 - 列出所有分类
        /投影列表 分类名 - 列出指定分类下的文件
        """
        # 列出所有分类
        if not category:
            if not self.litematic_categories:
                yield event.plain_result("还没有任何分类，使用 /litematic 分类名 来创建分类")
                return
                
            categories_text = "\n".join([f"- {cat}" for cat in self.litematic_categories])
            yield event.plain_result(f"可用的分类列表：\n{categories_text}\n\n使用 /litematic_list 分类名 查看分类下的文件")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
        
        # 列出分类下的文件    
        category_dir = os.path.join(self.litematic_dir, category)
        if not os.path.exists(category_dir):
            yield event.plain_result(f"分类目录 {category} 不存在，这可能是一个错误")
            return
            
        files = [f for f in os.listdir(category_dir) if f.endswith('.litematic')]
        if not files:
            yield event.plain_result(f"分类 {category} 下还没有文件，使用 /litematic {category} 来上传文件")
            return
            
        files_text = "\n".join([f"- {file}" for file in files])
        yield event.plain_result(f"分类 {category} 下的文件：\n{files_text}")
        
    @filter.command("投影删除", alias=["litematic_delete"])
    async def litematic_delete(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        删除litematic文件或分类
        使用方法：
        /投影删除 分类名 - 删除指定分类及其下所有文件
        /投影删除 分类名 文件名 - 删除指定分类下的文件
        """
        # 验证参数
        if not category:
            yield event.plain_result("请指定要删除的分类名，例如：/litematic_delete 建筑")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
            
        category_dir = os.path.join(self.litematic_dir, category)
        
        # 删除整个分类
        if not filename:
            try:
                shutil.rmtree(category_dir)
                self.litematic_categories.remove(category)
                self.save_categories()
                yield event.plain_result(f"已删除分类 {category} 及其下所有文件")
            except Exception as e:
                logger.error(f"删除分类失败: {e}")
                yield event.plain_result(f"删除分类失败: {e}")
            return
        
        # 删除指定文件
        file_path = os.path.join(category_dir, filename)
        if not os.path.exists(file_path):
            # 尝试查找部分匹配的文件名
            matches = [f for f in os.listdir(category_dir) if filename.lower() in f.lower()]
            if not matches:
                yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
                return
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                matches_text = "\n".join([f"- {file}" for file in matches])
                yield event.plain_result(f"找到多个匹配的文件，请指定完整文件名：\n{matches_text}")
                return
                
        try:
            os.remove(file_path)
            yield event.plain_result(f"已删除文件: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            yield event.plain_result(f"删除文件失败: {e}")

    @filter.command("投影获取", alias=["litematic_get"])
    async def litematic_get(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        获取litematic文件
        使用方法：
        /投影获取 分类名 文件名 - 发送指定分类下的文件
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/litematic_get 建筑 house.litematic")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
            
        category_dir = os.path.join(self.litematic_dir, category)
        if not os.path.exists(category_dir):
            yield event.plain_result(f"分类目录 {category} 不存在，这可能是一个错误")
            return
        
        # 查找文件
        file_path = os.path.join(category_dir, filename)
        if not os.path.exists(file_path):
            # 尝试查找部分匹配的文件名
            matches = [f for f in os.listdir(category_dir) if filename.lower() in f.lower()]
            if not matches:
                yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
                return
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                matches_text = "\n".join([f"- {file}" for file in matches])
                yield event.plain_result(f"找到多个匹配的文件，请指定更精确的文件名：\n{matches_text}")
                return
                
        try:
            # 发送文件
            yield event.plain_result("正在发送文件，请稍候...")
            
            # 构建文件消息链并发送
            file_name = os.path.basename(file_path)
            file_component = File(name=file_name, file=file_path)
            
            message = MessageChain()
            message.chain.append(file_component)
            
            await event.send(message)
            
        except Exception as e:
            logger.error(f"发送文件失败: {e}")
            yield event.plain_result(f"发送文件失败: {e}")
    
    @filter.command("投影材料", alias=["litematic_material"])
    async def litematic_material(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        分析litematic文件所需材料
        使用方法：
        /投影材料 分类名 文件名 - 分析指定分类下文件所需的材料
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影材料 建筑 house.litematic")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
            
        category_dir = os.path.join(self.litematic_dir, category)
        if not os.path.exists(category_dir):
            yield event.plain_result(f"分类目录 {category} 不存在，这可能是一个错误")
            return
        
        # 查找文件
        file_path = os.path.join(category_dir, filename)
        if not os.path.exists(file_path):
            # 尝试查找部分匹配的文件名
            matches = [f for f in os.listdir(category_dir) if filename.lower() in f.lower()]
            if not matches:
                yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
                return
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                matches_text = "\n".join([f"- {file}" for file in matches])
                yield event.plain_result(f"找到多个匹配的文件，请指定更精确的文件名：\n{matches_text}")
                return
                
        try:
            # 加载litematic文件
            yield event.plain_result("正在分析材料清单，请稍候...")
            
            # 使用Material类分析文件
            schematic = Schematic.load(file_path)
            material_analyzer = Material("材料分析", 0)
            
            try:
                # 获取方块和实体统计
                block_counts = material_analyzer.block_collection(schematic)
                entity_counts = material_analyzer.entity_collection(schematic)
                tile_counts = material_analyzer.tile_collection(schematic)
                
                # 格式化结果
                result = f"【{os.path.basename(file_path)}】材料清单：\n\n"
                
                # 添加方块信息
                if block_counts:
                    result += "方块材料：\n"
                    sorted_blocks = sorted(block_counts.items(), key=lambda item: item[1], reverse=True)
                    for block_id, count in sorted_blocks:
                        result += f"- {block_id[10:]}: {count}个\n"
                else:
                    result += "无方块材料\n"
                
                # 添加实体信息
                if entity_counts:
                    result += "\n实体：\n"
                    sorted_entities = sorted(entity_counts.items(), key=lambda item: item[1], reverse=True)
                    for entity_id, count in sorted_entities:
                        result += f"- {entity_id}: {count}个\n"
                
                # 添加方块实体信息
                if tile_counts:
                    result += "\n方块实体：\n"
                    sorted_tiles = sorted(tile_counts.items(), key=lambda item: item[1], reverse=True)
                    for tile_id, count in sorted_tiles:
                        # 确保正确显示，处理不同类型的tile_id
                        if isinstance(tile_id, tuple) and len(tile_id) > 0:
                            result += f"- {tile_id[0]}: {count}个\n"
                        else:
                            result += f"- {tile_id}: {count}个\n"
                
                yield event.plain_result(result)
            except Exception as inner_e:
                logger.error(f"分析材料处理失败: {str(inner_e)}")
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
                yield event.plain_result(f"分析材料处理失败: {str(inner_e)}")
            
        except Exception as e:
            logger.error(f"分析材料失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"分析材料失败: {e}")
    
    @filter.command("投影信息", alias=["litematic_info"])
    async def litematic_info(self, event: AstrMessageEvent, category: str = "", filename: str = ""):
        """
        分析litematic文件详细信息
        使用方法：
        /投影信息 分类名 文件名 - 分析指定分类下文件的详细信息
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影信息 建筑 house.litematic")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
            
        category_dir = os.path.join(self.litematic_dir, category)
        if not os.path.exists(category_dir):
            yield event.plain_result(f"分类目录 {category} 不存在，这可能是一个错误")
            return
        
        # 查找文件
        file_path = os.path.join(category_dir, filename)
        if not os.path.exists(file_path):
            # 尝试查找部分匹配的文件名
            matches = [f for f in os.listdir(category_dir) if filename.lower() in f.lower()]
            if not matches:
                yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
                return
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                matches_text = "\n".join([f"- {file}" for file in matches])
                yield event.plain_result(f"找到多个匹配的文件，请指定更精确的文件名：\n{matches_text}")
                return
                
        try:
            # 加载litematic文件
            yield event.plain_result("正在分析投影信息，请稍候...")
            
            # 使用DetailAnalysis类分析文件
            schematic = Schematic.load(file_path)
            detail_analyzer = DetailAnalysis(schematic)
            
            try:
                # 直接使用detail_analyzer的方法分析
                details = detail_analyzer.analyze_schematic(file_path)
                
                # 格式化结果
                result = f"【{os.path.basename(file_path)}】详细信息：\n\n"
                result += "\n".join(details)
                
                yield event.plain_result(result)
            except Exception as e:
                logger.error(f"分析投影信息处理失败: {str(e)}")
                yield event.plain_result(f"分析投影信息失败，请稍后再试")
            
        except Exception as e:
            logger.error(f"分析投影信息失败: {e}")
            yield event.plain_result(f"分析投影信息失败: {e}")
            
    @filter.command("投影预览", alias=["litematic_preview"])
    async def litematic_preview(self, event: AstrMessageEvent, category: str = "", filename: str = "", view: str = "combined"):
        """
        预览litematic文件的2D渲染效果
        使用方法：
        /投影预览 分类名 文件名 - 生成并显示litematic的预览图
        /投影预览 分类名 文件名 视角 - 生成并显示指定视角的预览图
        支持的视角: top(俯视图), front(正视图), side(侧视图), combined(综合视图), 
                north(北面), south(南面), east(东面), west(西面)
        """
        # 验证参数
        if not category or not filename:
            yield event.plain_result("请指定分类和文件名，例如：/投影预览 建筑 house.litematic")
            return
        
        # 验证分类是否存在
        if category not in self.litematic_categories:
            yield event.plain_result(f"分类 {category} 不存在，可用的分类：{', '.join(self.litematic_categories)}")
            return
            
        category_dir = os.path.join(self.litematic_dir, category)
        if not os.path.exists(category_dir):
            yield event.plain_result(f"分类目录 {category} 不存在，这可能是一个错误")
            return
        
        # 查找文件
        file_path = os.path.join(category_dir, filename)
        if not os.path.exists(file_path):
            # 尝试查找部分匹配的文件名
            matches = [f for f in os.listdir(category_dir) if filename.lower() in f.lower()]
            if not matches:
                yield event.plain_result(f"在分类 {category} 下找不到文件 {filename}")
                return
            elif len(matches) == 1:
                file_path = os.path.join(category_dir, matches[0])
            else:
                matches_text = "\n".join([f"- {file}" for file in matches])
                yield event.plain_result(f"找到多个匹配的文件，请指定更精确的文件名：\n{matches_text}")
                return
                
        try:
            # 加载litematic文件
            yield event.plain_result("正在生成预览图，请稍候...")
            
            # 使用渲染引擎生成预览图
            schematic = Schematic.load(file_path)
            
            # 1. 构建世界模型
            world = World()
            world.add_blocks(schematic)
            
            # 2. 初始化2D渲染器
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            resource_base_path = os.path.join(plugin_dir, "resource")
            special_blocks_config = os.path.join(plugin_dir, "core", "image_render", "Special_blocks.json")
            
            renderer = Render2D(
                world=world,
                resource_base_path=resource_base_path,
                special_blocks_config=special_blocks_config
            )
            
            # 3. 根据视角选择渲染方法
            temp_img_path = None
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_img_path = tmp.name
                
                # 确定缩放比例，预防过大的图像
                scale = 1.0
                
                view = view.lower()
                if view == "top":
                    image = renderer.render_top_view(scale=scale)
                    caption = "俯视图 (从上向下看)"
                elif view == "front" or view == "north":
                    image = renderer.render_front_view(scale=scale)
                    caption = "正视图 (北面)"
                elif view == "side" or view == "east":
                    image = renderer.render_side_view(scale=scale)
                    caption = "侧视图 (东面)"
                elif view == "south":
                    # 南面是正视图的反面
                    min_x, max_x, min_y, max_y, min_z, max_z = renderer.engine._get_structure_bounds()
                    image = renderer.render_front_view(min_x, max_x, min_y, max_y, max_z, scale)
                    caption = "南面视图"
                elif view == "west":
                    # 西面是侧视图的反面
                    min_x, max_x, min_y, max_y, min_z, max_z = renderer.engine._get_structure_bounds()
                    image = renderer.render_side_view(min_z, max_z, min_y, max_y, min_x, scale)
                    caption = "西面视图"
                else:  # combined或其他情况
                    image = renderer.render_all_views(scale=scale)
                    caption = "综合视图 (俯视图 + 正视图 + 侧视图)"
                
                # 保存图像到临时文件
                image.save(temp_img_path, format='PNG')
            
            # 4. 发送图像
            file_name = os.path.basename(file_path)
            message = MessageChain()
            message.chain.append(MessageImage.fromFileSystem(temp_img_path))
            
            await event.send(message)
            yield event.plain_result(f"【{file_name}】{caption}")
            
            # 删除临时文件
            try:
                if temp_img_path and os.path.exists(temp_img_path):
                    os.unlink(temp_img_path)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"生成预览图失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            yield event.plain_result(f"生成预览图失败: {e}")