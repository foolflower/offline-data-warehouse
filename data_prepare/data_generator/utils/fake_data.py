"""
中文姓名/手机号/身份证/地址生成
对应 plan.md 特征#7 敏感信息: 手机号13x/15x/18x, 身份证18位, 银行卡16/19位
"""
import random
import string

# ── 中文姓氏 (常见100姓) ──
_SURNAMES = [
    '王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
    '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
    '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
    '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
    '苏', '卢', '蒋', '蔡', '贾', '丁', '魏', '薛', '叶', '阎',
    '余', '潘', '杜', '戴', '夏', '钟', '汪', '田', '任', '姜',
    '范', '方', '石', '姚', '谭', '廖', '邹', '熊', '金', '陆',
    '郝', '孔', '白', '崔', '康', '毛', '邱', '秦', '江', '史',
    '顾', '侯', '邵', '孟', '龙', '万', '段', '漕', '钱', '汤',
    '尹', '黎', '易', '常', '武', '乔', '贺', '赖', '龚', '文',
]

# ── 名字常用字 ──
_NAME_CHARS = (
    '伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全'
    '国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和'
    '彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦'
    '亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德'
    '秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲'
    '真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊'
)


def random_chinese_name() -> str:
    surname = random.choice(_SURNAMES)
    name_len = random.choices([1, 2], weights=[0.3, 0.7])[0]
    given = ''.join(random.choice(_NAME_CHARS) for _ in range(name_len))
    return surname + given


def random_phone() -> str:
    """手机号13x/15x/18x格式 (特征#7)"""
    prefix = random.choice(['13', '15', '18'])
    suffix = ''.join(random.choices(string.digits, k=9))
    return prefix + suffix


def random_id_card() -> str:
    """身份证18位 (特征#7)"""
    # 地区码 (6位, 使用常见地区码)
    area_codes = [
        '110101', '110102', '310101', '310104', '440103', '440305',
        '320102', '320505', '330102', '330106', '420102', '500103',
        '510104', '610102', '370102', '350102', '430104', '340102',
    ]
    area = random.choice(area_codes)
    # 出生日期 (8位)
    year = random.randint(1960, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    birth = f'{year}{month:02d}{day:02d}'
    # 序号 (3位)
    seq = f'{random.randint(1, 999):03d}'
    # 校验位 (简化，随机)
    check = random.choice('0123456789X')
    return area + birth + seq + check


def random_bank_account() -> str:
    """银行卡16/19位 (特征#7)"""
    length = random.choice([16, 19])
    return ''.join(random.choices(string.digits, k=length))


def random_email(login_name: str) -> str:
    domains = ['qq.com', '163.com', 'gmail.com', 'sina.com', '126.com', 'outlook.com']
    return f'{login_name}@{random.choice(domains)}'


def mask_phone(phone: str) -> str:
    """脱敏: 138****0012"""
    if len(phone) >= 11:
        return phone[:3] + '****' + phone[7:]
    return phone


def mask_id_card(id_card: str) -> str:
    """脱敏: 43****34"""
    if len(id_card) >= 18:
        return id_card[:2] + '****' + id_card[-2:]
    return id_card


def mask_name(name: str) -> str:
    """脱敏: 张*"""
    if len(name) >= 2:
        return name[0] + '*' * (len(name) - 1)
    return name
