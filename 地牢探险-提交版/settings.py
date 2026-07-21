# 游戏常量配置

# 窗口
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
MIN_SCREEN_WIDTH = 640
MIN_SCREEN_HEIGHT = 480
FPS = 60
TITLE = "地牢探险"

# 字体
import os as _os
import sys as _sys
# 优先使用打包后的本地字体，其次系统字体
if getattr(_sys, 'frozen', False):
    _base = _sys._MEIPASS
else:
    _base = _os.path.dirname(_os.path.abspath(__file__))
_LOCAL_FONT = _os.path.join(_base, "assets", "simhei.ttf")
_SYSTEM_FONT = "C:/Windows/Fonts/simhei.ttf"
FONT_PATH = _LOCAL_FONT if _os.path.exists(_LOCAL_FONT) else _SYSTEM_FONT
FONT_DEFAULT_SIZE = 32
FONT_LARGE_SIZE = 56
FONT_SMALL_SIZE = 20

# 地图（瓦片大小）
TILE_SIZE = 40
MAP_WIDTH = 60   # 瓦片数
MAP_HEIGHT = 50

# 颜色
COLOR_BG = (20, 20, 30)
COLOR_FLOOR = (50, 50, 60)
COLOR_WALL = (30, 30, 40)
COLOR_CORRIDOR = (60, 60, 70)
COLOR_FLOOR_EXPLORED = (55, 55, 75)
COLOR_WALL_EXPLORED = (40, 40, 55)
COLOR_PLAYER = (70, 130, 255)
COLOR_ENEMY_SLIME = (100, 220, 100)
COLOR_ENEMY_ARCHER = (220, 100, 100)
COLOR_BOSS = (220, 50, 50)
COLOR_ITEM_WEAPON = (255, 200, 50)
COLOR_ITEM_ARMOR = (180, 180, 180)
COLOR_ITEM_POTION = (255, 100, 255)
COLOR_STAIRS = (255, 215, 0)
COLOR_ATTACK = (255, 255, 100)
COLOR_PROJECTILE = (255, 120, 50)
COLOR_HP_BAR = (220, 50, 50)
COLOR_HP_BG = (60, 20, 20)
COLOR_FOG = (0, 0, 0)
COLOR_FOG_EXPLORED = (30, 30, 40, 180)
COLOR_UI_PANEL = (40, 40, 50, 200)
COLOR_UI_BORDER = (100, 100, 120)
COLOR_UI_TEXT = (230, 230, 240)
COLOR_UI_HIGHLIGHT = (255, 255, 100)

# 玩家
PLAYER_SPEED = 440          # 像素/秒
PLAYER_MAX_HP = 100
PLAYER_ATTACK = 15
PLAYER_DEFENSE = 2
PLAYER_ATTACK_RANGE = 55   # 攻击判定距离
PLAYER_ATTACK_WIDTH = 50    # 攻击判定宽度
PLAYER_ATTACK_COOLDOWN = 350  # 毫秒
PLAYER_INVINCIBLE_TIME = 500   # 受伤无敌帧（毫秒）
PLAYER_SIZE = 14            # 渲染半径

# 视野
FOV_RADIUS = 12             # 瓦片数

# 敌人通用
ENEMY_DETECT_RANGE = 8      # 发现玩家的距离（瓦片）
ENEMY_FORGET_RANGE = 12     # 丢失玩家的距离（瓦片）

# 弹幕
PROJECTILE_SPEED = 250      # 像素/秒
PROJECTILE_LIFETIME = 3.0   # 秒
PROJECTILE_RADIUS = 5

# 地牢生成
BSP_MIN_ROOM_SIZE = 7       # 最小房间尺寸（瓦片）
BSP_MAX_DEPTH = 5           # BSP递归深度
