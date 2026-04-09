"""
Phase5: 物流全链路生成器 (shipment_info + shipment_track + delivery_exception)
对应 plan.md 七、shipment 字段规格
"""
import random
from datetime import datetime, timedelta, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import fmt_datetime, add_hours, add_days
from utils.distribution import weighted_choice


# ── 运单号前缀 ──
_WAYBILL_PREFIX = {
    1: "SF", 2: "ZT", 3: "YT", 4: "YD", 5: "ST",
    6: "JT", 7: "EMS", 8: "JD", 9: "DB", 10: "BS",
}

_EXCEPTION_TYPES = ["丢失", "破损", "拒收", "地址错误"]
_EXCEPTION_W = [0.10, 0.30, 0.40, 0.20]

_TRANSIT_CITIES = [
    "北京", "上海", "广州", "深圳", "武汉", "成都", "重庆", "杭州",
    "南京", "郑州", "长沙", "西安", "合肥", "济南", "昆明", "福州",
    "沈阳", "哈尔滨", "大连", "青岛",
]


class ShipmentEngine:
    """物流全链路: shipment_info + track + exception"""

    def __init__(self, out_dir: str, carriers: dict,
                 warehouses: dict, cities: dict, skus: dict = None):
        self.out_dir = out_dir
        self.carriers = carriers
        self.warehouses = warehouses
        self.cities = cities
        self.skus = skus or {}
        self.shipment_id = 0
        self.track_id = 0
        self.exception_id = 0

        # carrier 权重
        self.carrier_ids = sorted(carriers.keys())
        self.carrier_weights = [
            carriers[c]["share"] for c in self.carrier_ids]

        # warehouse 权重
        self.wh_ids = sorted(warehouses.keys())
        self.wh_weights = [
            warehouses[w]["share"] for w in self.wh_ids]

        # 缓存 shipment_info 行, 签收时更新 signed_flag/signed_time
        self._pending_ships = {}  # {shipment_id: row_list}

    def open_writers(self):
        d = self.out_dir
        self.w_ship = CsvWriter(d, "shipment_info.csv", [
            "shipment_id", "order_id", "warehouse_id",
            "carrier_id", "logistics_type",
            "ship_time", "pickup_time",
            "estimated_arrival", "actual_arrival",
            "promised_delivery_time", "waybill_no",
            "signed_flag", "signed_time",
            "last_mile_type", "delivery_cost",
            "cod_flag", "re_dispatch_count",
        ])
        self.w_track = CsvWriter(d, "shipment_track.csv", [
            "track_id", "shipment_id", "node_seq",
            "node_name", "node_time", "city",
        ])
        self.w_exc = CsvWriter(d, "delivery_exception.csv", [
            "exception_id", "shipment_id", "order_id",
            "exception_type", "exception_time", "description",
        ])
        self.w_sign = CsvWriter(d, "shipment_sign_log.csv", [
            "sign_id", "shipment_id", "order_id", "signed_time",
        ])
        self.sign_id = 0

    def close_writers(self):
        # 将缓存的 shipment_info 行全部写出
        for row in self._pending_ships.values():
            self.w_ship.write_row(row)
        self._pending_ships.clear()
        self.w_ship.close()
        self.w_track.close()
        self.w_exc.close()
        self.w_sign.close()

    def process_shipped_order(self, order: dict):
        """为已发货订单生成物流信息"""
        send_time = order.get("send_time")
        if send_time is None:
            return
        self.shipment_id += 1
        sid = self.shipment_id
        oid = order["order_id"]

        # 承运商选择
        carrier_id = weighted_choice(self.carrier_ids, self.carrier_weights)
        carrier = self.carriers[carrier_id]

        # 仓库选择
        wh_id = weighted_choice(self.wh_ids, self.wh_weights)
        wh = self.warehouses[wh_id]

        # 物流类型
        user_pid = order.get("province_id", 1)
        wh_pid = wh["province_id"]
        if user_pid == wh_pid:
            ltype = "same_province"
        elif self._same_region(user_pid, wh_pid):
            ltype = "intra_region"
        else:
            ltype = "inter_province"

        # 时间节点
        pickup_time = add_hours(send_time, random.uniform(1, 4))
        base_days = config.PROMISED_DAYS[ltype]
        speed = carrier["speed_factor"]
        est_days = base_days / speed
        estimated = add_days(send_time, est_days)
        # 实际到达: ±偏移, 5%超时; 至少在发货1小时后
        offset = random.gauss(0, 0.5)
        actual = add_days(estimated, offset)
        actual = max(actual, add_hours(send_time, 1))
        if random.random() < 0.05:
            actual = add_days(estimated, random.uniform(1, 3))

        # 对齐: 若订单已有receive_time, 物流到达应略早于签收
        if order.get("receive_time"):
            actual = add_hours(order["receive_time"],
                               -random.uniform(0, 4))
            actual = max(actual, add_hours(send_time, 1))
        promised = add_days(send_time, base_days)

        # 签收: 初始标记为未签收，签收时由 sign_orders() 更新
        signed_flag = 0
        signed_time = None

        # 末端配送
        lm_types = list(config.LAST_MILE_WEIGHTS.keys())
        lm_w = list(config.LAST_MILE_WEIGHTS.values())
        last_mile = weighted_choice(lm_types, lm_w)

        # 运费
        weight = sum(
            self._get_sku_weight(d["sku_id"])
            for d in order.get("details", []))
        base_cost = {"same_province": 5, "intra_region": 8,
                     "inter_province": 12}
        cost = round(base_cost[ltype] + weight * 0.5, 2)

        # COD
        cod = 1 if order.get("pay_type") == 4 else 0

        # 重派次数
        rd_keys = list(config.RE_DISPATCH_WEIGHTS.keys())
        rd_w = list(config.RE_DISPATCH_WEIGHTS.values())
        re_dispatch = weighted_choice(rd_keys, rd_w)

        # 运单号
        prefix = _WAYBILL_PREFIX.get(carrier_id, "EX")
        waybill = f"{prefix}{random.randint(100000000000, 999999999999)}"

        ship_row = [
            sid, oid, wh_id, carrier_id, ltype,
            fmt_datetime(send_time), fmt_datetime(pickup_time),
            fmt_datetime(estimated), fmt_datetime(actual),
            fmt_datetime(promised), waybill,
            signed_flag, fmt_datetime(signed_time),
            last_mile, cost, cod, re_dispatch,
        ]
        self._pending_ships[sid] = ship_row
        # 记录物流单号供签收日志使用
        order["_shipment_id"] = sid
        # 记录实际出库仓库供库存扣减使用
        order["_warehouse_id"] = wh_id

        # 轨迹节点
        self._gen_track(sid, send_time, actual, wh, order, carrier_id)

        # 异常 (基于 carrier exception_rate)
        if random.random() < carrier["exception_rate"]:
            self._gen_exception(sid, oid, actual)

    def _same_region(self, pid1, pid2):
        """简单判断是否同区域 (每10个省一个区域)"""
        return (pid1 - 1) // 10 == (pid2 - 1) // 10

    def _get_sku_weight(self, sku_id):
        """查真实SKU重量, 无则随机"""
        sku = self.skus.get(sku_id)
        if sku and "weight" in sku:
            return sku["weight"]
        return random.uniform(0.1, 5.0)

    def _gen_track(self, shipment_id, ship_time, actual_arrival,
                   wh, order, carrier_id):
        """生成 5-8 个轨迹节点, Feature #8: 5%延迟上报"""
        nodes = config.TRACK_NODES  # 7个标准节点
        n_nodes = random.randint(5, min(8, len(nodes)))
        chosen = nodes[:n_nodes]
        total_hours = (actual_arrival - ship_time).total_seconds() / 3600
        interval = max(1, total_hours / n_nodes)

        wh_city = wh.get("name", "仓库城市")
        # 从订单关联的 city_id 查出真实收货城市名
        recv_city_id = order.get("city_id")
        # base_city 中 cities[cid] 结构为 (city_id, city_name, province_id)
        if recv_city_id and recv_city_id in self.cities:
            _, user_city_name, _ = self.cities[recv_city_id]
            user_city = user_city_name
        else:
            user_city = "收货城市"

        cur_time = ship_time
        for seq, node_name in enumerate(chosen, 1):
            delay = random.uniform(interval * 0.5, interval * 1.5)
            # Feature #8: 5% 延迟上报
            if random.random() < config.LATE_SHIPMENT_TRACK_RATE:
                delay += random.uniform(2, 24)
            cur_time = add_hours(cur_time, delay)
            # 城市: 首=仓库城市, 末=收货城市
            if seq == 1:
                city = wh_city
            elif seq == n_nodes:
                city = user_city
            else:
                city = random.choice(_TRANSIT_CITIES)
            self.track_id += 1
            self.w_track.write_row([
                self.track_id, shipment_id, seq,
                node_name, fmt_datetime(cur_time), city,
            ])

    def _gen_exception(self, shipment_id, order_id, exc_time):
        """生成物流异常记录"""
        self.exception_id += 1
        exc_type = weighted_choice(_EXCEPTION_TYPES, _EXCEPTION_W)
        self.w_exc.write_row([
            self.exception_id, shipment_id, order_id,
            exc_type, fmt_datetime(exc_time),
            f"{exc_type}异常描述",
        ])

    def sign_orders(self, received_orders: list):
        """为今日到达 received 状态的订单写签收日志, 并更新 shipment_info 缓存"""
        for o in received_orders:
            sid = o.get("_shipment_id")
            if sid and o.get("receive_time"):
                self.sign_id += 1
                self.w_sign.write_row([
                    self.sign_id, sid, o["order_id"],
                    fmt_datetime(o["receive_time"]),
                ])
                # 更新缓存行的 signed_flag(idx=11) 和 signed_time(idx=12)
                if sid in self._pending_ships:
                    self._pending_ships[sid][11] = 1
                    self._pending_ships[sid][12] = fmt_datetime(
                        o["receive_time"])
