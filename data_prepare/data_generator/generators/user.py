"""
Phase3: 用户表生成器
对应 plan.md Phase 3: user_info(100000) / user_address(180000)
Feature #4: 30%用户birthday=null
Feature #7: 手机号/身份证格式
Feature #15: 用户注册跨180天
"""
import random
from datetime import datetime, timedelta

import config
from utils.csv_writer import CsvWriter
from utils.fake_data import (
    random_chinese_name, random_phone, random_id_card, random_email,
)
from utils.time_utils import fmt_datetime, fmt_date


# ========== user_info (100,000) ==========
_GENDERS = [0, 1, 2]  # Feature #13: 0未知/1男/2女
_GENDER_W = [0.05, 0.48, 0.47]
_USER_LEVELS = [1, 2, 3, 4, 5]
_LEVEL_W = [0.30, 0.30, 0.20, 0.12, 0.08]
_USER_STATUSES = ["active", "silent", "lost"]
_STATUS_W = [0.60, 0.25, 0.15]

# 昵称池(组合生成)
_NICK_PREFIXES = [
    "快乐的", "爱笑的", "安静的", "奔跑的", "勇敢的", "追梦", "自由的", "温暖的",
    "幸运的", "慵懒的", "甜蜜的", "淡定的", "阳光", "清风", "星辰", "月亮",
    "小小的", "元气", "佛系", "可爱的", "神秘的", "活力", "酷酷的", "率真的",
    "深夜的", "暴走的", "沉默的", "微醺的", "迷路的", "漫步的", "闪闪的", "机智的",
    "随性的", "执着的", "悠闲的", "飒爽的", "孤独的", "傲娇的", "呆萌的", "高冷的",
]
_NICK_SUFFIXES = [
    "猫咪", "兔子", "熊猫", "小鹿", "企鹅", "考拉", "柴犬", "仓鼠",
    "向日葵", "薄荷", "柠檬", "草莓", "蓝莓", "少年", "旅人", "书虫",
    "吃货", "达人", "玩家", "路人", "学长", "同学", "骑士", "小仙女",
    "海鸥", "白鸽", "松鼠", "刺猬", "萤火虫", "蜻蜓", "锦鲤", "麋鹿",
    "探险家", "诗人", "画手", "歌者", "程序员", "设计师", "摄影师", "咖啡控",
]
_NICK_NUMBERS = ["", "", "", "", ""]  # 60% 无数字后缀
_NICK_NUMBERS += [str(i) for i in range(10, 100)]

# R3: 多风格昵称素材
_NICK_EN_WORDS = [
    "sky", "moon", "star", "rose", "dream", "cool", "happy", "love",
    "angel", "bright", "echo", "flow", "glow", "hope", "lucky", "nova",
    "pixel", "ruby", "sunny", "vibe", "zero", "ace", "blue", "candy",
]
_NICK_SPECIAL = [
    "—", "·", "_", "ovo", "qaq", "orz", "233", "666", "hhh",
]

# 真实街道名池
_STREET_POOL = [
    "中山路", "解放路", "人民路", "建设路", "和平路", "长安街", "南京路",
    "北京路", "长江路", "黄河路", "文化路", "学院路", "科技路", "创业路",
    "幸福路", "朝阳路", "光明路", "友谊路", "迎宾路", "站前路", "新华路",
    "东风路", "胜利路", "建国路", "民主路", "复兴路", "青年路", "育才路",
    "花园路", "金水路", "龙华路", "翠竹路", "滨河路", "环城路", "广场路",
]


def _random_register_time():
    """Feature #15: 注册时间 2025-10-01 ~ 2026-03-30, 180天跨度"""
    start = datetime(2025, 10, 1, 0, 0, 0)
    offset_sec = random.randint(0, 180 * 86400)
    return start + timedelta(seconds=offset_sec)


def _random_birthday():
    """Feature #4: 30%用户birthday=null"""
    if random.random() < config.NULL_BIRTHDAY_RATE:
        return ""
    year = random.randint(1960, 2005)
    month = random.randint(1, 12)
    if month == 2:
        max_day = 28
    elif month in (4, 6, 9, 11):
        max_day = 30
    else:
        max_day = 31
    day = random.randint(1, max_day)
    return f"{year}-{month:02d}-{day:02d}"


def gen_user_info(out_dir: str, provinces: dict, cities: dict):
    w = CsvWriter(out_dir, "user_info.csv",
                  ["user_id", "login_name", "nick_name", "name",
                   "phone_num", "id_card", "email", "gender",
                   "birthday", "user_level", "status",
                   "province_id", "city_id",
                   "create_time", "operate_time",
                   "dw_start_date", "dw_end_date"])
    province_ids = list(provinces.keys())
    city_ids = list(cities.keys())
    users = {}
    for uid in range(1, config.TOTAL_USERS + 1):
        name = random_chinese_name()
        phone = random_phone()
        id_card = random_id_card()
        login_name = f"user{uid:06d}"
        email = random_email(login_name)
        gender = random.choices(_GENDERS, weights=_GENDER_W, k=1)[0]
        bday = _random_birthday()
        level = random.choices(_USER_LEVELS, weights=_LEVEL_W, k=1)[0]
        status = random.choices(
            _USER_STATUSES, weights=_STATUS_W, k=1)[0]
        pid = random.choice(province_ids)
        province_cities = [c for c in city_ids if cities[c][2] == pid]
        cid = random.choice(province_cities) if province_cities else random.choice(city_ids)
        reg_time = _random_register_time()
        reg_str = fmt_datetime(reg_time)
        # R3: 多风格昵称生成
        nick_style = random.random()
        if nick_style < 0.55:
            # 55% 中文前缀+后缀+可选数字
            nick = f"{random.choice(_NICK_PREFIXES)}{random.choice(_NICK_SUFFIXES)}{random.choice(_NICK_NUMBERS)}"
        elif nick_style < 0.70:
            # 15% 纯数字昵称
            nick = str(random.randint(10000000, 9999999999))
        elif nick_style < 0.85:
            # 15% 英文混合
            w1 = random.choice(_NICK_EN_WORDS)
            w2 = random.choice(_NICK_EN_WORDS)
            sep = random.choice(["_", "", str(random.randint(0, 99))])
            nick = f"{w1}{sep}{w2}"
        else:
            # 15% 特殊字符/表情风格
            nick = f"{random.choice(_NICK_PREFIXES)}{random.choice(_NICK_SPECIAL)}{random.choice(_NICK_SUFFIXES)}"
        w.write_row([
            uid, login_name, nick, name,
            phone, id_card, email, gender,
            bday, level, status, pid, cid,
            reg_str, reg_str,
            fmt_date(reg_time), "9999-12-31",
        ])
        users[uid] = {
            "user_id": uid, "user_level": level,
            "status": status, "province_id": pid,
            "city_id": cid, "register_time": reg_time,
            "nick_name": nick, "name": name,
            "phone_num": phone, "id_card": id_card,
            "email": email, "gender": gender,
            "birthday": bday, "create_time": reg_str,
        }
    w.close()
    return users


# ========== user_address (180,000) ==========
def gen_user_address(out_dir: str, users: dict,
                     provinces: dict, cities: dict, districts: dict):
    """Feature #9: 每用户1~5个地址, 多值关系"""
    w = CsvWriter(out_dir, "user_address.csv",
                  ["address_id", "user_id", "province_id", "city_id",
                   "district_id", "detail_address", "consignee",
                   "consignee_phone", "is_default",
                   "create_time", "operate_time"])
    addr_id = 1
    target = 180000
    user_ids = list(users.keys())
    idx = 0
    district_ids = list(districts.keys())
    # 按用户分组的地址列表, 供订单引擎使用
    user_addresses = {}  # {user_id: [{province_id, city_id, district_id}, ...]}
    # 构建 city_id -> 所属 district_ids 映射
    city_to_districts = {}
    for did, d_info in districts.items():
        city_to_districts.setdefault(d_info[2], []).append(did)
    # 构建 province_id -> city_ids 映射
    province_to_cities = {}
    for cid_key, c_info in cities.items():
        province_to_cities.setdefault(c_info[2], []).append(cid_key)

    while addr_id <= target:
        uid = user_ids[idx % len(user_ids)]
        n_addr = random.randint(1, 5)
        u_pid = users[uid].get("province_id")
        u_cid = users[uid].get("city_id")
        for j in range(n_addr):
            if addr_id > target:
                break
            if j == 0 and u_cid and u_cid in city_to_districts:
                # 默认地址关联注册城市
                did = random.choice(city_to_districts[u_cid])
            else:
                did = random.choice(district_ids)
            d_info = districts[did]
            cid = d_info[2]
            pid = d_info[3]
            street = random.choice(_STREET_POOL)
            detail = f"{street}{random.randint(1,200)}号{random.randint(1,30)}栋{random.randint(1,6)}单元{random.randint(101,2505)}室"
            consignee = random_chinese_name()
            phone = random_phone()
            is_def = 1 if j == 0 else 0
            reg_str = fmt_datetime(
                users[uid]["register_time"] + timedelta(
                    seconds=random.randint(0, 3600)))
            w.write_row([
                addr_id, uid, pid, cid, did,
                detail, consignee, phone, is_def,
                reg_str, reg_str,
            ])
            user_addresses.setdefault(uid, []).append(
                {"province_id": pid, "city_id": cid, "is_default": is_def})
            addr_id += 1
        idx += 1
    w.close()
    return user_addresses


# ========== 总入口 ==========
def generate_users(out_dir: str, provinces: dict, cities: dict,
                   districts: dict):
    """生成 Phase3 全部 2 张用户表"""
    print("[Phase3] 生成 user_info ...")
    users = gen_user_info(out_dir, provinces, cities)

    print("[Phase3] 生成 user_address ...")
    user_addresses = gen_user_address(
        out_dir, users, provinces, cities, districts)

    print("[Phase3] 用户表全部完成 (2张表)")
    return {"users": users, "user_addresses": user_addresses}
