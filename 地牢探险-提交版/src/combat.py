"""战斗系统：攻击判定、伤害计算、掉落"""
import math
import random
from src.items import Weapon, Armor, Potion, WEAPON_DB, Rarity


def melee_attack(attacker, targets, attack_range, attack_width, damage,
                 crit_rate=0.0, crit_damage=1.5, lifesteal=0.0):
    """近战扇形攻击判定，圆心在角色位置。

    返回: [(target, actual_damage, knockback_x, knockback_y, is_crit, heal_amount), ...]
    """
    hits = []
    half_angle = math.atan2(attack_width / 2, attack_range) * 1.3  # 扇形半角加大30%
    radius = attack_range + 25  # 扩大范围

    for target in targets:
        if not hasattr(target, "is_alive") or not target.is_alive:
            continue
        target_r = getattr(target, 'radius', 16)

        # 目标是否在扇形内
        if _point_in_sector(target.x, target.y,
                            attacker.x, attacker.y,
                            attacker.facing_angle, half_angle,
                            radius + target_r):
            is_crit = random.random() < crit_rate
            actual_damage = damage
            if is_crit:
                actual_damage = int(damage * crit_damage)
            actual_damage = target.take_damage(actual_damage)

            heal_amount = int(actual_damage * lifesteal) if lifesteal > 0 else 0

            knockback_x = math.cos(attacker.facing_angle) * 150
            knockback_y = math.sin(attacker.facing_angle) * 150
            hits.append((target, actual_damage, knockback_x, knockback_y, is_crit, heal_amount))

    return hits


def _point_in_sector(px, py, cx, cy, facing_angle, half_angle, radius):
    """判断点是否在以(cx,cy)为圆心、facing_angle方向、half_angle半角、radius半径的扇形内"""
    dx = px - cx
    dy = py - cy
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > radius:
        return False
    # 点到圆心的角度
    point_angle = math.atan2(dy, dx)
    # 角度差（处理 -pi/pi 环绕）
    diff = abs(point_angle - facing_angle)
    if diff > math.pi:
        diff = 2 * math.pi - diff
    return diff <= half_angle


# 楼层 → 稀有度权重
RARITY_WEIGHTS_BY_FLOOR = {
    1: {Rarity.COMMON: 70, Rarity.RARE: 20, Rarity.EPIC: 8, Rarity.LEGENDARY: 2},
    2: {Rarity.COMMON: 70, Rarity.RARE: 20, Rarity.EPIC: 8, Rarity.LEGENDARY: 2},
    3: {Rarity.COMMON: 50, Rarity.RARE: 30, Rarity.EPIC: 15, Rarity.LEGENDARY: 5},
    4: {Rarity.COMMON: 30, Rarity.RARE: 35, Rarity.EPIC: 23, Rarity.LEGENDARY: 12},
    5: {Rarity.COMMON: 10, Rarity.RARE: 30, Rarity.EPIC: 35, Rarity.LEGENDARY: 25},
}


def _pick_weapon_by_rarity(rarity):
    """从武器库中按稀有度随机选一把"""
    candidates = [w for w in WEAPON_DB if w["rarity"] == rarity]
    return random.choice(candidates) if candidates else random.choice(WEAPON_DB)


def generate_loot(x, y, floor_level):
    """根据楼层等级生成掉落物品"""
    loot_chance = 0.40
    if random.random() > loot_chance:
        return None

    roll = random.random()
    if roll < 0.40:
        # 药水
        heal_power = random.randint(20, 35 + floor_level * 5)
        return (Potion(f"生命药水 Lv.{floor_level}", f"恢复 {heal_power} 点生命", heal_power), x, y)
    elif roll < 0.78:
        # 武器：按楼层权重选稀有度
        w = _pick_weapon_by_rarity(_weighted_rarity(floor_level))
        return (_build_weapon(w, floor_level), x, y)
    else:
        armor_by_rarity = {
            Rarity.COMMON: ("皮甲", 0.30),
            Rarity.RARE: ("锁子甲", 0.50),
            Rarity.EPIC: ("铁板甲", 0.65),
            Rarity.LEGENDARY: ("龙鳞甲", 0.80),
        }
        rarity = _weighted_rarity(floor_level)
        name, base_reduction = armor_by_rarity[rarity]
        reduction = min(0.85, base_reduction + floor_level * 0.01)
        label = f"[{Rarity.NAMES[rarity]}]{name}"
        return (Armor(label, f"减伤 {int(reduction*100)}%", reduction, rarity), x, y)


def _weighted_rarity(floor_level):
    """按楼层权重随机返回稀有度"""
    weights = RARITY_WEIGHTS_BY_FLOOR.get(floor_level, RARITY_WEIGHTS_BY_FLOOR[1])
    rarities = list(weights.keys())
    w = list(weights.values())
    return random.choices(rarities, weights=w, k=1)[0]


def _build_weapon(data, floor_level):
    """根据武器模板 + 楼层加成构建 Weapon 对象"""
    atk = data["atk"] + random.randint(0, floor_level * 2)
    desc_parts = [f"攻击 +{atk}"]

    crit_rate = data.get("crit_rate", 0.0)
    crit_dmg = data.get("crit_dmg", 1.5)
    lifesteal = data.get("lifesteal", 0.0)

    if crit_rate > 0:
        desc_parts.append(f"暴击率 {int(crit_rate*100)}%")
    if crit_dmg > 1.5:
        desc_parts.append(f"暴击伤害 {crit_dmg:.1f}x")
    if lifesteal > 0:
        desc_parts.append(f"吸血 {int(lifesteal*100)}%")

    name = f"[{Rarity.NAMES[data['rarity']]}]{data['name']}"

    return Weapon(
        name=name,
        description=" | ".join(desc_parts),
        weapon_type=data["type"],
        rarity=data["rarity"],
        attack_bonus=atk,
        range_val=data.get("range", 0),
        width=data.get("width", 0),
        crit_rate=crit_rate,
        crit_damage=crit_dmg,
        lifesteal=lifesteal,
        cooldown=data.get("cooldown"),
        projectile_speed=data.get("proj_speed", 0),
    )
