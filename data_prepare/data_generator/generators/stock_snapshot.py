"""
Phase5b: 库存快照 (sku_stock)
对应 plan.md 特征#18: 每日生成全量SKU库存截面
5000 SKU × 30天 = 150,000行
"""
import random
from datetime import datetime, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import fmt_date


class StockSnapshotEngine:
    """每日生成全量SKU库存截面"""

    def __init__(self, out_dir: str, skus: dict, warehouses: dict):
        self.out_dir = out_dir
        self.skus = skus
        self.warehouses = warehouses
        self.row_id = 0
        # 初始化库存 (每个SKU在每个仓库一个初始值)
        self.stock = {}
        wh_ids = list(warehouses.keys())
        for sid in skus:
            self.stock[sid] = {}
            for wid in wh_ids:
                self.stock[sid][wid] = random.randint(50, 2000)

    def open_writer(self):
        self.w = CsvWriter(self.out_dir, "sku_stock.csv", [
            "id", "sku_id", "warehouse_id", "stock_date",
            "stock_qty", "in_qty", "out_qty",
        ])

    def close_writer(self):
        self.w.close()

    def process_day(self, day: date, day_orders: list,
                    shipped_orders: list = None,
                    refunded_orders: list = None):
        """
        根据实际发货扣减库存, 退款回补库存, 随机补货, 写入全量截面
        day_orders: 当日新建订单 (仅供扩展用, 不用于扣库存)
        shipped_orders: 当日实际发货订单 (含当日即发 + 历史待发)
        refunded_orders: 当日退款订单 (退货回补库存)
        """
        # 只统计实际发货订单的出库量, 避免取消订单虚扣
        # 按实际出库仓库定向扣减 (key=(sku_id, warehouse_id))
        out_map_by_wh = {}  # {(sku_id, wh_id): qty}
        out_map = {}  # {sku_id: qty} 无仓库信息时的回退
        for o in (shipped_orders or []):
            wh_id = o.get("_warehouse_id")
            for det in o.get("details", []):
                sid = det["sku_id"]
                qty = det.get("qty", 1)
                if wh_id:
                    key = (sid, wh_id)
                    out_map_by_wh[key] = out_map_by_wh.get(key, 0) + qty
                else:
                    out_map[sid] = out_map.get(sid, 0) + qty

        # 统计退货回补量 (按实际仓库或均匀分配)
        refund_map_by_wh = {}  # {(sku_id, wh_id): qty}
        refund_map = {}  # {sku_id: qty}
        for o in (refunded_orders or []):
            wh_id = o.get("_warehouse_id")
            for det in o.get("details", []):
                sid = det["sku_id"]
                qty = det.get("qty", 1)
                if wh_id:
                    key = (sid, wh_id)
                    refund_map_by_wh[key] = refund_map_by_wh.get(key, 0) + qty
                else:
                    refund_map[sid] = refund_map.get(sid, 0) + qty

        day_str = fmt_date(datetime(day.year, day.month, day.day))
        wh_ids = list(self.warehouses.keys())

        for sid in self.skus:
            total_out = out_map.get(sid, 0)
            # 按仓库share分配无仓库信息的出库量，余数分配法避免截断丢失
            shares = [self.warehouses[wid]["share"] for wid in wh_ids]
            allocated = [int(total_out * s) for s in shares]
            remainder = total_out - sum(allocated)
            # 将余数分配给share最大的仓库
            if remainder > 0:
                max_idx = shares.index(max(shares))
                allocated[max_idx] += remainder

            for idx, wid in enumerate(wh_ids):
                # 优先使用实际仓库出库量, 无仓库信息时用按份额分配的量
                w_out_precise = out_map_by_wh.get((sid, wid), 0)
                w_out = w_out_precise + allocated[idx]
                # 退货回补量
                refund_precise = refund_map_by_wh.get((sid, wid), 0)
                old_stock = self.stock[sid][wid]
                safety_stock = 50
                if old_stock - w_out < safety_stock:
                    w_in = random.randint(200, 500)
                elif random.random() < 0.3:
                    w_in = random.randint(0, 50)
                else:
                    w_in = 0
                w_in += refund_precise  # 退货回补计入入库量
                new_stock = max(0, old_stock - w_out + w_in)
                self.stock[sid][wid] = new_stock
                self.row_id += 1
                self.w.write_row([
                    self.row_id, sid, wid, day_str,
                    new_stock, w_in, w_out,
                ])
