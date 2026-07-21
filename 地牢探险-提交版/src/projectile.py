"""弹幕系统：远程敌人发射的可见弹幕"""
import math
import settings


class Projectile:
    def __init__(self, x, y, target_x, target_y, damage, speed=None):
        self.x = x
        self.y = y
        self.damage = damage
        self.radius = settings.PROJECTILE_RADIUS
        self.lifetime = settings.PROJECTILE_LIFETIME
        self.is_alive = True
        self.color = settings.COLOR_PROJECTILE
        self.is_crit = False
        self.lifesteal = 0.0
        self.from_player = False

        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        spd = speed or settings.PROJECTILE_SPEED
        self.vx = dx / dist * spd
        self.vy = dy / dist * spd

    def update(self, dt, dungeon_tiles):
        """更新弹幕位置，超时或碰墙则销毁"""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_alive = False
            return

        self.x += self.vx * dt
        self.y += self.vy * dt

        # 碰墙销毁
        from src.tile import Tile
        ts = settings.TILE_SIZE
        tx = int(self.x // ts)
        ty = int(self.y // ts)
        if 0 <= ty < len(dungeon_tiles) and 0 <= tx < len(dungeon_tiles[0]):
            if dungeon_tiles[ty][tx] == Tile.WALL:
                self.is_alive = False

    def collides_player(self, player):
        """检测是否命中玩家"""
        if not player.is_alive:
            return False
        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.sqrt(dx * dx + dy * dy)
        return dist < self.radius + player.radius
