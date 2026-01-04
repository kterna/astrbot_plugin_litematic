import os
import json
from typing import Dict, Any, Optional


class ModelResolver:
    """加载并解析方块模型文件，支持继承合并"""

    def __init__(self, resource_dir: str) -> None:
        self.models_dir = os.path.join(resource_dir, "models", "block")
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load(self, model_name: str) -> Optional[Dict[str, Any]]:
        """按模型名加载模型数据

        Args:
            model_name: 模型名称（不含.json后缀）
        """
        normalized = self._normalize_model_name(model_name)
        if normalized in self._cache:
            return self._cache[normalized]

        model_path = os.path.join(self.models_dir, f"{normalized}.json")
        if not os.path.exists(model_path):
            return None

        model_data = self._load_model_file(model_path)
        if not model_data:
            return None

        model_data = self._resolve_inheritance(model_data)
        self._cache[normalized] = model_data
        return model_data

    def _normalize_model_name(self, model_name: str) -> str:
        if model_name.startswith("minecraft:"):
            model_name = model_name[10:]
        if model_name.startswith("block/"):
            model_name = model_name[6:]
        return model_name

    def _load_model_file(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _resolve_inheritance(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        if "parent" not in model_data:
            return model_data

        parent_name = self._normalize_model_name(model_data["parent"])
        parent_path = os.path.join(self.models_dir, f"{parent_name}.json")
        if not os.path.exists(parent_path):
            return model_data

        parent_data = self._load_model_file(parent_path)
        if not parent_data:
            return model_data

        parent_data = self._resolve_inheritance(parent_data)
        return self._merge_model_data(parent_data, model_data)

    def _merge_model_data(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        merged = parent.copy()
        for key, value in child.items():
            if key == "textures" and "textures" in merged:
                merged["textures"].update(value)
            elif key == "elements" or key not in merged:
                merged[key] = value
        return merged
