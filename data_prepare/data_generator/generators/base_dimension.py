"""
Phase1: 基础维表生成器
对应 plan.md 二、Phase 1: 基础维表 (< 5MB)
生成: region/province/city/district/category/trademark/supplier/warehouse/channel/dim_date/dim_device/dim_carrier/merchant_info
"""
import random
from datetime import date, datetime, timedelta

import config
from utils.csv_writer import CsvWriter
from utils.fake_data import random_phone, random_bank_account, random_chinese_name
from utils.time_utils import fmt_datetime, fmt_date


# ========== base_region ==========
REGIONS = [
    (1, "华北"), (2, "华东"), (3, "华南"),
    (4, "华中"), (5, "西南"), (6, "西北"), (7, "东北"),
]


def gen_base_region(out_dir: str):
    w = CsvWriter(out_dir, "base_region.csv",
                  ["region_id", "region_name"])
    for rid, rname in REGIONS:
        w.write_row([rid, rname])
    w.close()
    return {r[0]: r[1] for r in REGIONS}


# ========== base_province ==========
PROVINCES = [
    (1, "北京", 1, "010", "CN-BJ"), (2, "天津", 1, "022", "CN-TJ"),
    (3, "河北", 1, "0311", "CN-HE"), (4, "山西", 1, "0351", "CN-SX"),
    (5, "内蒙古", 1, "0471", "CN-NM"),
    (6, "上海", 2, "021", "CN-SH"), (7, "江苏", 2, "025", "CN-JS"),
    (8, "浙江", 2, "0571", "CN-ZJ"), (9, "安徽", 2, "0551", "CN-AH"),
    (10, "福建", 2, "0591", "CN-FJ"), (11, "江西", 2, "0791", "CN-JX"),
    (12, "山东", 2, "0531", "CN-SD"),
    (13, "广东", 3, "020", "CN-GD"), (14, "广西", 3, "0771", "CN-GX"),
    (15, "海南", 3, "0898", "CN-HI"),
    (16, "河南", 4, "0371", "CN-HA"), (17, "湖北", 4, "027", "CN-HB"),
    (18, "湖南", 4, "0731", "CN-HN"),
    (19, "四川", 5, "028", "CN-SC"), (20, "贵州", 5, "0851", "CN-GZ"),
    (21, "云南", 5, "0871", "CN-YN"), (22, "重庆", 5, "023", "CN-CQ"),
    (23, "西藏", 5, "0891", "CN-XZ"),
    (24, "陕西", 6, "029", "CN-SN"), (25, "甘肃", 6, "0931", "CN-GS"),
    (26, "青海", 6, "0971", "CN-QH"), (27, "宁夏", 6, "0951", "CN-NX"),
    (28, "新疆", 6, "0991", "CN-XJ"),
    (29, "辽宁", 7, "024", "CN-LN"), (30, "吉林", 7, "0431", "CN-JL"),
    (31, "黑龙江", 7, "0451", "CN-HL"),
    (32, "台湾", 2, "886", "CN-TW"), (33, "香港", 3, "852", "CN-HK"),
    (34, "澳门", 3, "853", "CN-MO"),
]


def gen_base_province(out_dir: str):
    w = CsvWriter(out_dir, "base_province.csv",
                  ["province_id", "province_name", "region_id",
                   "area_code", "iso_code"])
    for pid, pname, rid, acode, iso in PROVINCES:
        w.write_row([pid, pname, rid, acode, iso])
    w.close()
    return {p[0]: p for p in PROVINCES}


# ========== base_city (340行) — 真实城市数据 ==========
# (province_id, city_name) 按省映射
_REAL_CITIES = {
    1: ["东城区", "西城区", "朝阳区", "海淀区", "丰台区", "石景山区", "通州区", "顺义区", "大兴区", "昌平区"],
    2: ["和平区", "河东区", "河西区", "南开区", "河北区", "红桥区", "滨海新区", "东丽区", "西青区", "津南区"],
    3: ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市"],
    4: ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市"],
    5: ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市", "兴安盟"],
    6: ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区", "浦东新区", "闵行区", "宝山区"],
    7: ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市"],
    8: ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市"],
    9: ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市"],
    10: ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市", "平潭县"],
    11: ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市"],
    12: ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市"],
    13: ["广州市", "深圳市", "珠海市", "汕头市", "佛山市", "韶关市", "湛江市", "肇庆市", "江门市", "惠州市"],
    14: ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市"],
    15: ["海口市", "三亚市", "三沙市", "儋州市", "琼海市", "万宁市", "文昌市", "东方市", "澄迈县", "临高县"],
    16: ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市"],
    17: ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市"],
    18: ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市"],
    19: ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市"],
    20: ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市", "黔西南州", "黔东南州", "黔南州", "仁怀市"],
    21: ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市", "楚雄州", "大理州"],
    22: ["渝中区", "万州区", "涪陵区", "江北区", "沙坪坝区", "九龙坡区", "南岸区", "北碚区", "渝北区", "巴南区"],
    23: ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市", "阿里地区", "尼木县", "堆龙德庆区", "达孜区"],
    24: ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
    25: ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市"],
    26: ["西宁市", "海东市", "海北州", "黄南州", "海南州", "果洛州", "玉树州", "海西州", "格尔木市", "德令哈市"],
    27: ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市", "永宁县", "贺兰县", "灵武市", "同心县", "海原县"],
    28: ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市", "昌吉州", "伊犁州", "塔城地区", "阿勒泰地区", "喀什地区", "和田地区"],
    29: ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市"],
    30: ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市", "延边州", "梅河口市"],
    31: ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市"],
    32: ["台北市", "新北市", "桃园市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉义市", "屏东县"],
    33: ["中西区", "湾仔区", "东区", "南区", "油尖旺区", "深水埗区", "九龙城区", "黄大仙区", "观塘区", "沙田区"],
    34: ["花地玛堂区", "花王堂区", "望德堂区", "大堂区", "风顺堂区", "嘉模堂区", "路氹填海区", "路环区", "圣安多尼堂区", "氹仔区"],
}


def gen_base_city(out_dir: str, provinces: dict):
    w = CsvWriter(out_dir, "base_city.csv",
                  ["city_id", "city_name", "province_id"])
    city_id = 1
    cities = {}
    for pid in sorted(provinces.keys()):
        city_names = _REAL_CITIES.get(pid, [f"城市{i}" for i in range(1, 11)])
        for cname in city_names:
            w.write_row([city_id, cname, pid])
            cities[city_id] = (city_id, cname, pid)
            city_id += 1
    w.close()
    return cities


# ========== base_district (3000行) — 真实区县名池 ==========
_DISTRICT_POOL = [
    "朝阳区", "海淀区", "西城区", "东城区", "丰台区", "通州区", "大兴区", "昌平区",
    "顺义区", "房山区", "石景山区", "门头沟区", "怀柔区", "延庆区", "密云区", "平谷区",
    "新华区", "长安区", "桥西区", "裕华区", "矿区", "鼓楼区", "相城区", "吴中区",
    "金阊区", "虎丘区", "吴江区", "昆山区", "太仓区", "常熟区", "张家港区", "姑苏区",
    "锡山区", "惠山区", "滨湖区", "新吴区", "梁溪区", "武进区", "天宁区", "钟楼区",
    "新北区", "金坛区", "溧阳区", "经济开发区", "高新区", "工业园区", "保税区",
    "南关区", "宽城区", "绿园区", "二道区", "双阳区", "九台区", "龙潭区", "船营区",
    "昌邑区", "丰满区", "铁西区", "铁东区", "立山区", "千山区", "顺城区", "望花区",
    "东洲区", "新抚区", "平山区", "明山区", "溪湖区", "南芬区", "振兴区", "元宝区",
    "振安区", "古塔区", "凌河区", "太和区", "站前区", "西市区", "鲅鱼圈区", "老边区",
    "海州区", "细河区", "太子河区", "白塔区", "宏伟区", "弓长岭区", "文圣区",
    "城关区", "七里河区", "西固区", "安宁区", "红古区", "永登县", "皋兰县", "榆中县",
    "雁塔区", "碑林区", "莲湖区", "新城区", "未央区", "灞桥区", "长安区", "临潼区",
    "阎良区", "高陵区", "鄠邑区", "蓝田县", "周至县", "渭城区", "秦都区", "兴平区",
    "武昌区", "洪山区", "青山区", "汉阳区", "汉口区", "硚口区", "江汉区", "江岸区",
    "蔡甸区", "东西湖区", "黄陂区", "新洲区", "江夏区", "岳麓区", "芙蓉区", "天心区",
    "开福区", "雨花区", "望城区", "长沙县", "浏阳市", "宁乡市", "天河区", "越秀区",
    "荔湾区", "白云区", "番禺区", "花都区", "南沙区", "增城区", "从化区", "黄埔区",
    "福田区", "罗湖区", "南山区", "宝安区", "龙岗区", "盐田区", "龙华区", "坪山区",
    "光明区", "香洲区", "斗门区", "金湾区", "武侯区", "锦江区", "青羊区", "金牛区",
    "成华区", "温江区", "郫都区", "新都区", "龙泉驿区", "青白江区", "双流区", "都江堰市",
    "南明区", "云岩区", "花溪区", "乌当区", "白云区", "观山湖区", "清镇市", "修文县",
    "官渡区", "五华区", "盘龙区", "西山区", "呈贡区", "晋宁区", "安宁市", "富民县",
    "上城区", "下城区", "江干区", "拱墅区", "西湖区", "滨江区", "萧山区", "余杭区",
    "富阳区", "临安区", "桐庐县", "淳安县", "建德市", "鼓楼区", "台江区", "仓山区",
    "马尾区", "晋安区", "长乐区", "福清市", "连江县", "东湖区", "西湖区", "青云谱区",
    "青山湖区", "新建区", "红谷滩区", "湾里管理局", "历下区", "市中区", "槐荫区",
    "天桥区", "历城区", "长清区", "章丘区", "济阳区", "市南区", "市北区", "李沧区",
    "崂山区", "城阳区", "黄岛区", "即墨区", "胶州市",
]


def gen_base_district(out_dir: str, cities: dict):
    w = CsvWriter(out_dir, "base_district.csv",
                  ["district_id", "district_name", "city_id", "province_id"])
    district_id = 1
    districts = {}
    city_ids = sorted(cities.keys())
    remaining = 3000
    pool_len = len(_DISTRICT_POOL)
    for idx, cid in enumerate(city_ids):
        pid = cities[cid][2]
        if idx == len(city_ids) - 1:
            n = remaining
        else:
            n = random.randint(7, 11)
            remaining -= n
            if remaining <= 0:
                n = max(1, n + remaining)
                remaining = 0
        for i in range(n):
            dname = _DISTRICT_POOL[(district_id + i * 7) % pool_len]
            w.write_row([district_id, dname, cid, pid])
            districts[district_id] = (district_id, dname, cid, pid)
            district_id += 1
    w.close()
    return districts


# ========== base_category1/2/3 (15/60/300) ==========
_CAT1_NAMES = [
    "手机数码", "电脑办公", "家用电器", "服饰鞋包", "美妆护肤",
    "食品饮料", "母婴用品", "运动户外", "家居家装", "图书音像",
    "医药保健", "汽车用品", "珠宝饰品", "玩具乐器", "宠物生活",
]

_CAT2_NAMES = {
    "手机数码": ["智能手机", "平板电脑", "手机配件", "智能穿戴"],
    "电脑办公": ["笔记本电脑", "台式机", "办公设备", "电脑配件"],
    "家用电器": ["大家电", "厨房电器", "生活电器", "个护健康"],
    "服饰鞋包": ["女装", "男装", "鞋靴", "箱包"],
    "美妆护肤": ["面部护肤", "彩妆", "香水", "美妆工具"],
    "食品饮料": ["休闲零食", "粮油调味", "饮料冲调", "生鲜水果"],
    "母婴用品": ["奶粉辅食", "纸尿裤", "童装童鞋", "妈妈用品"],
    "运动户外": ["运动鞋服", "健身器材", "户外装备", "骑行运动"],
    "家居家装": ["家纺布艺", "灯具照明", "家装建材", "收纳整理"],
    "图书音像": ["文学小说", "教育考试", "少儿读物", "人文社科"],
    "医药保健": ["营养保健", "家庭常备", "医疗器械", "隐形眼镜"],
    "汽车用品": ["车载电子", "汽车装饰", "汽车养护", "安全自驾"],
    "珠宝饰品": ["黄金饰品", "钻石饰品", "银饰", "时尚饰品"],
    "玩具乐器": ["遥控电动", "益智玩具", "乐器", "模型手办"],
    "宠物生活": ["猫粮猫砂", "狗粮狗用", "宠物玩具", "宠物医疗"],
}

_CAT3_NAMES = {
    "智能手机": ["5G手机", "折叠屏手机", "游戏手机", "商务手机", "老人手机"],
    "平板电脑": ["安卓平板", "学习平板", "绘画平板", "轻薄平板", "游戏平板"],
    "手机配件": ["手机壳", "钢化膜", "充电器", "数据线", "手机支架"],
    "智能穿戴": ["智能手表", "智能手环", "蓝牙耳机", "TWS耳机", "VR眼镜"],
    "笔记本电脑": ["轻薄本", "游戏本", "商务本", "二合一本", "设计本"],
    "台式机": ["品牌整机", "组装电脑", "一体机", "迷你主机", "工作站"],
    "办公设备": ["打印机", "投影仪", "扫描仪", "碎纸机", "考勤机"],
    "电脑配件": ["机械键盘", "无线鼠标", "显示器", "移动硬盘", "U盘"],
    "大家电": ["空调", "冰箱", "洗衣机", "电视机", "热水器"],
    "厨房电器": ["电饭煲", "微波炉", "烤箱", "破壁机", "豆浆机"],
    "生活电器": ["空气净化器", "吸尘器", "加湿器", "电风扇", "取暖器"],
    "个护健康": ["电动牙刷", "剃须刀", "吹风机", "体重秤", "按摩仪"],
    "女装": ["连衣裙", "T恤", "衬衫", "半身裙", "外套"],
    "男装": ["polo衫", "休闲裤", "夹克", "西装", "卫衣"],
    "鞋靴": ["运动鞋", "休闲鞋", "皮鞋", "雪地靴", "帆布鞋"],
    "箱包": ["双肩包", "手提包", "拉杆箱", "斜挎包", "钱包"],
    "面部护肤": ["面膜", "精华液", "面霜", "防晒霜", "洁面乳"],
    "彩妆": ["口红", "粉底液", "眼影", "腮红", "眉笔"],
    "香水": ["女士香水", "男士香水", "中性香水", "淡香水", "浓香水"],
    "美妆工具": ["化妆刷", "美妆蛋", "卷发棒", "修眉刀", "假睫毛"],
    "休闲零食": ["坚果炒货", "肉干肉脯", "糕点饼干", "蜜饯果干", "膨化食品"],
    "粮油调味": ["食用油", "大米", "面粉", "调味酱", "食盐"],
    "饮料冲调": ["矿泉水", "咖啡", "茶叶", "果汁", "奶粉"],
    "生鲜水果": ["新鲜水果", "蔬菜", "肉禽蛋", "海鲜水产", "冷冻食品"],
    "奶粉辅食": ["婴儿奶粉", "米粉米糊", "果泥", "磨牙饼干", "营养面条"],
    "纸尿裤": ["婴儿纸尿裤", "拉拉裤", "湿纸巾", "隔尿垫", "婴儿护肤"],
    "童装童鞋": ["婴儿连体衣", "儿童外套", "儿童运动鞋", "儿童凉鞋", "儿童袜子"],
    "妈妈用品": ["孕妇装", "待产包", "吸奶器", "防溢乳垫", "产后塑身"],
    "运动鞋服": ["跑步鞋", "篮球鞋", "运动T恤", "运动裤", "运动外套"],
    "健身器材": ["哑铃", "瑜伽垫", "跑步机", "拉力器", "仰卧板"],
    "户外装备": ["帐篷", "登山包", "睡袋", "登山杖", "户外手电"],
    "骑行运动": ["自行车", "骑行头盔", "骑行手套", "骑行服", "车灯"],
    "家纺布艺": ["四件套", "枕头", "被子", "毛巾浴巾", "窗帘"],
    "灯具照明": ["吸顶灯", "台灯", "落地灯", "壁灯", "灯带"],
    "家装建材": ["墙漆涂料", "瓷砖", "地板", "壁纸", "五金工具"],
    "收纳整理": ["收纳箱", "衣架", "鞋架", "置物架", "真空袋"],
    "文学小说": ["畅销小说", "经典名著", "网络文学", "散文诗歌", "推理悬疑"],
    "教育考试": ["考试真题", "公务员", "考研辅导", "英语考试", "职业资格"],
    "少儿读物": ["儿童绘本", "拼音读物", "少儿科普", "儿童文学", "启蒙认知"],
    "人文社科": ["历史读物", "哲学宗教", "心理学", "经济管理", "社会科学"],
    "营养保健": ["维生素", "钙片", "鱼油", "益生菌", "蛋白粉"],
    "家庭常备": ["创可贴", "口罩", "酒精棉片", "退烧贴", "感冒药"],
    "医疗器械": ["血压计", "体温计", "血糖仪", "制氧机", "轮椅"],
    "隐形眼镜": ["日抛", "月抛", "年抛", "美瞳", "护理液"],
    "车载电子": ["行车记录仪", "车载充电器", "车载导航", "胎压监测", "车载蓝牙"],
    "汽车装饰": ["座垫套", "方向盘套", "遮阳挡", "车载香薰", "脚垫"],
    "汽车养护": ["机油", "洗车液", "车蜡", "玻璃水", "防冻液"],
    "安全自驾": ["应急工具", "车载灭火器", "反光背心", "三角警示牌", "拖车绳"],
    "黄金饰品": ["黄金项链", "黄金手镯", "黄金戒指", "黄金耳环", "金条"],
    "钻石饰品": ["钻石戒指", "钻石项链", "钻石耳钉", "钻石手链", "裸钻"],
    "银饰": ["银手链", "银项链", "银耳环", "银戒指", "银手镯"],
    "时尚饰品": ["发卡", "胸针", "脚链", "手串", "发箍"],
    "遥控电动": ["遥控车", "遥控飞机", "电动轨道", "遥控船", "遥控机器人"],
    "益智玩具": ["积木", "拼图", "魔方", "科学实验", "磁力片"],
    "乐器": ["吉他", "钢琴", "尤克里里", "口琴", "电子琴"],
    "模型手办": ["高达模型", "盲盒", "手办公仔", "拼装模型", "雕塑摆件"],
    "猫粮猫砂": ["猫干粮", "猫湿粮", "豆腐猫砂", "膨润土猫砂", "混合猫砂"],
    "狗粮狗用": ["狗干粮", "狗湿粮", "狗零食", "牵引绳", "狗窝"],
    "宠物玩具": ["猫抓板", "逗猫棒", "狗咬胶", "飞盘", "猫爬架"],
    "宠物医疗": ["驱虫药", "宠物疫苗", "营养膏", "消毒液", "伤口护理"],
}


def gen_base_categories(out_dir: str):
    """生成三级品类层级, 返回 {cat3_id: (cat3_id, cat2_id, cat1_id)}"""
    # --- cat1 ---
    w1 = CsvWriter(out_dir, "base_category1.csv", ["id", "name"])
    cat1s = {}
    for i, name in enumerate(_CAT1_NAMES, 1):
        w1.write_row([i, name])
        cat1s[i] = name
    w1.close()

    # --- cat2: 每个cat1下4个 = 60 ---
    w2 = CsvWriter(out_dir, "base_category2.csv",
                   ["id", "name", "category1_id"])
    cat2s = {}
    cat2_id = 1
    for c1_id, c1_name in cat1s.items():
        c2_pool = _CAT2_NAMES.get(c1_name, [f"{c1_name}-子类{j}" for j in range(1, 5)])
        for c2name in c2_pool:
            w2.write_row([cat2_id, c2name, c1_id])
            cat2s[cat2_id] = (cat2_id, c2name, c1_id)
            cat2_id += 1
    w2.close()

    # --- cat3: 每个cat2下5个 = 300 ---
    w3 = CsvWriter(out_dir, "base_category3.csv",
                   ["id", "name", "category2_id"])
    cat3s = {}
    cat3_id = 1
    for c2_id, (_, c2name, c1_id) in cat2s.items():
        c3_pool = _CAT3_NAMES.get(c2name, [f"{c2name}-细类{k}" for k in range(1, 6)])
        for c3name in c3_pool:
            w3.write_row([cat3_id, c3name, c2_id])
            cat3s[cat3_id] = (cat3_id, c2_id, c1_id)
            cat3_id += 1
    w3.close()

    return cat1s, cat2s, cat3s


# ========== base_trademark (100) — 真实品牌名 ==========
_REAL_BRANDS = [
    "华为", "小米", "OPPO", "vivo", "联想", "海尔", "美的", "格力", "TCL", "海信",
    "苹果", "三星", "索尼", "松下", "飞利浦", "西门子", "博世", "戴森", "LG", "夏普",
    "耐克", "阿迪达斯", "安踏", "李宁", "特步", "361度", "匹克", "鸿星尔克", "回力", "飞跃",
    "优衣库", "ZARA", "H&M", "波司登", "太平鸟", "森马", "美特斯邦威", "海澜之家", "雅戈尔", "七匹狼",
    "兰蔻", "雅诗兰黛", "欧莱雅", "资生堂", "SK-II", "百雀羚", "自然堂", "珀莱雅", "完美日记", "花西子",
    "蒙牛", "伊利", "农夫山泉", "娃哈哈", "统一", "康师傅", "三只松鼠", "良品铺子", "百草味", "洽洽",
    "全友家居", "顾家家居", "林氏木业", "红星美凯龙", "宜家", "索菲亚", "欧派", "尚品宅配", "曲美", "左右",
    "茅台", "五粮液", "泸州老窖", "青岛啤酒", "雪花啤酒", "张裕", "洋河", "汾酒", "剑南春", "郎酒",
    "方太", "老板电器", "九阳", "苏泊尔", "美菱", "容声", "志高", "奥克斯", "科沃斯", "石头科技",
    "佳能", "尼康", "大疆", "华硕", "技嘉", "微星", "惠普", "戴尔", "罗技", "雷蛇",
]
_BRAND_CATEGORIES = ["电子", "服饰", "食品", "美妆", "家居"]
_COUNTRIES = ["中国", "中国", "中国", "美国", "日本", "韩国", "德国", "法国"]


def gen_base_trademark(out_dir: str):
    w = CsvWriter(out_dir, "base_trademark.csv",
                  ["tm_id", "tm_name", "logo_url", "country",
                   "is_owned_brand", "brand_category"])
    trademarks = {}
    for i in range(1, 101):
        tm_name = _REAL_BRANDS[i - 1]
        logo = f"http://logo.example.com/{i}.png"
        country = random.choice(_COUNTRIES)
        is_owned = 1 if random.random() < 0.2 else 0
        bcat = random.choice(_BRAND_CATEGORIES)
        w.write_row([i, tm_name, logo, country, is_owned, bcat])
        trademarks[i] = tm_name
    w.close()
    return trademarks


# ========== supplier_info (50) — 真实供应商名池 ==========
_SUPPLIER_TYPES = ["厂商直供", "代理商", "经销商", "贸易公司"]
_SUPPLIER_NAME_POOL = [
    "鼎盛供应链", "汇通达商贸", "嘉和物资", "远东实业", "华源供应链",
    "中通物流集团", "瑞丰达贸易", "新世纪商贸", "联合供应链", "永兴实业",
    "盛达物资", "鸿运商贸", "正泰供应链", "天成贸易", "利通实业",
    "华联商贸", "晟丰物资", "方圆供应链", "和顺贸易", "金桥实业",
    "德昌物资", "泰和商贸", "聚源供应链", "万达贸易", "通利实业",
    "恒丰商贸", "信达物资", "中瑞供应链", "广汇贸易", "鑫源实业",
    "诚信物资", "博远商贸", "丰汇供应链", "宏达贸易", "润和实业",
    "国泰商贸", "胜达物资", "长虹供应链", "富源贸易", "新华实业",
    "协鑫物资", "建华商贸", "中鼎供应链", "通宝贸易", "安泰实业",
    "佳盛物资", "亿达商贸", "顺鑫供应链", "隆兴贸易", "祥瑞实业",
]

def gen_supplier_info(out_dir: str):
    """Feature #7: bank_account / contact_phone 含敏感信息格式"""
    w = CsvWriter(out_dir, "supplier_info.csv",
                  ["supplier_id", "name", "type", "contact_phone",
                   "bank_account", "create_time", "operate_time"])
    now = fmt_datetime(datetime(2025, 10, 1, 10, 0, 0))
    for i in range(1, 51):
        sname = _SUPPLIER_NAME_POOL[i - 1]
        stype = random.choice(_SUPPLIER_TYPES)
        phone = random_phone()
        bank = random_bank_account()
        w.write_row([i, sname, stype, phone, bank, now, now])
    w.close()


# ========== warehouse_info (8) ==========
_WAREHOUSE_DATA = [
    (1, "华北仓", "综合仓", 1, 1, 0.20),
    (2, "华东仓", "综合仓", 6, 51, 0.25),
    (3, "华南仓", "综合仓", 13, 121, 0.20),
    (4, "华中仓", "综合仓", 16, 151, 0.12),
    (5, "西南仓", "区域仓", 19, 181, 0.08),
    (6, "东北仓", "区域仓", 29, 281, 0.07),
    (7, "西北仓", "区域仓", 24, 231, 0.05),
    (8, "备用仓", "备用仓", 7, 61, 0.03),
]


def gen_warehouse_info(out_dir: str):
    w = CsvWriter(out_dir, "warehouse_info.csv",
                  ["warehouse_id", "name", "type", "province_id",
                   "city_id", "share"])
    warehouses = {}
    for wid, wname, wtype, pid, cid, share in _WAREHOUSE_DATA:
        w.write_row([wid, wname, wtype, pid, cid, share])
        warehouses[wid] = {
            "warehouse_id": wid, "name": wname,
            "province_id": pid, "city_id": cid, "share": share,
        }
    w.close()
    return warehouses


# ========== marketing_channel (15) ==========
_CHANNELS = [
    (1, "微信", "社交", "wechat", "social"),
    (2, "微博", "社交", "weibo", "social"),
    (3, "抖音", "短视频", "douyin", "video"),
    (4, "快手", "短视频", "kuaishou", "video"),
    (5, "百度SEM", "搜索", "baidu", "cpc"),
    (6, "360搜索", "搜索", "360search", "cpc"),
    (7, "淘宝联盟", "联盟", "taobao_union", "affiliate"),
    (8, "京东联盟", "联盟", "jd_union", "affiliate"),
    (9, "APP推送", "站内", "app_push", "owned"),
    (10, "短信", "站内", "sms", "owned"),
    (11, "邮件", "站内", "email", "owned"),
    (12, "线下门店", "线下", "offline_store", "offline"),
    (13, "小红书", "社交", "xiaohongshu", "social"),
    (14, "B站", "视频", "bilibili", "video"),
    (15, "直接访问", "自然", "direct", "organic"),
]


def gen_marketing_channel(out_dir: str):
    w = CsvWriter(out_dir, "marketing_channel.csv",
                  ["channel_id", "channel_name", "channel_type",
                   "source", "medium"])
    channels = {}
    for cid, cname, ctype, src, med in _CHANNELS:
        w.write_row([cid, cname, ctype, src, med])
        channels[cid] = {"channel_id": cid, "channel_name": cname,
                         "source": src, "medium": med}
    w.close()
    return channels


# ========== dim_date (365天) ==========
# 法定节假日近似 (公历月日, 实际可能偏移)
_HOLIDAYS = {
    (1, 1), (1, 2), (1, 3),          # 元旦
    (1, 28), (1, 29), (1, 30), (1, 31),  # 春节(近似)
    (2, 1), (2, 2), (2, 3),
    (4, 4), (4, 5), (4, 6),          # 清明
    (5, 1), (5, 2), (5, 3), (5, 4), (5, 5),  # 劳动节
    (6, 8), (6, 9), (6, 10),         # 端午(近似)
    (9, 15), (9, 16), (9, 17),       # 中秋(近似)
    (10, 1), (10, 2), (10, 3), (10, 4),
    (10, 5), (10, 6), (10, 7),       # 国庆
}


def gen_dim_date(out_dir: str):
    """生成365天日期维度, 起始 2025-10-01"""
    w = CsvWriter(out_dir, "dim_date.csv",
                  ["date_key", "year", "month", "week", "day_of_week",
                   "quarter", "is_weekend", "is_holiday"])
    start = date(2025, 10, 1)
    dates = {}
    for i in range(365):
        d = start + timedelta(days=i)
        dow = d.isoweekday()  # 1=Mon, 7=Sun
        is_wknd = 1 if dow >= 6 else 0
        is_hol = 1 if (d.month, d.day) in _HOLIDAYS else 0
        q = (d.month - 1) // 3 + 1
        wk = d.isocalendar()[1]
        w.write_row([
            fmt_date(datetime(d.year, d.month, d.day)),
            d.year, d.month, wk, dow, q, is_wknd, is_hol,
        ])
        dates[fmt_date(datetime(d.year, d.month, d.day))] = {
            "is_weekend": is_wknd, "is_holiday": is_hol,
        }
    w.close()
    return dates


# ========== dim_device (2000) ==========
_DEV_TYPES = ["phone", "tablet", "pc"]
_DEV_TYPE_W = [0.70, 0.15, 0.15]
_OS_LIST = ["Android", "iOS", "Windows", "macOS"]
_OS_W = [0.55, 0.30, 0.10, 0.05]
_APP_VER = ["4.0.1", "4.1.0", "4.2.0", "4.3.0", "5.0.0"]
_DEV_BRANDS = [
    "华为", "小米", "OPPO", "vivo", "苹果",
    "三星", "荣耀", "联想", "红米", "一加",
]


def gen_dim_device(out_dir: str):
    w = CsvWriter(out_dir, "dim_device.csv",
                  ["device_id", "device_type", "os", "os_version",
                   "app_version", "brand_name"])
    devices = []
    for i in range(1, 2001):
        dtype = random.choices(_DEV_TYPES, weights=_DEV_TYPE_W, k=1)[0]
        os_name = random.choices(_OS_LIST, weights=_OS_W, k=1)[0]
        os_ver = f"{random.randint(10, 15)}.{random.randint(0, 4)}"
        app_ver = random.choice(_APP_VER)
        brand = random.choice(_DEV_BRANDS)
        w.write_row([i, dtype, os_name, os_ver, app_ver, brand])
        devices.append(i)
    w.close()
    return devices


# ========== dim_carrier (10) ==========
_CARRIERS = [
    (1, "顺丰速运", 0.25, 0.85, 0.01),
    (2, "中通快递", 0.18, 0.70, 0.03),
    (3, "圆通速递", 0.15, 0.68, 0.035),
    (4, "韵达速递", 0.12, 0.65, 0.04),
    (5, "申通快递", 0.08, 0.64, 0.04),
    (6, "极兔速递", 0.07, 0.72, 0.025),
    (7, "邮政EMS", 0.05, 0.60, 0.02),
    (8, "京东物流", 0.05, 0.90, 0.008),
    (9, "德邦快递", 0.03, 0.62, 0.03),
    (10, "百世快递", 0.02, 0.58, 0.05),
]


def gen_dim_carrier(out_dir: str):
    w = CsvWriter(out_dir, "dim_carrier.csv",
                  ["carrier_id", "carrier_name", "share",
                   "speed_factor", "exception_rate"])
    carriers = {}
    for cid, cname, share, spd, exc in _CARRIERS:
        w.write_row([cid, cname, share, spd, exc])
        carriers[cid] = {
            "carrier_id": cid, "carrier_name": cname,
            "share": share, "speed_factor": spd,
            "exception_rate": exc,
        }
    w.close()
    return carriers


# ========== merchant_info (200) — 真实商家名 ==========
_MERCHANT_TYPES = ["flagship", "self", "third_party"]
_MERCHANT_TYPE_W = [0.25, 0.15, 0.60]
_INDUSTRIES = ["电子", "服饰", "食品", "美妆", "家居", "运动", "母婴", "医药"]
_MERCHANT_NAME_PARTS = [
    "优品", "嘉禾", "盛世", "百汇", "瑞祥", "金鹏", "鸿达", "正泰", "博雅", "恒信",
    "万象", "天成", "华联", "新世界", "永兴", "利丰", "合众", "中信", "广达", "融通",
    "乐天", "凯旋", "锦绣", "龙腾", "鼎盛", "长兴", "裕丰", "泰安", "世纪", "远大",
    "金源", "弘扬", "信达", "同创", "富邦", "安达", "联盛", "天佑", "卓越", "方正",
    "晨曦", "云起", "星源", "海蓝", "山川", "紫霞", "流光", "清风", "碧波", "翠微",
    "启航", "汇通", "明远", "宏图", "志远", "兴华", "福泰", "顺达", "荣盛", "昌盛",
]
# 旗舰店/官方自营: 真实品牌风格名池
_FLAGSHIP_BRANDS = {
    "电子": ["华为", "小米", "OPPO", "vivo", "联想", "海尔", "格力", "美的", "荣耀", "一加", "魅族", "TCL"],
    "服饰": ["优衣库", "波司登", "太平鸟", "海澜之家", "森马", "拉夏贝尔", "真维斯", "美特斯邦威", "江南布衣", "例外"],
    "食品": ["三只松鼠", "良品铺子", "百草味", "旺旺", "洽洽", "卫龙", "老干妈", "李子柒", "劲仔", "甘源"],
    "美妆": ["珀莱雅", "薇诺娜", "自然堂", "韩束", "相宜本草", "丸美", "片仔癀", "花西子", "完美日记", "谷雨"],
    "家居": ["宜家", "索菲亚", "欧派", "顾家家居", "林氏家居", "芝华仕", "曲美", "全友", "红星", "居然"],
    "运动": ["李宁", "安踏", "特步", "鸿星尔克", "361度", "匹克", "乔丹", "德尔惠", "贵人鸟", "南极人"],
    "母婴": ["好孩子", "贝亲", "安贝贝", "飞鹤", "惠氏", "雅培", "贝因美", "伊威", "babycare", "英氏"],
    "医药": ["同仁堂", "云南白药", "华润三九", "葵花药业", "仁和药业", "天士力", "康恩贝", "江中药业", "东阿阿胶", "太极集团"],
}
_MERCHANT_SUFFIXES = {"flagship": "官方旗舰店", "self": "官方自营店", "third_party": "专营店"}


def gen_merchant_info(out_dir: str, provinces: dict):
    w = CsvWriter(out_dir, "merchant_info.csv",
                  ["merchant_id", "merchant_name", "merchant_type",
                   "industry", "province", "merchant_rating",
                   "open_date", "create_time", "operate_time"])
    merchants = {}
    now = fmt_datetime(datetime(2025, 10, 1, 8, 0, 0))
    province_ids = list(provinces.keys())
    pool_len = len(_MERCHANT_NAME_PARTS)
    for i in range(1, 201):
        mtype = random.choices(
            _MERCHANT_TYPES, weights=_MERCHANT_TYPE_W, k=1)[0]
        industry = random.choice(_INDUSTRIES)
        pid = random.choice(province_ids)
        pname = provinces[pid][1]
        rating = round(random.uniform(3.0, 5.0), 1)
        oday = date(2025, 10, 1) - timedelta(days=random.randint(30, 1000))
        suffix = _MERCHANT_SUFFIXES[mtype]
        if mtype in ("flagship", "self"):
            brand_pool = _FLAGSHIP_BRANDS.get(industry, _MERCHANT_NAME_PARTS)
            brand = brand_pool[(i * 7) % len(brand_pool)]
            mname = f"{brand}{suffix}"
        else:
            part = _MERCHANT_NAME_PARTS[(i * 7) % pool_len]
            mname = f"{part}{industry}{suffix}"
        w.write_row([
            i, mname, mtype, industry, pname,
            rating, fmt_date(datetime(oday.year, oday.month, oday.day)),
            now, now,
        ])
        merchants[i] = {
            "merchant_id": i, "merchant_type": mtype,
            "industry": industry, "province_id": pid,
        }
    w.close()
    return merchants


# ========== 总入口 ==========
def generate_all_dimensions(out_dir: str):
    """按序生成 Phase1 全部 15 张基础维表, 返回下游依赖的数据字典"""
    print("[Phase1] 生成 base_region ...")
    regions = gen_base_region(out_dir)

    print("[Phase1] 生成 base_province ...")
    provinces = gen_base_province(out_dir)

    print("[Phase1] 生成 base_city ...")
    cities = gen_base_city(out_dir, provinces)

    print("[Phase1] 生成 base_district ...")
    districts = gen_base_district(out_dir, cities)

    print("[Phase1] 生成 base_category1/2/3 ...")
    cat1s, cat2s, cat3s = gen_base_categories(out_dir)

    print("[Phase1] 生成 base_trademark ...")
    trademarks = gen_base_trademark(out_dir)

    print("[Phase1] 生成 supplier_info ...")
    gen_supplier_info(out_dir)

    print("[Phase1] 生成 warehouse_info ...")
    warehouses = gen_warehouse_info(out_dir)

    print("[Phase1] 生成 marketing_channel ...")
    channels = gen_marketing_channel(out_dir)

    print("[Phase1] 生成 dim_date ...")
    dates = gen_dim_date(out_dir)

    print("[Phase1] 生成 dim_device ...")
    devices = gen_dim_device(out_dir)

    print("[Phase1] 生成 dim_carrier ...")
    carriers = gen_dim_carrier(out_dir)

    print("[Phase1] 生成 merchant_info ...")
    merchants = gen_merchant_info(out_dir, provinces)

    print("[Phase1] 基础维表全部完成 (15张表)")
    return {
        "regions": regions,
        "provinces": provinces,
        "cities": cities,
        "districts": districts,
        "cat1s": cat1s,
        "cat2s": cat2s,
        "cat3s": cat3s,
        "trademarks": trademarks,
        "warehouses": warehouses,
        "channels": channels,
        "dates": dates,
        "devices": devices,
        "carriers": carriers,
        "merchants": merchants,
    }
