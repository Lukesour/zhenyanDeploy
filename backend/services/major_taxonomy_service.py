"""统一的专业方向分类服务"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


logger = logging.getLogger(__name__)


_DEFAULT_PATHS = [
    Path(__file__).resolve().parents[2]
    / "src"
    / "modules"
    / "study-planner"
    / "data"
    / "major_taxonomy.json",
    Path(__file__).resolve().parents[1] / "data" / "major_taxonomy.json",
]


def _resolve_taxonomy_path(explicit: Optional[Path | str]) -> Path:
    candidates: List[Path] = []

    if explicit:
        candidates.append(Path(explicit))

    env_path = os.getenv("MAJOR_TAXONOMY_PATH")
    if env_path:
        candidates.append(Path(env_path))

    candidates.extend(_DEFAULT_PATHS)

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    # If none exist, return final candidate for clearer error reporting
    return candidates[-1]


class MajorTaxonomyService:
    """加载并提供专业方向的统一映射与校验能力"""

    def __init__(self, taxonomy_path: Optional[Path | str] = None) -> None:
        self.taxonomy_path = _resolve_taxonomy_path(taxonomy_path)
        self._groups: List[Dict] = []
        self._directions: List[Dict] = []
        self._direction_map: Dict[str, Dict] = {}
        self._alias_map: Dict[str, str] = {}
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        if not self.taxonomy_path.exists():
            logger.error("专业方向词表不存在: %s", self.taxonomy_path)
            raise FileNotFoundError(f"major taxonomy file not found: {self.taxonomy_path}")

        with self.taxonomy_path.open(encoding="utf-8") as f:
            data = json.load(f)

        groups = data.get("groups", [])
        directions = data.get("directions", [])

        if not groups or not directions:
            raise ValueError("major taxonomy file is missing required sections")

        self._groups = groups
        self._directions = directions
        self._direction_map = {item["id"]: item for item in directions}
        self._alias_map = self._build_alias_map(directions)

        logger.info(
            "Loaded major taxonomy: %d groups, %d directions", len(groups), len(directions)
        )

    def _build_alias_map(self, directions: Iterable[Dict]) -> Dict[str, str]:
        alias_map: Dict[str, str] = {}

        for entry in directions:
            canonical = entry["id"]
            alias_candidates = set()
            alias_candidates.add(entry.get("id"))
            alias_candidates.add(entry.get("name"))

            for alias in entry.get("aliases", []) or []:
                alias_candidates.add(alias)

            # 允许以中文顿号、斜杠等分割的别名分拆匹配
            expanded: List[str] = []
            for alias in list(alias_candidates):
                if not alias:
                    continue
                expanded.append(alias.replace("/", " "))
                expanded.append(alias.replace("・", ""))
                expanded.append(alias.replace("和", "与"))
            alias_candidates.update(expanded)

            for alias in alias_candidates:
                if not alias:
                    continue
                key = self._normalise_key(alias)
                if not key:
                    continue

                # 避免不同方向对同一别名的冲突，保留首次定义并记录日志
                existing = alias_map.get(key)
                if existing and existing != canonical:
                    logger.debug(
                        "冲突的专业别名映射: '%s' -> '%s' (已有: '%s')",
                        alias,
                        canonical,
                        existing,
                    )
                    continue

                alias_map[key] = canonical

        return alias_map

    @staticmethod
    def _normalise_key(value: str) -> str:
        return "".join(value.strip().lower().split())

    @property
    def groups(self) -> List[Dict]:
        return self._groups

    @property
    def directions(self) -> List[Dict]:
        return self._directions

    def get_direction(self, direction_id: str) -> Optional[Dict]:
        if not direction_id:
            return None
        return self._direction_map.get(direction_id)

    def normalise_direction(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        key = self._normalise_key(value)
        return self._alias_map.get(key)

    def normalise_target_majors(
        self, target_majors: Optional[Iterable[str]]
    ) -> Tuple[List[str], List[str]]:
        canonical: List[str] = []
        invalid: List[str] = []

        for item in target_majors or []:
            if not item:
                continue
            normalised = self.normalise_direction(item)
            if normalised:
                if normalised not in canonical:
                    canonical.append(normalised)
            else:
                invalid.append(item)

        return canonical, invalid

    def refresh(self) -> None:
        """重新加载词表数据，用于热更新场景"""
        self._load_taxonomy()


@lru_cache(maxsize=1)
def get_major_taxonomy_service() -> MajorTaxonomyService:
    return MajorTaxonomyService()


# 导出单例，供直接导入使用
major_taxonomy_service = get_major_taxonomy_service()
