# 材质包使用说明

本功能允许用户选择不同的材质包来渲染立体结构图的2D投影视图。系统支持按优先级顺序搜索多个材质包，如果在当前材质包中找不到某个方块的材质，会自动在下一个材质包中查找。

## 材质包配置

材质包配置存储在 `resource/resourcepack.json` 文件中，结构如下：

```json
{
    "selected_pack": "XeKr 原版红显16_19plus",
    "available_packs": [
        "XeKr 原版红显16_19plus",
        "Faithful 64x"
    ],
    "texture_size": {
        "XeKr 原版红显16_19plus": 16,
        "Faithful 64x": 64
    },
    "description": {
        "XeKr 原版红显16_19plus": "XeKr的红石显示增强材质包，16x16分辨率",
        "Faithful 64x": "Faithful高清材质包，64x64分辨率"
    }
}
```

配置说明：
- `selected_pack`: 当前选择的材质包
- `available_packs`: 可用的材质包列表，**按优先级顺序排列**
- `texture_size`: 各材质包的材质尺寸（像素）
- `description`: 各材质包的描述信息

## 材质包目录结构

材质包存放在 `resource/block/` 目录下，每个材质包都是该目录下的一个子目录，例如：
```
resource/
  ├── block/
  │   ├── XeKr 原版红显16_19plus/
  │   │   ├── stone.png
  │   │   ├── dirt.png
  │   │   └── ...其他材质
  │   └── Faithful 64x/
  │       ├── stone.png
  │       ├── dirt.png
  │       └── ...其他材质
  └── resourcepack.json
```

## 材质包优先级

系统会按照 `available_packs` 中列出的顺序查找材质：
1. 首先在 `selected_pack` 指定的材质包中查找
2. 如果找不到，则按照 `available_packs` 列表的顺序，在其他材质包中查找
3. 如果所有材质包中都找不到，则使用默认材质（灰色方块）

## 使用材质包管理工具

提供了一个简单的材质包管理工具：`tools/manage_resourcepacks.py`，可以用来管理材质包。

### 查看可用材质包

```bash
python tools/manage_resourcepacks.py --list
```

### 选择材质包

按名称选择：
```bash
python tools/manage_resourcepacks.py --select "Faithful 64x"
```

按索引选择：
```bash
python tools/manage_resourcepacks.py --index 2
```

### 扫描并添加新材质包

```bash
python tools/manage_resourcepacks.py --scan
```

## 测试材质包回退功能

可以使用以下测试脚本测试材质包回退功能：
```bash
python test/test_resourcepack_fallback.py
```

该脚本会创建一个简单的世界模型，并尝试使用配置的材质包进行渲染，同时会统计每个材质包实际提供的材质数量。 