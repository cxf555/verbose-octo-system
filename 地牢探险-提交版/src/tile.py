from enum import IntEnum


class Tile(IntEnum):
    """地图瓦片类型"""
    VOID = 0       # 地图外
    FLOOR = 1      # 房间地板
    WALL = 2       # 墙壁
    CORRIDOR = 3   # 走廊地板
