"""
主入口: 按Phase顺序调用各generator, 实现30天循环
对应 plan.md 三、生成顺序与依赖 + 八、实施步骤
"""
import random
import time
from datetime import timedelta

import config


def main():
    start_all = time.time()
    random.seed(config.RANDOM_SEED)

    config.ensure_output_dir()
    out = config.OUTPUT_DIR
    print(f"输出目录: {out}")
    print(f"随机种子: {config.RANDOM_SEED}")
    print("=" * 60)

    # ── Phase 1: 基础维表 ──
    from generators.base_dimension import generate_all_dimensions
    dims = generate_all_dimensions(out)

    # ── Phase 2: 商品维表 ──
    from generators.product import generate_products
    products = generate_products(
        out, dims["cat3s"], dims["trademarks"], dims["merchants"],
        dims["cat1s"], dims["cat2s"])

    # ── Phase 3: 用户表 ──
    from generators.user import generate_users
    user_data = generate_users(
        out, dims["provinces"], dims["cities"], dims["districts"])

    # ── Phase 4: 活动优惠券 ──
    from generators.activity_coupon import generate_activity_coupon
    ac_data = generate_activity_coupon(
        out, products["skus"], user_data["users"])

    # ── Phase 5: 引擎初始化 ──
    from generators.order_engine import OrderEngine
    from generators.behavior_engine import BehaviorEngine
    from generators.daily_change import DailyChangeEngine
    from generators.stock_snapshot import StockSnapshotEngine
    from generators.shipment_engine import ShipmentEngine
    from generators.marketing_engine import MarketingEngine
    from utils.distribution import build_hot_sku_weights

    skus = products["skus"]
    users = user_data["users"]
    sku_ids = sorted(skus.keys())
    sku_weights = build_hot_sku_weights(
        sku_ids, config.HOT_SKU_COUNT, config.HOT_SKU_ORDER_SHARE)

    user_addresses = user_data.get("user_addresses", {})

    order_eng = OrderEngine(
        out, skus, users,
        ac_data["activities"], ac_data["coupons"],
        dims["merchants"], dims["cities"],
        ac_data["receives"], ac_data["rules_by_activity"],
        user_addresses, ac_data.get("activity_sku_map"))
    order_eng.open_writers()

    behavior_eng = BehaviorEngine(out, sku_ids, sku_weights, dims["devices"])
    behavior_eng.open_writers()

    change_eng = DailyChangeEngine(
        out, users, skus,
        order_stats_fn=lambda: order_eng.user_stats)
    change_eng.open_writers()

    stock_eng = StockSnapshotEngine(out, skus, dims["warehouses"])
    stock_eng.open_writer()

    ship_eng = ShipmentEngine(
        out, dims["carriers"], dims["warehouses"], dims["cities"], skus)
    ship_eng.open_writers()

    mkt_eng = MarketingEngine(
        out, ac_data["campaigns"], dims["channels"], users)
    mkt_eng.open_writers()

    # ── Phase 5: 30天每日循环 ──
    print("=" * 60)
    print("[Phase5] 开始30天事件驱动循环 ...")
    active_user_ids = [
        uid for uid, u in users.items() if u["status"] != "lost"
    ]

    traced_orders_map: dict = {}  # {uid: [order, ...]} 跨天 trace_id 全链路

    for day_num in range(1, config.SIM_DAYS + 1):
        day = config.SIM_START + timedelta(days=day_num - 1)
        day_start = time.time()

        # 周末/工作日 DAU 差异: 周末高20%, 周一低10%
        weekday = day.weekday()  # 0=周一 ... 6=周日
        if weekday >= 5:  # 周六日
            dau_factor = 1.20
        elif weekday == 0:  # 周一
            dau_factor = 0.90
        elif weekday == 4:  # 周五
            dau_factor = 1.05
        else:
            dau_factor = 1.0
        base_dau = random.randint(config.DAU_MIN, config.DAU_MAX)
        dau = int(base_dau * dau_factor)
        dau_users = random.sample(active_user_ids, k=min(dau, len(active_user_ids)))

        # 5a: SCD 变更注入
        change_eng.process_day(day, day_num)

        # 同步SCD变更后的用户等级到订单权重
        for uid in change_eng.changed_user_ids:
            lv = users[uid].get("user_level", 1)
            order_eng._user_order_weights[uid] = 2 ** (lv - 1)

        # 5f: 行为日志 (先于订单, 建立session映射)
        behavior_eng.process_day(day, dau_users, traced_orders_map)

        # 5b: 订单链生成 (使用行为session映射)
        order_eng.user_session_map = behavior_eng.user_session_map
        day_orders = order_eng.process_day(day, dau_users)

        # 更新 trace 映射供次日行为日志使用
        traced_orders_map.clear()
        for o in day_orders:
            if o.get("trace_id"):
                traced_orders_map.setdefault(o["user_id"], []).append(o)

        # 5c: 物流生成 — 使用 newly_shipped_today 覆盖所有发货(含跨天完成订单)
        newly_shipped = []
        for o in order_eng.newly_shipped_today:
            if not o.get("_shipped_processed"):
                ship_eng.process_shipped_order(o)
                o["_shipped_processed"] = True
                newly_shipped.append(o)
        # 签收日志 — 今日进入 received 状态的订单
        ship_eng.sign_orders(order_eng.newly_received_today)

        # 5d: 库存快照 (仅实际发货, 不含新建订单; 退款回补库存)
        stock_eng.process_day(day, [], newly_shipped,
                              order_eng.newly_refunded_today)

        # 5e: 营销触达 + 归因
        mkt_eng.process_day(day, dau_users, day_orders)

        elapsed = time.time() - day_start
        print(f"  Day {day_num:2d} ({day}) | "
              f"DAU={len(dau_users)} 新订单={len(day_orders)} "
              f"| {elapsed:.1f}s")

    # ── B3: 为最后一天traced订单补写行为事件 ──
    behavior_eng.flush_remaining_traces(traced_orders_map)

    # ── 关闭所有writer ──
    order_eng.close_writers()
    behavior_eng.close_writers()
    change_eng.close_writers()
    stock_eng.close_writer()
    ship_eng.close_writers()
    mkt_eng.close_writers()

    total_time = time.time() - start_all
    print("=" * 60)
    print(f"全部完成! 总耗时: {total_time:.1f}s")
    print(f"CSV 文件已输出到: {out}")


if __name__ == "__main__":
    main()
