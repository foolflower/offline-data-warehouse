"""
Phase2: 商品维表生成器
对应 plan.md Phase 2: spu_info / sku_info / sku_attr_value / sku_sale_attr_value
"""
import random
from datetime import datetime, timedelta

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import fmt_datetime


# ========== 价格带定义 ==========
_PRICE_BANDS = [
    ("5-49", 5, 49),
    ("50-149", 50, 149),
    ("150-399", 150, 399),
    ("400-1500", 400, 1500),
]
_PRICE_BAND_W = [0.30, 0.35, 0.25, 0.10]


# ========== SPU/SKU 产品名称池（按一级品类） ==========
_SPU_NAME_MAP = {
    "手机数码": ["智能手机", "平板电脑", "蓝牙耳机", "智能手表", "充电宝", "数据线", "手机壳", "屏幕保护膜", "无线充电器", "自拍杆"],
    "电脑办公": ["笔记本电脑", "机械键盘", "无线鼠标", "显示器", "打印机", "U盘", "移动硬盘", "电脑包", "散热器", "摄像头"],
    "家用电器": ["空气净化器", "电饭煲", "微波炉", "吸尘器", "加湿器", "电热水壶", "电风扇", "烤箱", "破壁机", "豆浆机"],
    "服饰鞋包": ["连衣裙", "T恤", "牛仔裤", "运动鞋", "单肩包", "羽绒服", "polo衫", "雪地靴", "棒球帽", "丝巾"],
    "美妆护肤": ["面膜", "口红", "精华液", "防晒霜", "洗面奶", "粉底液", "眼霜", "卸妆水", "腮红", "眉笔"],
    "食品饮料": ["坚果礼盒", "牛肉干", "矿泉水", "即饮咖啡", "巧克力", "蜂蜜", "茶叶", "方便面", "果汁饮料", "酸奶"],
    "母婴用品": ["婴儿奶粉", "纸尿裤", "儿童积木", "婴儿推车", "儿童水壶", "婴儿湿巾", "儿童书包", "安抚玩具", "学步鞋", "婴儿餐椅"],
    "运动户外": ["跑步鞋", "瑜伽垫", "运动水壶", "登山包", "帐篷", "运动手环", "羽毛球拍", "游泳镜", "哑铃", "自行车"],
    "家居家装": ["四件套", "窗帘", "落地灯", "收纳箱", "浴巾", "地毯", "抱枕", "相框", "花瓶", "挂钟"],
    "图书音像": ["畅销小说", "编程教程", "儿童绘本", "历史读物", "管理书籍", "外语教材", "漫画", "字帖", "词典", "考试真题"],
    "医药保健": ["维生素C", "钙片", "鱼油", "益生菌", "护眼贴", "血压计", "体温计", "创可贴", "口罩", "酒精棉片"],
    "汽车用品": ["车载充电器", "行车记录仪", "座垫套", "车载香薰", "手机支架", "后备箱垫", "遮阳挡", "脚垫", "车衣", "方向盘套"],
    "珠宝饰品": ["黄金项链", "银手链", "珍珠耳环", "钻石戒指", "翡翠吊坠", "情侣对戒", "发卡", "胸针", "手镯", "脚链"],
    "玩具乐器": ["遥控车", "积木套装", "毛绒玩具", "拼图", "尤克里里", "电子琴", "口琴", "飞行棋", "水彩笔", "手工套装"],
    "宠物生活": ["猫粮", "狗粮", "猫砂", "宠物窝", "牵引绳", "猫爬架", "宠物玩具", "宠物零食", "宠物洗浴液", "宠物饮水机"],
}
_SKU_VARIANTS = [
    "标准版", "升级版", "豪华版", "经典款", "新款", "限量版",
    "大号", "中号", "小号", "黑色", "白色", "红色", "蓝色",
    "粉色", "绿色", "金色", "银色", "深灰色",
]


# ========== spu_info (1500) ==========
def gen_spu_info(out_dir: str, cat3s: dict, trademarks: dict, cat1s: dict, cat2s: dict):
    """生成SPU, 每个SPU关联一个cat3和trademark"""
    w = CsvWriter(out_dir, "spu_info.csv",
                  ["spu_id", "spu_name", "category3_id", "tm_id",
                   "create_time", "operate_time"])
    cat3_ids = list(cat3s.keys())
    tm_ids = list(trademarks.keys())
    now_str = fmt_datetime(datetime(2025, 10, 1, 10, 0, 0))
    spu_map = {}
    for spu_id in range(1, config.TOTAL_SPU + 1):
        c3 = random.choice(cat3_ids)
        tm = random.choice(tm_ids)
        # 根据一级品类选名
        c1_id = cat3s[c3][2]
        c1_name = cat1s.get(c1_id, "通用")
        pool = _SPU_NAME_MAP.get(c1_name, ["商品"])
        base_name = pool[(spu_id - 1) % len(pool)]
        tm_name = trademarks.get(tm, "品牌")
        spu_name = f"{tm_name} {base_name}"
        w.write_row([spu_id, spu_name, c3, tm, now_str, now_str])
        spu_map[spu_id] = {"cat3_id": c3, "tm_id": tm, "spu_name": spu_name}
    w.close()
    return spu_map


# ========== sku_info (5000) ==========
def gen_sku_info(out_dir: str, spu_map: dict, merchants: dict):
    """
    sku_info: 含增强字段 merchant_id / is_hot / price_band
    每个SPU下分配 ~3-4 个SKU, 总量=TOTAL_SKU
    """
    w = CsvWriter(out_dir, "sku_info.csv",
                  ["sku_id", "sku_name", "spu_id", "category3_id",
                   "tm_id", "original_price", "cost_price",
                   "weight", "volume", "merchant_id",
                   "is_hot", "price_band",
                   "create_time", "operate_time",
                   "dw_start_date", "dw_end_date"])
    spu_ids = list(spu_map.keys())
    merchant_ids = list(merchants.keys())
    now_str = fmt_datetime(datetime(2025, 10, 1, 10, 0, 0))

    # 将SKU分配给SPU
    sku_to_spu = []
    for sku_id in range(1, config.TOTAL_SKU + 1):
        spu_id = spu_ids[(sku_id - 1) % len(spu_ids)]
        sku_to_spu.append((sku_id, spu_id))

    # 热销SKU: 前 HOT_SKU_COUNT 个
    hot_set = set(range(1, config.HOT_SKU_COUNT + 1))

    skus = {}
    for sku_id, spu_id in sku_to_spu:
        spu = spu_map[spu_id]
        # 价格带
        band_info = random.choices(
            _PRICE_BANDS, weights=_PRICE_BAND_W, k=1)[0]
        band_label, lo, hi = band_info
        original_price = round(random.uniform(lo, hi), 2)
        cost_price = round(original_price * random.uniform(0.3, 0.7), 2)
        weight = round(random.uniform(0.1, 20.0), 2)
        volume = round(random.uniform(100, 50000), 0)
        mid = random.choice(merchant_ids)
        is_hot = 1 if sku_id in hot_set else 0

        sku_name = f"{spu.get('spu_name', 'SKU')} {random.choice(_SKU_VARIANTS)}"
        w.write_row([
            sku_id, sku_name, spu_id, spu["cat3_id"],
            spu["tm_id"], original_price, cost_price,
            weight, volume, mid,
            is_hot, band_label, now_str, now_str,
            "2025-10-01", "9999-12-31",
        ])
        skus[sku_id] = {
            "sku_id": sku_id, "spu_id": spu_id,
            "cat3_id": spu["cat3_id"], "tm_id": spu["tm_id"],
            "original_price": original_price,
            "cost_price": cost_price,
            "merchant_id": mid, "is_hot": is_hot,
            "weight": weight, "volume": volume,
            "sku_name": sku_name, "price_band": band_label,
            "create_time": now_str,
        }
    w.close()
    return skus


# ========== sku_attr_value (25000) ==========
_ATTR_NAMES = ["材质", "产地", "保质期", "包装", "适用人群"]
_ATTR_VALUES = {
    "材质": ["纯棉", "涤纶", "真丝", "合金", "塑料", "玻璃"],
    "产地": ["广东", "浙江", "江苏", "福建", "山东"],
    "保质期": ["12个月", "24个月", "36个月", "永久"],
    "包装": ["盒装", "袋装", "散装", "礼盒"],
    "适用人群": ["通用", "男士", "女士", "儿童", "老人"],
}


def gen_sku_attr_value(out_dir: str, skus: dict):
    """每个SKU 3~8 个属性值, Feature #9 多值关系"""
    w = CsvWriter(out_dir, "sku_attr_value.csv",
                  ["id", "sku_id", "attr_name", "attr_value"])
    attr_id = 1
    target = 25000
    sku_ids = list(skus.keys())
    idx = 0
    while attr_id <= target:
        sid = sku_ids[idx % len(sku_ids)]
        n = random.randint(3, 8)
        chosen_attrs = random.sample(
            _ATTR_NAMES, k=min(n, len(_ATTR_NAMES)))
        for aname in chosen_attrs:
            if attr_id > target:
                break
            aval = random.choice(_ATTR_VALUES[aname])
            w.write_row([attr_id, sid, aname, aval])
            attr_id += 1
        idx += 1
    w.close()


# ========== sku_sale_attr_value (15000) ==========
_SALE_ATTRS = {
    "颜色": ["黑色", "白色", "红色", "蓝色", "灰色", "粉色", "绿色"],
    "尺码": ["S", "M", "L", "XL", "XXL", "均码"],
    "规格": ["标准版", "升级版", "旗舰版", "迷你版"],
}
_SALE_ATTR_NAMES = list(_SALE_ATTRS.keys())


def gen_sku_sale_attr_value(out_dir: str, skus: dict):
    """每个SKU 2~4 个销售属性值"""
    w = CsvWriter(out_dir, "sku_sale_attr_value.csv",
                  ["id", "sku_id", "sale_attr_name", "sale_attr_value"])
    sa_id = 1
    target = 15000
    sku_ids = list(skus.keys())
    idx = 0
    while sa_id <= target:
        sid = sku_ids[idx % len(sku_ids)]
        n = random.randint(2, 4)
        chosen = random.sample(
            _SALE_ATTR_NAMES, k=min(n, len(_SALE_ATTR_NAMES)))
        for sa_name in chosen:
            if sa_id > target:
                break
            sa_val = random.choice(_SALE_ATTRS[sa_name])
            w.write_row([sa_id, sid, sa_name, sa_val])
            sa_id += 1
        idx += 1
    w.close()


# ========== 总入口 ==========
def generate_products(out_dir: str, cat3s: dict, trademarks: dict,
                      merchants: dict, cat1s: dict = None, cat2s: dict = None):
    """生成 Phase2 全部 4 张商品维表"""
    if cat1s is None:
        cat1s = {}
    if cat2s is None:
        cat2s = {}
    print("[Phase2] 生成 spu_info ...")
    spu_map = gen_spu_info(out_dir, cat3s, trademarks, cat1s, cat2s)

    print("[Phase2] 生成 sku_info ...")
    skus = gen_sku_info(out_dir, spu_map, merchants)

    print("[Phase2] 生成 sku_attr_value ...")
    gen_sku_attr_value(out_dir, skus)

    print("[Phase2] 生成 sku_sale_attr_value ...")
    gen_sku_sale_attr_value(out_dir, skus)

    print("[Phase2] 商品维表全部完成 (4张表)")
    return {"spu_map": spu_map, "skus": skus}
