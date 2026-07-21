"""UI 组件：血条、面板、小地图"""
import pygame
import settings
from src.tile import Tile


def draw_health_bar(surface, x, y, w, h, current, maximum, color=None):
    """绘制血条"""
    if color is None:
        color = settings.COLOR_HP_BAR
    bg_rect = (x, y, w, h)
    pygame.draw.rect(surface, settings.COLOR_HP_BG, bg_rect)
    pygame.draw.rect(surface, (60, 60, 70), bg_rect, 1)
    if maximum > 0:
        fill_w = int(w * current / maximum)
        pygame.draw.rect(surface, color, (x, y, fill_w, h))


def draw_panel(surface, rect, alpha=200):
    """绘制半透明面板"""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((*settings.COLOR_UI_PANEL[:3], alpha))
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, settings.COLOR_UI_BORDER, rect, 2)


def draw_minimap(surface, x, y, size, dungeon_tiles, fov_data, player_pos, stairs_pos):
    """绘制小地图"""
    ts = settings.TILE_SIZE
    tile_w = max(2, size // len(dungeon_tiles[0]))
    tile_h = max(2, size // len(dungeon_tiles))

    map_surf = pygame.Surface((len(dungeon_tiles[0]) * tile_w, len(dungeon_tiles) * tile_h))
    map_surf.fill((0, 0, 0))

    for my in range(len(dungeon_tiles)):
        for mx in range(len(dungeon_tiles[0])):
            fov_state = fov_data[my][mx]
            if fov_state == 0:  # 未探索
                continue

            tile = dungeon_tiles[my][mx]
            if fov_state == 1:  # 已探索
                if tile in (Tile.FLOOR, Tile.CORRIDOR):
                    color = (40, 40, 50)
                elif tile == Tile.WALL:
                    color = (25, 25, 35)
                else:
                    continue
            else:  # 可见
                if tile in (Tile.FLOOR, Tile.CORRIDOR):
                    color = (100, 100, 120)
                elif tile == Tile.WALL:
                    color = (60, 60, 75)
                else:
                    continue

            pygame.draw.rect(map_surf, color, (mx * tile_w, my * tile_h, tile_w, tile_h))

    # 玩家位置
    ppx = int(player_pos[0] / ts * tile_w)
    ppy = int(player_pos[1] / ts * tile_h)
    pygame.draw.circle(map_surf, (100, 180, 255), (ppx, ppy), max(2, tile_w))

    # 楼梯位置
    if stairs_pos:
        sx = int(stairs_pos[0] / ts * tile_w)
        sy = int(stairs_pos[1] / ts * tile_h)
        pygame.draw.rect(map_surf, settings.COLOR_STAIRS,
                         (sx - tile_w // 2, sy - tile_h // 2, tile_w, tile_h))

    surface.blit(map_surf, (x, y))
    pygame.draw.rect(surface, settings.COLOR_UI_BORDER,
                     (x, y, len(dungeon_tiles[0]) * tile_w, len(dungeon_tiles) * tile_h), 1)