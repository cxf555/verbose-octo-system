"""物品系统：武器、防具、药水"""
from enum import Enum, auto


class ItemType(Enum):
    WEAPON = auto()
    ARMOR = auto()
    POTION = auto()


class Rarity:
    """稀有度常量"""
    COMMON = "common"    # 绿色
    RARE = "rare"        # 蓝色
    EPIC = "epic"        # 橙色
    LEGENDARY = "legendary"  # 红色

    COLORS = {
        COMMON: (76, 175, 80),      # 绿
        RARE: (66, 165, 245),       # 蓝
        EPIC: (255, 152, 0),        # 橙
        LEGENDARY: (244, 67, 54),   # 红
    }

    NAMES = {
        COMMON: "普通",
        RARE: "稀有",
        EPIC: "史诗",
        LEGENDARY: "传说",
    }


class Item:
    def __init__(self, name, description, item_type):
        self.name = name
        self.description = description
        self.item_type = item_type


class Weapon(Item):
    def __init__(self, name, description, weapon_type, rarity,
                 attack_bonus, range_val=0, width=0,
                 crit_rate=0.0, crit_damage=1.5, lifesteal=0.0,
                 cooldown=None, projectile_speed=0):
        super().__init__(name, description, ItemType.WEAPON)
        self.weapon_type = weapon_type  # "melee" 或 "ranged"
        self.rarity = rarity
        self.attack_bonus = attack_bonus
        self.range_bonus = range_val      # 近战：攻击范围加成；远程不使用
        self.width = width                # 近战：攻击宽度
        self.crit_rate = crit_rate
        self.crit_damage = crit_damage
        self.lifesteal = lifesteal
        self.cooldown = cooldown          # 远程：攻击冷却ms（None=用默认）
        self.projectile_speed = projectile_speed  # 远程：弹幕速度
        self.color = Rarity.COLORS[rarity]

    @property
    def rarity_name(self):
        return Rarity.NAMES[self.rarity]


class Armor(Item):
    def __init__(self, name, description, reduction, rarity=Rarity.COMMON):
        super().__init__(name, description, ItemType.ARMOR)
        self.reduction = reduction  # 0.0~1.0 减伤比例
        self.rarity = rarity
        self.color = Rarity.COLORS[rarity]

    @property
    def rarity_name(self):
        return Rarity.NAMES[self.rarity]


class Potion(Item):
    def __init__(self, name, description, heal_amount):
        super().__init__(name, description, ItemType.POTION)
        self.heal_amount = heal_amount


# ---- 武器库 ----

WEAPON_DB = [
    # === 近战 - 绿色(普通) ===
    {"name": "木棒", "rarity": Rarity.COMMON, "type": "melee",
     "atk": 3, "range": 40, "width": 40},
    {"name": "短剑", "rarity": Rarity.COMMON, "type": "melee",
     "atk": 5, "range": 45, "width": 35},
    {"name": "铁剑", "rarity": Rarity.COMMON, "type": "melee",
     "atk": 6, "range": 50, "width": 40},
    {"name": "手斧", "rarity": Rarity.COMMON, "type": "melee",
     "atk": 7, "range": 40, "width": 50},

    # === 近战 - 蓝色(稀有) ===
    {"name": "长矛", "rarity": Rarity.RARE, "type": "melee",
     "atk": 8, "range": 80, "width": 30, "crit_rate": 0.10, "crit_dmg": 1.5},
    {"name": "战斧", "rarity": Rarity.RARE, "type": "melee",
     "atk": 10, "range": 50, "width": 60, "crit_rate": 0.05, "crit_dmg": 1.8},
    {"name": "弯刀", "rarity": Rarity.RARE, "type": "melee",
     "atk": 9, "range": 55, "width": 45, "crit_rate": 0.12, "crit_dmg": 1.5},
    {"name": "骑士剑", "rarity": Rarity.RARE, "type": "melee",
     "atk": 11, "range": 60, "width": 45, "crit_rate": 0.08, "crit_dmg": 1.6},
    {"name": "流星锤", "rarity": Rarity.RARE, "type": "melee",
     "atk": 12, "range": 55, "width": 55, "crit_rate": 0.05, "crit_dmg": 2.0},

    # === 近战 - 橙色(史诗) ===
    {"name": "火焰剑", "rarity": Rarity.EPIC, "type": "melee",
     "atk": 14, "range": 55, "width": 45, "crit_rate": 0.15, "crit_dmg": 2.0},
    {"name": "冰霜刃", "rarity": Rarity.EPIC, "type": "melee",
     "atk": 13, "range": 60, "width": 40, "crit_rate": 0.20, "crit_dmg": 1.8},
    {"name": "暗影匕首", "rarity": Rarity.EPIC, "type": "melee",
     "atk": 12, "range": 35, "width": 25, "crit_rate": 0.30, "crit_dmg": 2.5},
    {"name": "巨剑", "rarity": Rarity.EPIC, "type": "melee",
     "atk": 18, "range": 70, "width": 55, "crit_rate": 0.10, "crit_dmg": 2.0},

    # === 近战 - 红色(传说) ===
    {"name": "圣剑", "rarity": Rarity.LEGENDARY, "type": "melee",
     "atk": 17, "range": 60, "width": 50, "crit_rate": 0.20, "crit_dmg": 2.2, "lifesteal": 0.12},
    {"name": "龙牙", "rarity": Rarity.LEGENDARY, "type": "melee",
     "atk": 22, "range": 65, "width": 45, "crit_rate": 0.15, "crit_dmg": 2.5, "lifesteal": 0.15},
    {"name": "雷锤", "rarity": Rarity.LEGENDARY, "type": "melee",
     "atk": 20, "range": 50, "width": 65, "crit_rate": 0.10, "crit_dmg": 2.0, "lifesteal": 0.18},

    # === 远程 - 绿色(普通) ===
    {"name": "短弓", "rarity": Rarity.COMMON, "type": "ranged",
     "atk": 2, "cooldown": 500, "proj_speed": 600},

    # === 远程 - 蓝色(稀有) ===
    {"name": "猎弓", "rarity": Rarity.RARE, "type": "ranged",
     "atk": 3, "cooldown": 450, "proj_speed": 675, "crit_rate": 0.10, "crit_dmg": 1.5},
    {"name": "连弩", "rarity": Rarity.RARE, "type": "ranged",
     "atk": 2, "cooldown": 250, "proj_speed": 750, "crit_rate": 0.08, "crit_dmg": 1.5},

    # === 远程 - 橙色(史诗) ===
    {"name": "魔法弹珠", "rarity": Rarity.EPIC, "type": "ranged",
     "atk": 4, "cooldown": 400, "proj_speed": 630, "crit_rate": 0.18, "crit_dmg": 2.0},

    # === 远程 - 红色(传说) ===
    {"name": "毁灭者", "rarity": Rarity.LEGENDARY, "type": "ranged",
     "atk": 6, "cooldown": 350, "proj_speed": 750, "crit_rate": 0.22, "crit_dmg": 2.2, "lifesteal": 0.10},
]
