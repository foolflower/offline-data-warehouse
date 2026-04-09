"""
热点分布/长尾分布/正态分布
对应 plan.md 特征#6 热点倾斜: Top50 SKU 30%订单, Top3城市40%订单
"""
import random
import bisect
import itertools
import numpy as np
from typing import List, Any


def weighted_sample(items: list, weights: list, k: int = 1) -> list:
    """按权重抽样 (不放回)"""
    if k >= len(items):
        return list(items)
    return random.choices(items, weights=weights, k=k)


def weighted_choice(items: list, weights: list):
    """按权重选择单个元素"""
    return random.choices(items, weights=weights, k=1)[0]


class PrecomputedWeightedChooser:
    """预计算累积权重，用 bisect 实现 O(log n) 的加权随机选择"""

    def __init__(self, items: list, weights: list):
        self.items = items
        self.cum_weights = list(itertools.accumulate(weights))

    def choose(self):
        x = random.random() * self.cum_weights[-1]
        idx = bisect.bisect_right(self.cum_weights, x)
        return self.items[min(idx, len(self.items) - 1)]

    def choose_many(self, k: int) -> list:
        total = self.cum_weights[-1]
        result = []
        for _ in range(k):
            x = random.random() * total
            idx = bisect.bisect_right(self.cum_weights, x)
            result.append(self.items[min(idx, len(self.items) - 1)])
        return result


def build_hot_sku_weights(sku_ids: list, hot_count: int, hot_share: float) -> list:
    """
    特征#6: 构建热销SKU权重
    hot_count个SKU占hot_share比例的订单
    """
    n = len(sku_ids)
    if hot_count >= n:
        return [1.0 / n] * n
    hot_weight_each = hot_share / hot_count
    normal_weight_each = (1.0 - hot_share) / (n - hot_count)
    weights = []
    for i in range(n):
        if i < hot_count:
            weights.append(hot_weight_each)
        else:
            weights.append(normal_weight_each)
    return weights


def build_hot_city_weights(city_ids: list, hot_count: int, hot_share: float) -> list:
    """
    特征#6: 构建热点城市权重
    hot_count个城市占hot_share比例的订单
    """
    return build_hot_sku_weights(city_ids, hot_count, hot_share)


def power_law_sample(n: int, alpha: float = 1.5) -> list:
    """幂律分布，用于长尾分布生成"""
    rng = np.random.default_rng()
    values = rng.pareto(alpha, size=n)
    return values.tolist()


def zipf_weights(n: int, s: float = 1.2) -> list:
    """Zipf分布权重，排名越前权重越高"""
    weights = [1.0 / (i ** s) for i in range(1, n + 1)]
    total = sum(weights)
    return [w / total for w in weights]


def normal_int(mean: float, std: float, min_val: int, max_val: int) -> int:
    """截断正态整数"""
    val = random.gauss(mean, std)
    return max(min_val, min(max_val, int(round(val))))


def choose_fate(fate_weights: dict) -> str:
    """选择订单命运路径"""
    fates = list(fate_weights.keys())
    weights = list(fate_weights.values())
    return random.choices(fates, weights=weights, k=1)[0]
