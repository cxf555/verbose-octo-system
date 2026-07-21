"""敌人系统：基类 + 具体敌人类型 + AI 状态机"""
import math
import random
import pygame
from enum import Enum, auto
import settings
from src.tile import Tile
from src.projectile import Projectile


class EnemyState(Enum):
    IDLE = auto()
    PATROL = auto()
    ALERT = auto()
    CHASE = auto()
    ATTACK = auto()


class Enemy:
    """敌人基类"""
    def __init__(self, x, y, name, max_hp, attack, defense, speed,
                 detect_range, attack_range, attack_cooldown, color, radius=14):
        self.x = float(x)
        self.y = float(y)
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.detect_range = detect_range
        self.attack_range_val = attack_range
        self.attack_cooldown = attack_cooldown
        self.attack_timer = 0
        self.color = color
        self.radius = radius
        self.is_alive = True

        # AI
        self.state = EnemyState.IDLE
        self.state_timer = random.uniform(0, 2)
        self.patrol_target = (x, y)
        self.knockback_vx = 0
        self.knockback_vy = 0

        # 闪烁（受伤反馈）
        self.hit_flash = 0

        self.is_boss = False

        # 弹幕队列：game.py 每帧检查并取出
        self.pending_projectiles = []

        # 召唤队列：Boss技能，(x, y, EnemyClass)
        self.pending_spawns = []

    def update(self, dt, player, dungeon_tiles):
        """每帧更新"""
        if not self.is_alive:
            return

        # 冷却
        if self.attack_timer > 0:
            self.attack_timer -= dt * 1000
        if self.hit_flash > 0:
            self.hit_flash -= dt * 1000

        # 击退衰减
        if abs(self.knockback_vx) > 5 or abs(self.knockback_vy) > 5:
            self.x += self.knockback_vx * dt
            self.y += self.knockback_vy * dt
            self.knockback_vx *= 0.85
            self.knockback_vy *= 0.85
            self._clamp_to_walkable(dungeon_tiles)
        else:
            self.knockback_vx = 0
            self.knockback_vy = 0

        # AI 状态机
        self._update_ai(dt, player, dungeon_tiles)

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return

        dist_to_player = self._distance_to(player.x, player.y)

        # 状态转换
        if self.state in (EnemyState.IDLE, EnemyState.PATROL):
            if dist_to_player <= self.detect_range * settings.TILE_SIZE:
                self.state = EnemyState.ALERT
        elif self.state == EnemyState.ALERT:
            self.state = EnemyState.CHASE
        elif self.state == EnemyState.CHASE:
            if dist_to_player > settings.ENEMY_FORGET_RANGE * settings.TILE_SIZE:
                self.state = EnemyState.IDLE
            elif dist_to_player <= self.attack_range_val:
                self.state = EnemyState.ATTACK
        elif self.state == EnemyState.ATTACK:
            if dist_to_player > self.attack_range_val + 20:
                self.state = EnemyState.CHASE

        self.state_timer -= dt

        # 状态行为
        if self.state == EnemyState.IDLE:
            if self.state_timer <= 0:
                self.state = EnemyState.PATROL
                angle = random.uniform(0, math.pi * 2)
                self.patrol_target = (
                    self.x + math.cos(angle) * random.randint(40, 120),
                    self.y + math.sin(angle) * random.randint(40, 120),
                )
                self.state_timer = random.uniform(1.5, 3.0)
        elif self.state == EnemyState.PATROL:
            if self.state_timer <= 0:
                self.state = EnemyState.IDLE
                self.state_timer = random.uniform(0.5, 2.0)
            else:
                self._move_toward(self.patrol_target[0], self.patrol_target[1], self.speed * 0.4, dt, dungeon_tiles)
        elif self.state in (EnemyState.ALERT, EnemyState.CHASE):
            self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
        elif self.state == EnemyState.ATTACK:
            self._perform_attack(player)

    def _move_toward(self, tx, ty, spd, dt, dungeon_tiles):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 2:
            return
        self.x += (dx / dist) * spd * dt
        self.y += (dy / dist) * spd * dt
        self._clamp_to_walkable(dungeon_tiles)

    def _clamp_to_walkable(self, dungeon_tiles):
        """防止走进墙壁"""
        ts = settings.TILE_SIZE
        offsets = [(self.radius, 0), (-self.radius, 0), (0, self.radius), (0, -self.radius)]
        for ox, oy in offsets:
            tx = int((self.x + ox) // ts)
            ty = int((self.y + oy) // ts)
            if 0 <= ty < len(dungeon_tiles) and 0 <= tx < len(dungeon_tiles[0]):
                if dungeon_tiles[ty][tx] == Tile.WALL:
                    # 推回
                    cx = (tx * ts + ts // 2)
                    cy = (ty * ts + ts // 2)
                    push_x = self.x - cx
                    push_y = self.y - cy
                    dist = math.sqrt(push_x * push_x + push_y * push_y) or 1
                    self.x = cx + push_x / dist * (ts // 2 + self.radius)
                    self.y = cy + push_y / dist * (ts // 2 + self.radius)

    def _perform_attack(self, player):
        """执行攻击（子类可覆盖）"""
        if self.attack_timer <= 0:
            player.take_damage(self.attack)
            self.attack_timer = self.attack_cooldown

    def take_damage(self, amount):
        """受到伤害"""
        actual = max(1, amount - self.defense)
        self.hp -= actual
        self.hit_flash = 100
        if self.hp <= 0:
            self.hp = 0
            self.is_alive = False
        return actual

    def _distance_to(self, tx, ty):
        return math.sqrt((tx - self.x) ** 2 + (ty - self.y) ** 2)

    @property
    def is_dead(self):
        return not self.is_alive


def _floor_scale(floor_level):
    """每层属性倍率: 1.3^(floor-1)（仅影响HP攻击，不影响速度）"""
    return 1.3 ** (floor_level - 1)


def _speed(base_ratio, floor_level):
    """速度 = 玩家移速 * 比例 * 每层+5%"""
    s = settings.PLAYER_SPEED * base_ratio * (1 + 0.05 * (floor_level - 1))
    return int(s)


class Slime(Enemy):
    """史莱姆 — 近战追击（慢但血量高）"""
    def __init__(self, x, y, floor_level=1):
        s = _floor_scale(floor_level)
        hp = int((25 + floor_level * 8) * s)
        atk = int((6 + floor_level * 2) * s)
        super().__init__(
            x, y, "史莱姆",
            max_hp=hp, attack=atk, defense=1,
            speed=_speed(0.70, floor_level),
            detect_range=6, attack_range=35, attack_cooldown=900,
            color=settings.COLOR_ENEMY_SLIME,
            radius=13
        )


class SkeletonArcher(Enemy):
    """骷髅射手 — 远程弹幕攻击，标准速度"""
    def __init__(self, x, y, floor_level=1):
        s = _floor_scale(floor_level)
        hp = int((20 + floor_level * 5) * s)
        atk = int((8 + floor_level * 2) * s)
        super().__init__(
            x, y, "骷髅射手",
            max_hp=hp, attack=atk, defense=1,
            speed=_speed(1.0, floor_level),
            detect_range=8, attack_range=200, attack_cooldown=1500,
            color=settings.COLOR_ENEMY_ARCHER,
            radius=12
        )
        self.preferred_distance = 140

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return

        dist_to_player = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL):
            if dist_to_player <= self.detect_range * settings.TILE_SIZE:
                self.state = EnemyState.ALERT
        elif self.state == EnemyState.ALERT:
            self.state = EnemyState.CHASE
        elif self.state == EnemyState.CHASE:
            if dist_to_player > settings.ENEMY_FORGET_RANGE * settings.TILE_SIZE:
                self.state = EnemyState.IDLE
            elif dist_to_player <= self.attack_range_val:
                self.state = EnemyState.ATTACK

        self.state_timer -= dt

        if self.state in (EnemyState.ALERT, EnemyState.CHASE):
            if dist_to_player > self.preferred_distance:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
            elif dist_to_player < self.preferred_distance - 30:
                self._move_toward(player.x, player.y, -self.speed * 0.6, dt, dungeon_tiles)
        elif self.state == EnemyState.ATTACK:
            if dist_to_player > self.attack_range_val + 30:
                self.state = EnemyState.CHASE
            self._perform_attack(player)
        elif self.state == EnemyState.IDLE:
            if self.state_timer <= 0:
                self.state = EnemyState.PATROL
                angle = random.uniform(0, math.pi * 2)
                self.patrol_target = (
                    self.x + math.cos(angle) * random.randint(40, 100),
                    self.y + math.sin(angle) * random.randint(40, 100),
                )
                self.state_timer = random.uniform(1.5, 3.0)
        elif self.state == EnemyState.PATROL:
            if self.state_timer <= 0:
                self.state = EnemyState.IDLE
                self.state_timer = random.uniform(0.5, 2.0)
            else:
                self._move_toward(self.patrol_target[0], self.patrol_target[1], self.speed * 0.3, dt, dungeon_tiles)

    def _perform_attack(self, player):
        if self.attack_timer <= 0:
            p = Projectile(self.x, self.y, player.x, player.y, self.attack, speed=260)
            self.pending_projectiles.append(p)
            self.attack_timer = self.attack_cooldown


class ShadowAssassin(Enemy):
    """暗影刺客 — 极快但血量极低，近战"""
    def __init__(self, x, y, floor_level=1):
        s = _floor_scale(floor_level)
        hp = int((12 + floor_level * 3) * s)
        atk = int((10 + floor_level * 2) * s)
        super().__init__(
            x, y, "暗影刺客",
            max_hp=hp, attack=atk, defense=1,
            speed=_speed(1.0, floor_level),
            detect_range=7, attack_range=30, attack_cooldown=600,
            color=(180, 80, 220),
            radius=10
        )


class BossDemon(Enemy):
    """Boss 恶魔领主 — 第 5 层，近战+冲刺+扇形弹幕"""
    def __init__(self, x, y):
        s = _floor_scale(5)
        hp = int(250 * s)
        atk = int(20 * s)
        super().__init__(
            x, y, "恶魔领主",
            max_hp=hp, attack=atk, defense=4,
            speed=_speed(0.90, 5),
            detect_range=12, attack_range=55, attack_cooldown=600,
            color=settings.COLOR_BOSS,
            radius=22
        )
        self.is_boss = True
        self.phase = 1
        self.charge_cooldown = 0
        self.charge_dir = 0
        self.burst_cooldown = 0  # 扇形弹幕冷却

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return

        dist_to_player = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL, EnemyState.ALERT):
            self.state = EnemyState.CHASE

        self.state_timer -= dt
        if self.charge_cooldown > 0:
            self.charge_cooldown -= dt * 1000
        if self.burst_cooldown > 0:
            self.burst_cooldown -= dt * 1000

        if self.state == EnemyState.CHASE:
            if dist_to_player <= self.attack_range_val:
                self.state = EnemyState.ATTACK
            else:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)

        elif self.state == EnemyState.ATTACK:
            if dist_to_player > self.attack_range_val + 30:
                self.state = EnemyState.CHASE
            else:
                if self.hp < self.max_hp * 0.5 and self.phase == 1:
                    self.phase = 2
                    self.speed = _speed(1.15, 5)
                    self.attack_cooldown = 400

                # 近战攻击
                if self.attack_timer <= 0:
                    self._perform_attack(player)
                    self.attack_timer = self.attack_cooldown

                # 冲刺攻击
                if self.charge_cooldown <= 0 and dist_to_player > 80:
                    self.charge_cooldown = 2500
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.sqrt(dx * dx + dy * dy) or 1
                    self.charge_dir = (dx / dist, dy / dist)

                # 第2阶段：扇形弹幕
                if self.phase == 2 and self.burst_cooldown <= 0 and dist_to_player > 60:
                    self.burst_cooldown = 2000
                    self._fire_burst(player)

        # 冲刺
        if self.charge_cooldown > 2000:
            charge_speed = 400
            self.x += self.charge_dir[0] * charge_speed * dt
            self.y += self.charge_dir[1] * charge_speed * dt
            self._clamp_to_walkable(dungeon_tiles)
            if self._distance_to(player.x, player.y) < self.radius + player.radius + 10:
                player.take_damage(self.attack + 10)
                self.charge_cooldown = 2000

    def _fire_burst(self, player):
        """发射 3 枚扇形散射弹幕"""
        base_angle = math.atan2(player.y - self.y, player.x - self.x)
        for offset in (-0.35, 0, 0.35):
            angle = base_angle + offset
            tx = self.x + math.cos(angle) * 200
            ty = self.y + math.sin(angle) * 200
            p = Projectile(self.x, self.y, tx, ty, self.attack + 5, speed=230)
            self.pending_projectiles.append(p)


class GiantSlimeKing(Enemy):
    """F1 Boss — 巨型史莱姆王：慢速近战，半血分裂成3只普通史莱姆"""
    def __init__(self, x, y):
        s = _floor_scale(1)
        hp = int(180 * s)
        atk = int(14 * s)
        super().__init__(
            x, y, "巨型史莱姆王",
            max_hp=hp, attack=atk, defense=3,
            speed=_speed(0.55, 1),
            detect_range=10, attack_range=48, attack_cooldown=900,
            color=(80, 230, 80),
            radius=24
        )
        self.is_boss = True
        self.split_used = False

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return
        dist = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL, EnemyState.ALERT):
            self.state = EnemyState.CHASE

        if self.hp < self.max_hp * 0.5 and not self.split_used:
            self.split_used = True
            for angle in [0, math.pi * 2 / 3, math.pi * 4 / 3]:
                sx = self.x + math.cos(angle) * 50
                sy = self.y + math.sin(angle) * 50
                self.pending_spawns.append((sx, sy, Slime))

        self.state_timer -= dt

        if self.state == EnemyState.CHASE:
            if dist <= self.attack_range_val:
                self.state = EnemyState.ATTACK
            else:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
        elif self.state == EnemyState.ATTACK:
            if dist > self.attack_range_val + 30:
                self.state = EnemyState.CHASE
            elif self.attack_timer <= 0:
                self._perform_attack(player)
                self.attack_timer = self.attack_cooldown


class SkeletonGeneral(Enemy):
    """F2 Boss — 骷髅将军：近战+周期性召唤骷髅射手"""
    def __init__(self, x, y):
        s = _floor_scale(2)
        hp = int(260 * s)
        atk = int(18 * s)
        super().__init__(
            x, y, "骷髅将军",
            max_hp=hp, attack=atk, defense=4,
            speed=_speed(0.80, 2),
            detect_range=11, attack_range=50, attack_cooldown=700,
            color=(200, 70, 70),
            radius=22
        )
        self.is_boss = True
        self.summon_cooldown = 3000
        self.summon_timer = 1000
        self.phase2 = False

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return
        dist = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL, EnemyState.ALERT):
            self.state = EnemyState.CHASE

        if self.hp < self.max_hp * 0.5 and not self.phase2:
            self.phase2 = True
            self.speed = _speed(0.95, 2)
            self.summon_cooldown = 2000

        self.state_timer -= dt
        if self.summon_timer > 0:
            self.summon_timer -= dt * 1000

        if self.summon_timer <= 0:
            self.summon_timer = self.summon_cooldown
            for _ in range(2):
                angle = random.uniform(0, math.pi * 2)
                sx = self.x + math.cos(angle) * 80
                sy = self.y + math.sin(angle) * 80
                self.pending_spawns.append((sx, sy, SkeletonArcher))

        if self.state == EnemyState.CHASE:
            if dist <= self.attack_range_val:
                self.state = EnemyState.ATTACK
            else:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
        elif self.state == EnemyState.ATTACK:
            if dist > self.attack_range_val + 30:
                self.state = EnemyState.CHASE
            elif self.attack_timer <= 0:
                self._perform_attack(player)
                self.attack_timer = self.attack_cooldown


class ShadowLord(Enemy):
    """F3 Boss — 暗影领主：极快+瞬移到玩家背后+多段连击"""
    def __init__(self, x, y):
        s = _floor_scale(3)
        hp = int(260 * s)
        atk = int(22 * s)
        super().__init__(
            x, y, "暗影领主",
            max_hp=hp, attack=atk, defense=4,
            speed=_speed(1.35, 3),
            detect_range=12, attack_range=38, attack_cooldown=500,
            color=(130, 40, 210),
            radius=18
        )
        self.is_boss = True
        self.teleport_cooldown = 3500
        self.teleport_timer = 2500
        self.combo_hits = 0
        self.phase2 = False

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return
        dist = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL, EnemyState.ALERT):
            self.state = EnemyState.CHASE

        if self.hp < self.max_hp * 0.5 and not self.phase2:
            self.phase2 = True
            self.speed = _speed(1.6, 3)
            self.attack_cooldown = 350
            self.teleport_cooldown = 2500

        self.state_timer -= dt
        if self.teleport_timer > 0:
            self.teleport_timer -= dt * 1000

        # 瞬移到玩家背后
        if self.teleport_timer <= 0 and dist > 30:
            self.teleport_timer = self.teleport_cooldown
            self.x = player.x - math.cos(player.facing_angle) * 70
            self.y = player.y - math.sin(player.facing_angle) * 70
            self._clamp_to_walkable(dungeon_tiles)
            self.combo_hits = 3

        if self.state == EnemyState.CHASE:
            if dist <= self.attack_range_val:
                self.state = EnemyState.ATTACK
            else:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
        elif self.state == EnemyState.ATTACK:
            if dist > self.attack_range_val + 25:
                self.state = EnemyState.CHASE
            elif self.attack_timer <= 0:
                self._perform_attack(player)
                if self.combo_hits > 0:
                    self.combo_hits -= 1
                    self.attack_timer = 120
                else:
                    self.attack_timer = self.attack_cooldown


class FlameDemon(Enemy):
    """F4 Boss — 炎魔：远程弹幕+环形散射，保持距离风筝"""
    def __init__(self, x, y):
        s = _floor_scale(4)
        hp = int(420 * s)
        atk = int(25 * s)
        super().__init__(
            x, y, "炎魔",
            max_hp=hp, attack=atk, defense=5,
            speed=_speed(0.55, 4),
            detect_range=13, attack_range=250, attack_cooldown=1600,
            color=(255, 100, 30),
            radius=24
        )
        self.is_boss = True
        self.preferred_distance = 180
        self.burst_cooldown = 2000
        self.burst_timer = 1200
        self.phase2 = False

    def _update_ai(self, dt, player, dungeon_tiles):
        if not player or not player.is_alive:
            return
        dist = self._distance_to(player.x, player.y)

        if self.state in (EnemyState.IDLE, EnemyState.PATROL, EnemyState.ALERT):
            self.state = EnemyState.CHASE

        if self.hp < self.max_hp * 0.5 and not self.phase2:
            self.phase2 = True
            self.burst_cooldown = 1200
            self.attack_cooldown = 1000

        self.state_timer -= dt
        if self.burst_timer > 0:
            self.burst_timer -= dt * 1000

        # 环形散射弹幕
        if self.burst_timer <= 0:
            self.burst_timer = self.burst_cooldown
            count = 8 if self.phase2 else 6
            base_angle = math.atan2(player.y - self.y, player.x - self.x)
            for i in range(count):
                angle = base_angle + (2 * math.pi / count) * i
                tx = self.x + math.cos(angle) * 200
                ty = self.y + math.sin(angle) * 200
                p = Projectile(self.x, self.y, tx, ty, self.attack, speed=220)
                self.pending_projectiles.append(p)

        # 保持距离风筝
        if self.state == EnemyState.CHASE:
            if dist > self.preferred_distance + 40:
                self._move_toward(player.x, player.y, self.speed, dt, dungeon_tiles)
            elif dist < self.preferred_distance - 40:
                self._move_toward(player.x, player.y, -self.speed * 0.7, dt, dungeon_tiles)
            if dist <= self.attack_range_val:
                self.state = EnemyState.ATTACK

        elif self.state == EnemyState.ATTACK:
            if dist < self.preferred_distance - 50:
                self._move_toward(player.x, player.y, -self.speed * 0.7, dt, dungeon_tiles)
            if dist > self.attack_range_val + 40:
                self.state = EnemyState.CHASE
            # 单发瞄准弹幕
            if self.attack_timer <= 0:
                p = Projectile(self.x, self.y, player.x, player.y, self.attack, speed=280)
                self.pending_projectiles.append(p)
                self.attack_timer = self.attack_cooldown
