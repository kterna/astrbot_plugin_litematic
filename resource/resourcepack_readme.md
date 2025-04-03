# 材质包使用说明

本功能允许用户选择不同的材质包来渲染立体结构图的2D投影视图。系统支持按优先级顺序搜索多个材质包，如果在当前材质包中找不到某个方块的材质，会自动在下一个材质包中查找。

## 材质包配置

材质包配置存储在 `resource/resourcepack.json` 文件中，结构如下：

```json
{
    "selected_pack": "XeKr 原版红显",
    "available_packs": [
        "XeKr 原版红显16_19plus",
        "Faithful 64x"
    ],
    "texture_size": {
        "XeKr 原版红显": 16,
        "Faithful 64x": 64
    },
    "description": {
        "XeKr 原版红显": "XeKr的红石显示增强材质包，16x16分辨率",
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

材质包存放在 `resource/textures/block/` 目录下，每个材质包都是该目录下的一个子目录，例如：
```
resource/
  ├── textures/
  │     └──block        
  │         ├── XeKr 原版红显/
  │         │   ├── stone.png
  │         │   ├── dirt.png
  │         │   └── ...其他材质
  │         └── Faithful 64x/
  │               ├── stone.png
  │               ├── dirt.png
  │               └── ...其他材质
  └── resourcepack.json
```

## 材质包优先级

系统会按照 `available_packs` 中列出的顺序查找材质：
1. 首先在 `selected_pack` 指定的材质包中查找
2. 如果找不到，则按照 `available_packs` 列表的顺序，在其他材质包中查找
3. 如果所有材质包中都找不到，则使用默认材质（灰色方块）