"""BSP 地牢生成算法"""
import random
from dataclasses import dataclass
from src.tile import Tile
import settings


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)


class BSPNode:
    """BSP 树节点"""
    def __init__(self, x, y, w, h):
        self.rect = Rect(x, y, w, h)
        self.left = None
        self.right = None
        self.room = None

    @property
    def is_leaf(self):
        return self.left is None and self.right is None


def _split_node(node, depth, max_depth):
    """递归分割 BSP 节点"""
    if depth >= max_depth:
        return

    # 决定分割方向：房间太窄则只能横向切，太扁则只能纵向切
    if node.rect.w > node.rect.h and node.rect.w / node.rect.h >= 1.25:
        split_h = False  # 纵向切
    elif node.rect.h > node.rect.w and node.rect.h / node.rect.w >= 1.25:
        split_h = True   # 横向切
    else:
        split_h = random.choice([True, False])

    min_size = settings.BSP_MIN_ROOM_SIZE + 2  # 房间+墙壁
    if split_h:
        # 横向分割
        max_split = node.rect.h - min_size
        if max_split < min_size:
            return
        split = random.randint(min_size, max_split)
        node.left = BSPNode(node.rect.x, node.rect.y, node.rect.w, split)
        node.right = BSPNode(node.rect.x, node.rect.y + split, node.rect.w, node.rect.h - split)
    else:
        # 纵向分割
        max_split = node.rect.w - min_size
        if max_split < min_size:
            return
        split = random.randint(min_size, max_split)
        node.left = BSPNode(node.rect.x, node.rect.y, split, node.rect.h)
        node.right = BSPNode(node.rect.x + split, node.rect.y, node.rect.w - split, node.rect.h)

    _split_node(node.left, depth + 1, max_depth)
    _split_node(node.right, depth + 1, max_depth)


def _create_rooms(node, min_room_size):
    """在叶子节点中创建随机房间"""
    if not node.is_leaf:
        _create_rooms(node.left, min_room_size)
        _create_rooms(node.right, min_room_size)
        return

    # 在节点区域内随机缩小边界生成房间
    room_w = random.randint(min_room_size, max(min_room_size, node.rect.w - 2))
    room_h = random.randint(min_room_size, max(min_room_size, node.rect.h - 2))
    room_x = node.rect.x + random.randint(1, max(1, node.rect.w - room_w - 1))
    room_y = node.rect.y + random.randint(1, max(1, node.rect.h - room_h - 1))

    node.room = Rect(room_x, room_y, room_w, room_h)


def _connect_siblings(node, tiles):
    """用走廊连接兄弟节点的房间"""
    if node.is_leaf:
        return

    _connect_siblings(node.left, tiles)
    _connect_siblings(node.right, tiles)

    # 找到左右子树中各一个随机房间
    left_room = _get_room(node.left)
    right_room = _get_room(node.right)
    if left_room is None or right_room is None:
        return

    _carve_corridor(left_room.center, right_room.center, tiles)


def _get_room(node):
    """从子树中随机获取一个房间"""
    if node.is_leaf:
        return node.room
    # 随机选择一个子节点
    children = [n for n in (node.left, node.right) if n is not None]
    return _get_room(random.choice(children)) if children else None


def _carve_corridor(p1, p2, tiles):
    """L 形走廊：先水平再垂直，或先垂直再水平。走廊宽度 3 格"""
    x1, y1 = p1
    x2, y2 = p2
    corridor_width = 3
    half = corridor_width // 2

    if random.random() < 0.5:
        # 先水平后垂直
        for dy in range(-half, half + 1):
            _carve_h(tiles, x1, x2, y1 + dy)
            _carve_v(tiles, y1, y2, x2 + dy)
    else:
        # 先垂直后水平
        for dy in range(-half, half + 1):
            _carve_v(tiles, y1, y2, x1 + dy)
            _carve_h(tiles, x1, x2, y2 + dy)


def _carve_h(tiles, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] == Tile.VOID or tiles[y][x] == Tile.WALL:
                tiles[y][x] = Tile.CORRIDOR


def _carve_v(tiles, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            if tiles[y][x] == Tile.VOID or tiles[y][x] == Tile.WALL:
                tiles[y][x] = Tile.CORRIDOR


def _collect_rooms(node, rooms):
    """收集所有房间"""
    if node.is_leaf and node.room is not None:
        rooms.append(node.room)
    if node.left:
        _collect_rooms(node.left, rooms)
    if node.right:
        _collect_rooms(node.right, rooms)


def generate_dungeon(map_width, map_height, min_room_size, max_depth):
    """生成一个完整的随机地牢

    返回 (tiles, rooms) — tiles 是 2D 列表，rooms 是房间列表
    """
    # 初始化全 VOID
    tiles = [[Tile.VOID for _ in range(map_width)] for _ in range(map_height)]

    # 创建 BSP 树
    root = BSPNode(1, 1, map_width - 2, map_height - 2)

    # 递归分割
    _split_node(root, 0, max_depth)

    # 创建房间
    _create_rooms(root, min_room_size)

    # 将房间写入地图
    for node in _iter_nodes(root):
        if node.room is not None:
            r = node.room
            for y in range(r.y, r.y + r.h):
                for x in range(r.x, r.x + r.w):
                    if 0 <= y < map_height and 0 <= x < map_width:
                        tiles[y][x] = Tile.FLOOR

    # 生成走廊
    _connect_siblings(root, tiles)

    # 收集所有房间
    rooms = []
    _collect_rooms(root, rooms)

    # 生成墙壁：把与地板/走廊相邻的 VOID 变成 WALL
    _generate_walls(tiles, map_width, map_height)

    return tiles, rooms


def _iter_nodes(node):
    """迭代所有节点"""
    yield node
    if node.left:
        yield from _iter_nodes(node.left)
    if node.right:
        yield from _iter_nodes(node.right)


def _generate_walls(tiles, map_width, map_height):
    """在所有可行走区域周围生成墙壁"""
    walkable = {Tile.FLOOR, Tile.CORRIDOR}
    for y in range(map_height):
        for x in range(map_width):
            if tiles[y][x] in walkable:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < map_height and 0 <= nx < map_width:
                            if tiles[ny][nx] == Tile.VOID:
                                tiles[ny][nx] = Tile.WALL
