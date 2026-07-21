"""玩家类：移动、属性、攻击状态"""
import pygame
import math
import settings
from src.tile import Tile


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = settings.PLAYER_SIZE

        # 属性
        self.max_hp = settings.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.attack = settings.PLAYER_ATTACK
        self.damage_reduction = 0.0  # 护甲减伤率 0~1
        self.speed = settings.PLAYER_SPEED

        # 攻击
        self.attack_cooldown = 0
        self.attack_timer = 0

        # 受击
        self.invincible_timer = 0

        # 朝向（弧度）
        self.facing_angle = 0

        # 装备
        self.weapon = None
        self.armor = None
        self.backpack = []

        # 挥砍动画
        self.swing_timer = 0      # 动画剩余时间 ms
        self.swing_duration = 200  # 动画总时长 ms

    def update(self, dt, dungeon_tiles, enemies, items_on_ground):
        """每帧更新"""
        # 冷却计时
        if self.attack_timer > 0:
            self.attack_timer -= dt * 1000
        if self.invincible_timer > 0:
            self.invincible_timer -= dt * 1000
        if self.swing_timer > 0:
            self.swing_timer -= dt * 1000

        self._handle_movement(dt, dungeon_tiles)
        self._update_facing()

    def _handle_movement(self, dt, dungeon_tiles):
        """处理键盘移动 + 碰撞检测"""
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if dx == 0 and dy == 0:
            return

        # 归一化对角线移动
        length = math.sqrt(dx * dx + dy * dy)
        dx /= length
        dy /= length

        move_speed = self.speed * dt

        # 分别检测 X 和 Y 轴碰撞（允许沿墙滑动）
        self.x += dx * move_speed
        if self._collides_with_wall(dungeon_tiles):
            self.x -= dx * move_speed

        self.y += dy * move_speed
        if self._collides_with_wall(dungeon_tiles):
            self.y -= dy * move_speed

    def _collides_with_wall(self, dungeon_tiles):
        """检测玩家圆形是否与墙壁碰撞"""
        ts = settings.TILE_SIZE
        # 检测玩家半径范围内的四个角
        check_offsets = [
            (self.radius, 0), (-self.radius, 0),
            (0, self.radius), (0, -self.radius),
            (self.radius * 0.7, self.radius * 0.7),
            (-self.radius * 0.7, self.radius * 0.7),
            (self.radius * 0.7, -self.radius * 0.7),
            (-self.radius * 0.7, -self.radius * 0.7),
        ]
        for ox, oy in check_offsets:
            tx = int((self.x + ox) // ts)
            ty = int((self.y + oy) // ts)
            if 0 <= ty < len(dungeon_tiles) and 0 <= tx < len(dungeon_tiles[0]):
                if dungeon_tiles[ty][tx] == Tile.WALL:
                    return True
        return False

    def _update_facing(self):
        """更新朝向为鼠标方向"""
        mx, my = pygame.mouse.get_pos()
        # 鼠标坐标需要加上相机偏移来转换为世界坐标
        # 这里先记录屏幕坐标，由 game 层传入偏移
        self.facing_angle = 0  # 默认，game 层会在 update 后调整

    @property
    def rect(self):
        """返回 pygame Rect（用于粗略碰撞）"""
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )

    def take_damage(self, amount):
        """受到伤害（护甲百分比减伤），返回实际伤害值"""
        if self.invincible_timer > 0:
            return 0
        actual = max(1, int(amount * (1 - self.damage_reduction)))
        self.hp -= actual
        self.invincible_timer = settings.PLAYER_INVINCIBLE_TIME
        return actual

    def get_attack_range_rect(self):
        """获取攻击判定矩形（世界坐标）"""
        angle = self.facing_angle
        half_w = settings.PLAYER_ATTACK_WIDTH / 2
        center_x = self.x + math.cos(angle) * settings.PLAYER_ATTACK_RANGE
        center_y = self.y + math.sin(angle) * settings.PLAYER_ATTACK_RANGE

        # 旋转矩形简化为沿朝向的矩形
        # 这里返回 (center_x, center_y, half_w, half_h) 用于后续判定
        return (center_x, center_y, half_w, settings.PLAYER_ATTACK_RANGE / 2, angle)

    @property
    def is_alive(self):
        return self.hp > 0
