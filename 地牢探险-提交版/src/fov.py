"""视野系统：战争迷雾 + 记忆地图"""
import math
import settings
from src.tile import Tile


# FOV 状态常量
UNEXPLORED = 0
EXPLORED = 1
VISIBLE = 2


class FOVMap:
    def __init__(self, map_width, map_height):
        self.width = map_width
        self.height = map_height
        # 0=未探索, 1=已探索但不可见, 2=当前可见
        self.data = [[UNEXPLORED for _ in range(map_width)] for _ in range(map_height)]

    def update(self, px, py, dungeon_tiles):
        """从玩家位置更新视野"""
        ts = settings.TILE_SIZE
        ptile_x = int(px // ts)
        ptile_y = int(py // ts)

        # 先将所有 VISIBLE 降为 EXPLORED
        for y in range(self.height):
            for x in range(self.width):
                if self.data[y][x] == VISIBLE:
                    self.data[y][x] = EXPLORED

        radius = settings.FOV_RADIUS

        # 对视野范围内的每个格子进行射线检测
        for ty in range(ptile_y - radius, ptile_y + radius + 1):
            for tx in range(ptile_x - radius, ptile_x + radius + 1):
                if 0 <= tx < self.width and 0 <= ty < self.height:
                    # 检查距离
                    dx = tx - ptile_x
                    dy = ty - ptile_y
                    if dx * dx + dy * dy <= radius * radius:
                        if self._line_of_sight(ptile_x, ptile_y, tx, ty, dungeon_tiles):
                            self.data[ty][tx] = VISIBLE

    def _line_of_sight(self, x0, y0, x1, y1, dungeon_tiles):
        """Bresenham 视线检测：从(x0,y0)到(x1,y1)是否被墙壁阻挡"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        cx, cy = x0, y0
        while True:
            # 检查当前格子是否阻挡视线
            if 0 <= cy < len(dungeon_tiles) and 0 <= cx < len(dungeon_tiles[0]):
                if dungeon_tiles[cy][cx] == Tile.WALL:
                    # 如果是目标格子本身是墙，可以看到
                    if cx == x1 and cy == y1:
                        return True
                    return False

            if cx == x1 and cy == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

        return True

    def is_visible(self, world_x, world_y):
        """检查世界坐标位置是否可见"""
        ts = settings.TILE_SIZE
        tx = int(world_x // ts)
        ty = int(world_y // ts)
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.data[ty][tx] == VISIBLE
        return False

    def is_explored(self, world_x, world_y):
        """检查世界坐标位置是否已探索"""
        ts = settings.TILE_SIZE
        tx = int(world_x // ts)
        ty = int(world_y // ts)
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.data[ty][tx] >= EXPLORED
        return False
