import sys
import math
import random
import pygame
from enum import Enum, auto
import settings
from src.dungeon import generate_dungeon
from src.tile import Tile
from src.player import Player
from src.camera import Camera
from src.combat import melee_attack, generate_loot
from src.enemy import Slime, SkeletonArcher, ShadowAssassin, BossDemon, \
    GiantSlimeKing, SkeletonGeneral, ShadowLord, FlameDemon
from src.fov import FOVMap, VISIBLE, EXPLORED, UNEXPLORED
from src.ui import draw_health_bar, draw_minimap


class GameState(Enum):
    MENU = auto()
    HOW_TO_PLAY = auto()
    PLAYING = auto()
    PAUSE = auto()
    GAMEOVER = auto()
    VICTORY = auto()


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            pygame.RESIZABLE
        )
        pygame.display.set_caption(settings.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.font_default = pygame.font.Font(settings.FONT_PATH, settings.FONT_DEFAULT_SIZE)
        self.font_large = pygame.font.Font(settings.FONT_PATH, settings.FONT_LARGE_SIZE)
        self.font_small = pygame.font.Font(settings.FONT_PATH, settings.FONT_SMALL_SIZE)

        self.player = None
        self.dungeon_tiles = None
        self.dungeon_rooms = None
        self.camera = None
        self.enemies = []
        self.items_on_ground = []
        self.projectiles = []
        self.damage_numbers = []  # 浮动伤害数字
        self.fov = None
        self.current_floor = 0
        self.kill_count = 0
        self.backpack_open = False
        self.floor_transition_timer = 0
        self.boss_defeated = False
        self.attack_flash_timer = 0

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.VIDEORESIZE:
                w = max(settings.MIN_SCREEN_WIDTH, event.w)
                h = max(settings.MIN_SCREEN_HEIGHT, event.h)
                self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                settings.SCREEN_WIDTH = w
                settings.SCREEN_HEIGHT = h
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSE
                    elif self.state == GameState.PAUSE:
                        self.state = GameState.PLAYING
                self._on_key_down(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._on_mouse_down(event)

    def _update(self, dt):
        if self.floor_transition_timer > 0:
            self.floor_transition_timer -= dt
        if self.attack_flash_timer > 0:
            self.attack_flash_timer -= dt * 1000

        # 伤害数字更新
        for dm in self.damage_numbers[:]:
            dm["life"] -= dt
            dm["y"] += dm["vy"] * dt
            if dm["life"] <= 0:
                self.damage_numbers.remove(dm)

        if self.state == GameState.PLAYING and self.player:
            prev_hp = self.player.hp
            self.player.update(dt, self.dungeon_tiles, self.enemies, self.items_on_ground)
            self.camera.update(self.player.x, self.player.y)
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.camera.screen_to_world(mx, my)
            self.player.facing_angle = math.atan2(wy - self.player.y, wx - self.player.x)
            self.fov.update(self.player.x, self.player.y, self.dungeon_tiles)
            for enemy in self.enemies:
                enemy.update(dt, self.player, self.dungeon_tiles)
                for p in enemy.pending_projectiles:
                    self.projectiles.append(p)
                enemy.pending_projectiles.clear()
            # 检测敌人近战伤害
            if self.player.hp < prev_hp:
                dmg_taken = prev_hp - self.player.hp
                self.damage_numbers.append(_make_dmg(str(dmg_taken), self.player.x, self.player.y - 20, (255, 80, 80), "normal"))
            # 处理敌人召唤（Boss技能）
            for enemy in self.enemies[:]:
                for sx, sy, EnemyClass in enemy.pending_spawns:
                    self.enemies.append(EnemyClass(sx, sy, self.current_floor))
                enemy.pending_spawns.clear()
            # 更新弹幕
            self._update_projectiles(dt)
            self._process_enemy_deaths()
            if not self.player.is_alive:
                self.state = GameState.GAMEOVER

    def _render(self):
        self.screen.fill(settings.COLOR_BG)

        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.HOW_TO_PLAY:
            self._render_how_to_play()
        elif self.state == GameState.PLAYING:
            self._render_playing()
        elif self.state == GameState.PAUSE:
            self._render_playing()
            self._render_pause_overlay()
        elif self.state == GameState.GAMEOVER:
            self._render_gameover()
        elif self.state == GameState.VICTORY:
            self._render_victory()

        pygame.display.flip()

    # ---- 各状态渲染 ----

    def _render_menu(self):
        title = self.font_large.render("地牢探险", True, settings.COLOR_UI_TEXT)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 160))
        self.screen.blit(title, title_rect)

        start_rect = pygame.Rect(0, 0, 300, 50)
        start_rect.center = (settings.SCREEN_WIDTH // 2, 300)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], start_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, start_rect, 2)
        start_text = self.font_default.render("开始游戏", True, settings.COLOR_UI_TEXT)
        self.screen.blit(start_text, start_text.get_rect(center=start_rect.center))

        help_rect = pygame.Rect(0, 0, 300, 50)
        help_rect.center = (settings.SCREEN_WIDTH // 2, 370)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], help_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, help_rect, 2)
        help_text = self.font_default.render("玩法说明", True, settings.COLOR_UI_TEXT)
        self.screen.blit(help_text, help_text.get_rect(center=help_rect.center))

        quit_rect = pygame.Rect(0, 0, 300, 50)
        quit_rect.center = (settings.SCREEN_WIDTH // 2, 440)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], quit_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, quit_rect, 2)
        quit_text = self.font_default.render("退出", True, settings.COLOR_UI_TEXT)
        self.screen.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

        self._menu_buttons = {
            "start": start_rect,
            "help": help_rect,
            "quit": quit_rect,
        }

    def _render_how_to_play(self):
        title = self.font_large.render("玩法说明", True, settings.COLOR_UI_TEXT)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)

        instructions = [
            ("W A S D", "移动"),
            ("鼠标移动", "瞄准方向"),
            ("鼠标左键", "攻击（近战）"),
            ("E", "打开背包 / 拾取物品"),
            ("F", "进入下一层（在楼梯上）"),
            ("ESC", "暂停 / 继续"),
        ]

        y = 160
        for key, desc in instructions:
            key_text = self.font_default.render(key, True, settings.COLOR_UI_HIGHLIGHT)
            desc_text = self.font_default.render(f"  -  {desc}", True, settings.COLOR_UI_TEXT)
            self.screen.blit(key_text, (settings.SCREEN_WIDTH // 2 - 220, y))
            self.screen.blit(desc_text, (settings.SCREEN_WIDTH // 2 + 10, y))
            y += 42

        back_rect = pygame.Rect(0, 0, 260, 50)
        back_rect.center = (settings.SCREEN_WIDTH // 2, 500)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], back_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, back_rect, 2)
        back_text = self.font_default.render("返回主菜单", True, settings.COLOR_UI_TEXT)
        self.screen.blit(back_text, back_text.get_rect(center=back_rect.center))
        self._how_to_play_back_btn = back_rect

    def _render_playing(self):
        if self.dungeon_tiles:
            self._render_dungeon()
            if self.player:
                # 渲染楼梯
                if self.stairs_pos and self.boss_defeated and self.fov.is_explored(self.stairs_pos[0], self.stairs_pos[1]):
                    self._render_stairs()
                # 渲染地面物品
                for item_data in self.items_on_ground:
                    self._render_item_on_ground(item_data)
                # 渲染敌人
                for enemy in self.enemies:
                    self._render_enemy(enemy)
                # 渲染弹幕
                for projectile in self.projectiles:
                    self._render_projectile(projectile)
                # 玩家最上层
                self._render_player()
                # 渲染攻击特效
                self._render_attack_effect()
                # 渲染伤害数字
                self._render_damage_numbers()
                # HUD
                self._render_hud()
                # 小地图
                self._render_minimap()
                # 楼层提示
                self._render_floor_notice()
                # 背包（覆盖层）
                if self.backpack_open:
                    self._render_backpack()
        else:
            info = self.font_default.render(
                "Dungeon generation coming soon...", True, settings.COLOR_UI_TEXT
            )
            self.screen.blit(info, (50, 300))

    def _render_dungeon(self):
        """渲染地牢地图（带视口偏移）"""
        ts = settings.TILE_SIZE
        scr_w, scr_h = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        cam_x = int(self.camera.x)
        cam_y = int(self.camera.y)

        start_x = max(0, cam_x // ts)
        start_y = max(0, cam_y // ts)
        end_x = min(len(self.dungeon_tiles[0]), start_x + scr_w // ts + 2)
        end_y = min(len(self.dungeon_tiles), start_y + scr_h // ts + 2)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.dungeon_tiles[y][x]
                screen_x = x * ts - cam_x
                screen_y = y * ts - cam_y

                fov_state = self.fov.data[y][x]

                if fov_state == UNEXPLORED:
                    continue  # 完全不可见，跳过（背景色）
                elif fov_state == EXPLORED:
                    if tile == Tile.FLOOR or tile == Tile.CORRIDOR:
                        color = settings.COLOR_FLOOR_EXPLORED
                    elif tile == Tile.WALL:
                        color = settings.COLOR_WALL_EXPLORED
                    else:
                        continue
                else:  # VISIBLE
                    if tile == Tile.FLOOR:
                        color = settings.COLOR_FLOOR
                    elif tile == Tile.CORRIDOR:
                        color = settings.COLOR_CORRIDOR
                    elif tile == Tile.WALL:
                        color = settings.COLOR_WALL
                    else:
                        continue

                pygame.draw.rect(self.screen, color, (screen_x, screen_y, ts, ts))

    def _render_player(self):
        """渲染玩家（立体球形 + 朝向指示线）"""
        sx, sy = self.camera.world_to_screen(self.player.x, self.player.y)
        if self.player.invincible_timer > 0 and int(self.player.invincible_timer // 80) % 2 == 0:
            return

        r = self.player.radius
        # 球体光照：从暗到亮多层同心圆叠加
        base_color = settings.COLOR_PLAYER
        for i in range(r, 0, -1):
            t = i / r           # 0(中心) ~ 1(边缘)
            alpha = 60 + int(140 * (1 - t))  # 中心亮，边缘暗
            shade = int(255 * t * 0.6)       # 边缘颜色加深
            color = (
                max(0, base_color[0] - shade),
                max(0, base_color[1] - shade),
                max(0, base_color[2] - shade),
                alpha,
            )
            # 用带 alpha 的小 surface 叠加
            layer = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(layer, color, (r, r), i)
            self.screen.blit(layer, (int(sx) - r, int(sy) - r))

        # 高光点（左上偏移）
        hl_x = int(sx) - r // 3
        hl_y = int(sy) - r // 3
        hl_r = max(2, r // 4)
        pygame.draw.circle(self.screen, (255, 255, 255, 180), (hl_x, hl_y), hl_r)

        # 朝向指示线
        angle = self.player.facing_angle
        ex = sx + math.cos(angle) * (self.player.radius + 8)
        ey = sy + math.sin(angle) * (self.player.radius + 8)
        pygame.draw.line(self.screen, (200, 200, 255), (sx, sy), (ex, ey), 2)

    def _render_enemy(self, enemy):
        """渲染敌人（圆形 + 血条 + 受伤闪烁），仅视野内可见"""
        if not self.fov.is_visible(enemy.x, enemy.y):
            return
        sx, sy = self.camera.world_to_screen(enemy.x, enemy.y)
        r = enemy.radius
        # 受伤闪烁
        color = (255, 255, 255) if enemy.hit_flash > 0 else enemy.color
        # Boss 更大并有特殊效果
        if getattr(enemy, 'is_boss', False):
            # 光环
            glow_r = r + 6 + int(math.sin(pygame.time.get_ticks() * 0.005) * 3)
            glow_r_color = tuple(max(0, c - 100) for c in enemy.color) + (120,)
            pygame.draw.circle(self.screen, glow_r_color[:3],
                             (int(sx), int(sy)), glow_r, 2)

        pygame.draw.circle(self.screen, color, (int(sx), int(sy)), r)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(sx), int(sy)), r, 2)

        # 血条（受伤时或Boss始终显示）
        if enemy.hp < enemy.max_hp or getattr(enemy, 'is_boss', False):
            bar_w = r * 2.5
            bar_h = 4
            bar_y = sy - r - 8
            hp_ratio = enemy.hp / enemy.max_hp
            pygame.draw.rect(self.screen, settings.COLOR_HP_BG,
                             (sx - bar_w / 2, bar_y, bar_w, bar_h))
            pygame.draw.rect(self.screen, settings.COLOR_HP_BAR,
                             (sx - bar_w / 2, bar_y, bar_w * hp_ratio, bar_h))

    def _render_item_on_ground(self, item_data):
        """渲染地面物品（大菱形 + 靠近显示信息面板）"""
        from src.items import Weapon, Armor, Potion
        item, wx, wy = item_data
        if not self.fov.is_visible(wx, wy):
            return
        sx, sy = self.camera.world_to_screen(wx, wy)

        r = 14  # 近似视觉半径（用于信息面板定位）
        if isinstance(item, Weapon):
            color = getattr(item, 'color', settings.COLOR_ITEM_WEAPON)
            # 斜45°细长矩形（剑/斧形状）
            half_w = 3
            half_h = 12
            angle = math.pi / 4
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            pts = [
                (sx + (-half_w * cos_a - half_h * sin_a), sy + (-half_w * sin_a + half_h * cos_a)),
                (sx + ( half_w * cos_a - half_h * sin_a), sy + ( half_w * sin_a + half_h * cos_a)),
                (sx + ( half_w * cos_a + half_h * sin_a), sy + ( half_w * sin_a - half_h * cos_a)),
                (sx + (-half_w * cos_a + half_h * sin_a), sy + (-half_w * sin_a - half_h * cos_a)),
            ]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), pts, 2)
            # 护手/十字格
            guard_pts = [
                (sx + (-6 * cos_a - 4 * sin_a), sy + (-6 * sin_a + 4 * cos_a)),
                (sx + ( 6 * cos_a - 4 * sin_a), sy + ( 6 * sin_a + 4 * cos_a)),
                (sx + ( 6 * cos_a + 4 * sin_a), sy + ( 6 * sin_a - 4 * cos_a)),
                (sx + (-6 * cos_a + 4 * sin_a), sy + (-6 * sin_a - 4 * cos_a)),
            ]
            hl_w = tuple(min(255, c + 40) for c in color)
            pygame.draw.polygon(self.screen, hl_w, guard_pts)
        elif isinstance(item, Armor):
            color = getattr(item, 'color', settings.COLOR_ITEM_ARMOR)
            # 防弹衣六边形
            pts = [
                (sx, sy - 12),
                (sx + 14, sy - 6),
                (sx + 10, sy + 4),
                (sx, sy + 12),
                (sx - 10, sy + 4),
                (sx - 14, sy - 6),
            ]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), pts, 2)
            # 肩部高光线
            hl = tuple(min(255, c + 60) for c in color)
            pygame.draw.line(self.screen, hl, (sx, sy - 10), (sx + 10, sy - 4), 2)
            pygame.draw.line(self.screen, hl, (sx, sy - 10), (sx - 10, sy - 4), 2)
        elif isinstance(item, Potion):
            color = settings.COLOR_ITEM_POTION
            # 玻璃瓶：圆形瓶身 + 瓶颈 + 瓶塞
            pygame.draw.circle(self.screen, color, (int(sx), int(sy + 4)), 8)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(sx), int(sy + 4)), 8, 1)
            neck_rect = (sx - 3, sy - 10, 6, 10)
            pygame.draw.rect(self.screen, color, neck_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), neck_rect, 1)
            cap_rect = (sx - 5, sy - 14, 10, 5)
            darker = tuple(max(0, c - 40) for c in color)
            pygame.draw.rect(self.screen, darker, cap_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), cap_rect, 1)
            # 高光
            pygame.draw.circle(self.screen, (255, 255, 255, 150), (int(sx - 2), int(sy + 2)), 2)
        else:
            color = (200, 200, 200)
            # 默认菱形
            r2 = 12
            pts = [(sx, sy - r2), (sx + r2, sy), (sx, sy + r2), (sx - r2, sy)]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), pts, 2)

        # 靠近时显示属性面板
        dist = math.sqrt((self.player.x - wx) ** 2 + (self.player.y - wy) ** 2)
        if dist < 70:
            lines = []
            if isinstance(item, Weapon):
                lines.append(item.name)
                lines.append(f"攻击 +{item.attack_bonus}")
                if item.weapon_type == "ranged":
                    lines.append(f"远程 冷却{int(item.cooldown or 0)}ms")
                else:
                    lines.append(f"近战 范围{item.range_bonus} 宽度{item.width}")
                if item.crit_rate > 0:
                    lines.append(f"暴击率 {int(item.crit_rate*100)}% 暴击伤害 {item.crit_damage:.1f}x")
                if item.lifesteal > 0:
                    lines.append(f"吸血 {int(item.lifesteal*100)}%")
            elif isinstance(item, Armor):
                lines.append(item.name)
                lines.append(f"减伤 {int(item.reduction*100)}%")
            elif isinstance(item, Potion):
                lines.append(item.name)
                lines.append(item.description)

            if lines:
                font = pygame.font.Font(settings.FONT_PATH, 16)
                line_h = 18
                pad = 6
                max_w = max(font.size(l)[0] for l in lines)
                panel_w = max_w + pad * 2
                panel_h = len(lines) * line_h + pad * 2
                px = sx - panel_w // 2
                py = sy - r - panel_h - 6

                panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                panel.fill((20, 20, 30, 210))
                self.screen.blit(panel, (px, py))
                pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, (px, py, panel_w, panel_h), 1)

                for i, ln in enumerate(lines):
                    t = font.render(ln, True, settings.COLOR_UI_TEXT)
                    self.screen.blit(t, (px + pad, py + pad + i * line_h))

                # 拾取提示
                pickup_hint = self.font_small.render("按 E 拾取", True, settings.COLOR_UI_HIGHLIGHT)
                self.screen.blit(pickup_hint, (sx - pickup_hint.get_width() // 2, py - 22))

    def _render_stairs(self):
        """渲染楼梯（金色方块）"""
        sx, sy = self.camera.world_to_screen(self.stairs_pos[0], self.stairs_pos[1])
        ts = settings.TILE_SIZE // 2
        rect = (sx - ts // 2, sy - ts // 2, ts, ts)
        pygame.draw.rect(self.screen, settings.COLOR_STAIRS, rect)
        pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
        # 提示文字
        if self.fov.is_visible(self.stairs_pos[0], self.stairs_pos[1]):
            dist = math.sqrt(
                (self.player.x - self.stairs_pos[0]) ** 2 +
                (self.player.y - self.stairs_pos[1]) ** 2
            )
            if dist < 50:
                hint = self.font_small.render("按 F 进入下一层", True, settings.COLOR_UI_HIGHLIGHT)
                self.screen.blit(hint, (sx - hint.get_width() // 2, sy - 24))

    def _render_attack_effect(self):
        if self.player.weapon and self.player.weapon.weapon_type == "ranged":
            return

        atk_range = settings.PLAYER_ATTACK_RANGE
        atk_width = settings.PLAYER_ATTACK_WIDTH
        if self.player.weapon:
            atk_range = self.player.weapon.range_bonus or settings.PLAYER_ATTACK_RANGE
            atk_width = self.player.weapon.width or settings.PLAYER_ATTACK_WIDTH

        half_angle = math.atan2(atk_width / 2, atk_range) * 1.3
        sx, sy = self.camera.world_to_screen(self.player.x, self.player.y)
        disp_range = atk_range + 25

        if self.attack_flash_timer > 0:
            alpha = int(self.attack_flash_timer / 150 * 120)
            self._draw_sector(sx, sy, disp_range, self.player.facing_angle, half_angle,
                              (255, 255, 150, alpha))

        if self.player.attack_timer <= 0:
            self._draw_sector(sx, sy, disp_range, self.player.facing_angle, half_angle,
                              (255, 255, 100, 30))

        # 武器挥砍动画
        if self.player.swing_timer > 0:
            progress = 1 - self.player.swing_timer / self.player.swing_duration
            swing_angle = self.player.facing_angle - half_angle + 2 * half_angle * progress
            # 武器颜色
            wcolor = self.player.weapon.color if self.player.weapon else (180, 180, 200)
            # 画武器线条（粗线表示武器）
            end_x = sx + math.cos(swing_angle) * disp_range
            end_y = sy + math.sin(swing_angle) * disp_range
            # 武器主体粗线
            pygame.draw.line(self.screen, wcolor, (sx, sy), (end_x, end_y), 5)
            # 高光细线
            hl = tuple(min(255, c + 80) for c in wcolor)
            pygame.draw.line(self.screen, hl, (sx, sy), (end_x, end_y), 2)

    def _draw_sector(self, cx, cy, radius, facing, half_angle, color):
        """绘制扇形"""
        import pygame.gfxdraw
        points = [(cx, cy)]
        steps = 12
        for i in range(steps + 1):
            a = facing - half_angle + (2 * half_angle) * i / steps
            px = cx + math.cos(a) * radius
            py = cy + math.sin(a) * radius
            points.append((px, py))

        if len(color) == 4:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            local_pts = [(p[0] - cx + radius, p[1] - cy + radius) for p in points]
            if len(local_pts) >= 3:
                pygame.draw.polygon(surf, color, local_pts)
            self.screen.blit(surf, (cx - radius, cy - radius))
        else:
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, color, points, 1)

    def _render_damage_numbers(self):
        """渲染浮动伤害数字"""
        for dm in self.damage_numbers:
            sx, sy = self.camera.world_to_screen(dm["x"], dm["y"])
            alpha = int(255 * min(1.0, dm["life"] / 0.3))
            font = pygame.font.Font(settings.FONT_PATH, dm["size"])
            surf = font.render(dm["text"], True, dm["color"])
            surf.set_alpha(alpha)
            self.screen.blit(surf, (sx - surf.get_width() // 2, sy))

    def _render_hud(self):
        """渲染HUD：血条、层数、击杀数、装备信息"""
        margin = 14
        y = margin

        bar_w, bar_h = 200, 16
        hp_text = self.font_small.render(
            f"生命: {self.player.hp}/{self.player.max_hp}", True, settings.COLOR_UI_TEXT
        )
        self.screen.blit(hp_text, (margin, y))
        y += 18
        draw_health_bar(self.screen, margin, y, bar_w, bar_h,
                        self.player.hp, self.player.max_hp)
        y += bar_h + 8

        floor_text = self.font_small.render(
            f"层数: {self.current_floor} / 5", True, settings.COLOR_UI_TEXT
        )
        self.screen.blit(floor_text, (margin, y))
        y += 20

        kill_text = self.font_small.render(
            f"击杀: {self.kill_count}", True, settings.COLOR_UI_TEXT
        )
        self.screen.blit(kill_text, (margin, y))
        y += 20

        # Boss 状态
        if self.boss_defeated:
            boss_text = self.font_small.render("Boss: 已击败", True, (100, 255, 100))
        else:
            boss_text = self.font_small.render("Boss: 未击败", True, (255, 100, 100))
        self.screen.blit(boss_text, (margin, y))
        y += 20

        if self.player.weapon:
            wpn_text = self.font_small.render(
                f"武器: {self.player.weapon.name}", True, settings.COLOR_ITEM_WEAPON
            )
            self.screen.blit(wpn_text, (margin, y))
            y += 18
        if self.player.armor:
            arm_text = self.font_small.render(
                f"防具: {self.player.armor.name} (减伤{int(self.player.armor.reduction*100)}%)",
                True, settings.COLOR_ITEM_ARMOR
            )
            self.screen.blit(arm_text, (margin, y))

        tip = "E:拾取/背包  F:下一层  ESC:暂停"
        tip_text = self.font_small.render(tip, True, settings.COLOR_UI_TEXT)
        self.screen.blit(tip_text, (margin, settings.SCREEN_HEIGHT - 22))

    def _render_minimap(self):
        """渲染小地图（右上角）"""
        mm_size = 150
        mm_x = settings.SCREEN_WIDTH - mm_size - 10
        mm_y = 10
        draw_minimap(self.screen, mm_x, mm_y, mm_size,
                     self.dungeon_tiles, self.fov.data,
                     (self.player.x, self.player.y),
                     self.stairs_pos if self.boss_defeated else None)

    def _render_floor_notice(self):
        if self.floor_transition_timer > 0:
            alpha = min(255, int(self.floor_transition_timer * 255))
            text = self.font_large.render(
                f"第 {self.current_floor} 层", True, settings.COLOR_UI_HIGHLIGHT
            )
            text.set_alpha(alpha)
            self.screen.blit(text, text.get_rect(center=(
                settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2 - 40
            )))

    def _render_backpack(self):
        from src.items import Weapon, Armor, Potion

        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("背包", True, settings.COLOR_UI_TEXT)
        self.screen.blit(title, title.get_rect(
            center=(settings.SCREEN_WIDTH // 2, 60)
        ))

        eq_x = settings.SCREEN_WIDTH // 2 - 240
        eq_y = 130
        eq_text = self.font_default.render("已装备:", True, settings.COLOR_UI_HIGHLIGHT)
        self.screen.blit(eq_text, (eq_x, eq_y))

        weapon_text = self.font_small.render(
            f"武器: {self.player.weapon.name if self.player.weapon else '无'} "
            f"(攻击 +{self.player.weapon.attack_bonus if self.player.weapon else 0})",
            True, settings.COLOR_ITEM_WEAPON
        )
        self.screen.blit(weapon_text, (eq_x, eq_y + 35))

        armor_text = self.font_small.render(
            f"防具: {self.player.armor.name if self.player.armor else '无'} "
            f"(减伤 {int(self.player.armor.reduction*100) if self.player.armor else 0}%)",
            True, settings.COLOR_ITEM_ARMOR
        )
        self.screen.blit(armor_text, (eq_x, eq_y + 60))

        inv_y = eq_y + 100
        inv_text = self.font_default.render("物品:", True, settings.COLOR_UI_HIGHLIGHT)
        self.screen.blit(inv_text, (eq_x, inv_y))

        if not self.player.backpack:
            empty = self.font_small.render("（空）", True, (150, 150, 160))
            self.screen.blit(empty, (eq_x, inv_y + 35))
        else:
            for i, item in enumerate(self.player.backpack):
                if isinstance(item, Weapon):
                    color = settings.COLOR_ITEM_WEAPON
                elif isinstance(item, Armor):
                    color = settings.COLOR_ITEM_ARMOR
                else:
                    color = settings.COLOR_ITEM_POTION
                item_text = self.font_small.render(
                    f"{i+1}. {item.name} - {item.description}", True, color
                )
                self.screen.blit(item_text, (eq_x, inv_y + 30 + i * 22))

        close_text = self.font_small.render(
            "按 E 关闭", True, settings.COLOR_UI_TEXT
        )
        self.screen.blit(close_text, close_text.get_rect(
            center=(settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 40)
        ))

    def _render_pause_overlay(self):
        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        text = self.font_large.render("已暂停", True, settings.COLOR_UI_TEXT)
        self.screen.blit(
            text, text.get_rect(center=(settings.SCREEN_WIDTH // 2, 280))
        )
        hint = self.font_small.render(
            "按 ESC 继续", True, settings.COLOR_UI_TEXT
        )
        self.screen.blit(
            hint, hint.get_rect(center=(settings.SCREEN_WIDTH // 2, 340))
        )

    def _render_gameover(self):
        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        text = self.font_large.render("游戏结束", True, (220, 50, 50))
        self.screen.blit(
            text, text.get_rect(center=(settings.SCREEN_WIDTH // 2, 180))
        )
        stats = [
            f"到达层数: {self.current_floor}",
            f"击杀敌人: {self.kill_count}",
        ]
        y = 260
        for s in stats:
            st = self.font_default.render(s, True, settings.COLOR_UI_TEXT)
            self.screen.blit(st, st.get_rect(center=(settings.SCREEN_WIDTH // 2, y)))
            y += 36

        menu_rect = pygame.Rect(0, 0, 300, 50)
        menu_rect.center = (settings.SCREEN_WIDTH // 2, 380)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], menu_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, menu_rect, 2)
        menu_text = self.font_default.render("返回主菜单", True, settings.COLOR_UI_TEXT)
        self.screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))
        self._gameover_menu_btn = menu_rect

    def _render_victory(self):
        overlay = pygame.Surface(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        text = self.font_large.render("胜利！", True, settings.COLOR_UI_HIGHLIGHT)
        self.screen.blit(
            text, text.get_rect(center=(settings.SCREEN_WIDTH // 2, 180))
        )
        stats = [
            "全部楼层通关！",
            f"击杀敌人: {self.kill_count}",
        ]
        y = 260
        for s in stats:
            st = self.font_default.render(s, True, settings.COLOR_UI_TEXT)
            self.screen.blit(st, st.get_rect(center=(settings.SCREEN_WIDTH // 2, y)))
            y += 36

        menu_rect = pygame.Rect(0, 0, 300, 50)
        menu_rect.center = (settings.SCREEN_WIDTH // 2, 380)
        pygame.draw.rect(self.screen, settings.COLOR_UI_PANEL[:3], menu_rect)
        pygame.draw.rect(self.screen, settings.COLOR_UI_BORDER, menu_rect, 2)
        menu_text = self.font_default.render("返回主菜单", True, settings.COLOR_UI_TEXT)
        self.screen.blit(menu_text, menu_text.get_rect(center=menu_rect.center))
        self._victory_menu_btn = menu_rect

    def _generate_floor(self):
        """生成一个新楼层（地牢 + 玩家 + 敌人 + 楼梯）"""
        self.dungeon_tiles, self.dungeon_rooms = generate_dungeon(
            settings.MAP_WIDTH, settings.MAP_HEIGHT,
            settings.BSP_MIN_ROOM_SIZE, settings.BSP_MAX_DEPTH
        )
        self.enemies = []
        self.items_on_ground = []
        self.projectiles = []
        self.boss_defeated = False

        if self.player is None:
            start_room = self.dungeon_rooms[0]
            start_px = start_room.center[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2
            start_py = start_room.center[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2
            self.player = Player(start_px, start_py)
        else:
            # 从已有玩家：放置到第一个房间
            start_room = self.dungeon_rooms[0]
            self.player.x = start_room.center[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2
            self.player.y = start_room.center[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2

        if self.camera is None:
            self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.camera.update(self.player.x, self.player.y)

        self.fov = FOVMap(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.fov.update(self.player.x, self.player.y, self.dungeon_tiles)

        self._spawn_enemies()
        self._place_stairs()

    def _place_stairs(self):
        """在远离玩家出生点的房间放置楼梯"""
        if len(self.dungeon_rooms) < 2:
            self.stairs_pos = None
            return
        # 使用最后一个房间（离出生点最远）
        stair_room = self.dungeon_rooms[-1]
        self.stairs_pos = (
            stair_room.center[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2,
            stair_room.center[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2,
        )

    def _start_game(self):
        """初始化并开始一局新游戏"""
        self.state = GameState.PLAYING
        self.current_floor = 1
        self.kill_count = 0
        self.player = None
        self.camera = None
        self.stairs_pos = None
        self.boss_defeated = False
        self._generate_floor()

    def _spawn_enemies(self):
        """在当前地牢生成敌人（每层必有一个Boss在最终房间）"""
        self.enemies = []
        # 怪物数量每层 +50% ×3倍：F1=30, F2=45, F3=66, F4=99, F5=150
        enemy_count = int(10 * (1.5 ** (self.current_floor - 1))) * 3
        spawn_rooms = self.dungeon_rooms[1:]  # 不在玩家出生房间生成

        # Boss: 始终在最后一个房间（楼梯所在房间）
        if len(self.dungeon_rooms) > 1:
            boss_room = self.dungeon_rooms[-1]
            bpx = boss_room.center[0] * settings.TILE_SIZE + settings.TILE_SIZE // 2
            bpy = boss_room.center[1] * settings.TILE_SIZE + settings.TILE_SIZE // 2
            boss = self._create_boss(bpx, bpy)
            self.enemies.append(boss)

        # 普通敌人：避开Boss房间
        non_boss_rooms = spawn_rooms[:-1] if len(spawn_rooms) > 1 else []
        for i in range(min(enemy_count, len(non_boss_rooms) * 2)):
            room = random.choice(non_boss_rooms)
            px = (room.x + random.randint(1, room.w - 1)) * settings.TILE_SIZE + settings.TILE_SIZE // 2
            py = (room.y + random.randint(1, room.h - 1)) * settings.TILE_SIZE + settings.TILE_SIZE // 2
            self._spawn_random_enemy(px, py)

    def _create_boss(self, x, y):
        """根据当前楼层创建对应的Boss"""
        boss_map = {
            1: GiantSlimeKing,
            2: SkeletonGeneral,
            3: ShadowLord,
            4: FlameDemon,
            5: BossDemon,
        }
        BossClass = boss_map.get(self.current_floor, BossDemon)
        return BossClass(x, y)

    def _spawn_random_enemy(self, px, py):
        """随机生成一种敌人"""
        r = random.random()
        if r < 0.35:
            self.enemies.append(Slime(px, py, self.current_floor))
        elif r < 0.65:
            self.enemies.append(SkeletonArcher(px, py, self.current_floor))
        else:
            self.enemies.append(ShadowAssassin(px, py, self.current_floor))

    def _process_enemy_deaths(self):
        """处理敌人死亡，增加击杀数，生成掉落。Boss死亡时激活楼梯"""
        for enemy in self.enemies[:]:
            if enemy.is_dead:
                self.kill_count += 1
                if getattr(enemy, 'is_boss', False):
                    self.boss_defeated = True
                loot = generate_loot(enemy.x, enemy.y, self.current_floor)
                if loot:
                    self.items_on_ground.append(loot)
                self.enemies.remove(enemy)

    def _on_key_down(self, event):
        if self.state == GameState.PLAYING and self.player:
            if event.key == pygame.K_e:
                # 尝试拾取，没物品则切换背包
                if not self._pickup_nearby_items():
                    self.backpack_open = not self.backpack_open
            elif event.key == pygame.K_f:
                self._try_go_next_floor()

    def _on_mouse_down(self, event):
        if event.button == 1:  # 左键
            if self.state == GameState.MENU and hasattr(self, "_menu_buttons"):
                if self._menu_buttons["start"].collidepoint(event.pos):
                    self._start_game()
                elif self._menu_buttons["help"].collidepoint(event.pos):
                    self.state = GameState.HOW_TO_PLAY
                elif self._menu_buttons["quit"].collidepoint(event.pos):
                    self.running = False
            elif self.state == GameState.HOW_TO_PLAY and hasattr(self, "_how_to_play_back_btn"):
                if self._how_to_play_back_btn.collidepoint(event.pos):
                    self.state = GameState.MENU
            elif self.state == GameState.GAMEOVER and hasattr(self, "_gameover_menu_btn"):
                if self._gameover_menu_btn.collidepoint(event.pos):
                    self.state = GameState.MENU
            elif self.state == GameState.VICTORY and hasattr(self, "_victory_menu_btn"):
                if self._victory_menu_btn.collidepoint(event.pos):
                    self.state = GameState.MENU
            elif self.state == GameState.PLAYING and self.player and self.player.attack_timer <= 0:
                self._player_attack()

    def _player_attack(self):
        """玩家执行攻击（近战或远程）"""
        if self.player.weapon and self.player.weapon.weapon_type == "ranged":
            self._ranged_attack()
        else:
            self._melee_attack()

    def _melee_attack(self):
        self.player.attack_timer = settings.PLAYER_ATTACK_COOLDOWN
        self.attack_flash_timer = 150
        self.player.swing_timer = self.player.swing_duration
        atk_range = settings.PLAYER_ATTACK_RANGE
        atk_width = settings.PLAYER_ATTACK_WIDTH
        crit_rate = 0.0
        crit_dmg = 1.5
        lifesteal = 0.0

        if self.player.weapon:
            atk_range = self.player.weapon.range_bonus or settings.PLAYER_ATTACK_RANGE
            atk_width = self.player.weapon.width or settings.PLAYER_ATTACK_WIDTH
            crit_rate = self.player.weapon.crit_rate
            crit_dmg = self.player.weapon.crit_damage
            lifesteal = self.player.weapon.lifesteal

        dmg = self.player.attack
        if self.player.weapon:
            dmg += self.player.weapon.attack_bonus

        hits = melee_attack(self.player, self.enemies, atk_range, atk_width, dmg,
                            crit_rate, crit_dmg, lifesteal)
        for enemy, actual_dmg, kbx, kby, is_crit, heal in hits:
            enemy.knockback_vx += kbx
            enemy.knockback_vy += kby
            # 伤害数字
            color = (255, 180, 50) if is_crit else (255, 255, 100)
            size = "large" if is_crit else "normal"
            text = str(actual_dmg) + ("!" if is_crit else "")
            self.damage_numbers.append(_make_dmg(text, enemy.x, enemy.y - 20, color, size))
            # 吸血
            if heal > 0:
                self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                self.damage_numbers.append(_make_dmg(f"+{heal}", self.player.x, self.player.y - 20, (100, 255, 100), "small"))

    def _ranged_attack(self):
        """远程武器：发射弹幕"""
        from src.projectile import Projectile
        wpn = self.player.weapon
        cd = wpn.cooldown or 500
        self.player.attack_timer = cd

        mx, my = pygame.mouse.get_pos()
        wx, wy = self.camera.screen_to_world(mx, my)

        dmg = self.player.attack + wpn.attack_bonus
        is_crit = random.random() < wpn.crit_rate
        if is_crit:
            dmg = int(dmg * wpn.crit_damage)

        p = Projectile(self.player.x, self.player.y, wx, wy, dmg, speed=wpn.projectile_speed)
        p.color = wpn.color  # 覆盖默认弹幕颜色为武器颜色
        p.is_crit = is_crit
        p.lifesteal = wpn.lifesteal
        p.from_player = True
        self.projectiles.append(p)

    def _update_projectiles(self, dt):
        for p in self.projectiles[:]:
            p.update(dt, self.dungeon_tiles)
            if not p.is_alive:
                self.projectiles.remove(p)
                continue

            if p.from_player:
                # 玩家弹幕命中敌人
                for enemy in self.enemies:
                    if enemy.is_alive and _circle_hit(p.x, p.y, p.radius, enemy.x, enemy.y, enemy.radius):
                        actual = enemy.take_damage(p.damage)
                        color = (255, 180, 50) if p.is_crit else (255, 255, 100)
                        size = "large" if p.is_crit else "normal"
                        text = str(actual) + ("!" if p.is_crit else "")
                        self.damage_numbers.append(_make_dmg(text, enemy.x, enemy.y - 20, color, size))
                        if p.lifesteal > 0:
                            heal = int(actual * p.lifesteal)
                            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
                            self.damage_numbers.append(_make_dmg(f"+{heal}", self.player.x, self.player.y - 20, (100, 255, 100), "small"))
                        p.is_alive = False
                        self.projectiles.remove(p)
                        break
            else:
                # 敌人弹幕命中玩家
                if p.collides_player(self.player):
                    actual = self.player.take_damage(p.damage)
                    self.damage_numbers.append(_make_dmg(str(actual), self.player.x, self.player.y - 20, (255, 80, 80), "normal"))
                    p.is_alive = False
                    self.projectiles.remove(p)

    def _render_projectile(self, p):
        """渲染弹幕（橙色圆 + 尾迹），仅视野内可见"""
        if not self.fov.is_visible(p.x, p.y):
            return
        sx, sy = self.camera.world_to_screen(p.x, p.y)
        # 尾迹
        trail = pygame.Surface((p.radius * 3, p.radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(trail, (255, 100, 30, 60), (p.radius * 1.5, p.radius * 1.5), p.radius * 1.5)
        self.screen.blit(trail, (int(sx) - p.radius * 1.5, int(sy) - p.radius * 1.5))
        # 主体
        pygame.draw.circle(self.screen, p.color, (int(sx), int(sy)), p.radius)
        highlight = tuple(min(255, c + 80) for c in p.color[:3])
        pygame.draw.circle(self.screen, highlight, (int(sx), int(sy)), p.radius - 1)

    def _pickup_nearby_items(self):
        """拾取玩家附近的物品，返回是否拾取了物品"""
        pickup_range = 50
        picked = False
        for item_data in self.items_on_ground[:]:
            item, ix, iy = item_data
            dist = math.sqrt((self.player.x - ix) ** 2 + (self.player.y - iy) ** 2)
            if dist <= pickup_range:
                self._apply_item(item)
                self.items_on_ground.remove(item_data)
                picked = True
        return picked

    def _apply_item(self, item):
        """使用/装备物品"""
        from src.items import Weapon, Armor, Potion
        if isinstance(item, Potion):
            self.player.hp = min(self.player.max_hp, self.player.hp + item.heal_amount)
        elif isinstance(item, Weapon):
            self.player.weapon = item
            self.player.backpack = [it for it in self.player.backpack
                                    if not isinstance(it, Weapon)] + [item]
        elif isinstance(item, Armor):
            self.player.armor = item
            self.player.damage_reduction = item.reduction
            self.player.backpack = [it for it in self.player.backpack
                                    if not isinstance(it, Armor)] + [item]

    def _try_go_next_floor(self):
        """尝试进入下一层（Boss必须已击败）"""
        if self.stairs_pos is None or not self.boss_defeated:
            return
        dist = math.sqrt(
            (self.player.x - self.stairs_pos[0]) ** 2 +
            (self.player.y - self.stairs_pos[1]) ** 2
        )
        if dist > 50:
            return

        self.current_floor += 1
        if self.current_floor > 5:
            self.state = GameState.VICTORY
            return

        self.player.max_hp = int(settings.PLAYER_MAX_HP * (1.25 ** (self.current_floor - 1)))
        self.player.hp = self.player.max_hp

        self._generate_floor()
        self.floor_transition_timer = 2.0
        self.backpack_open = False


# ---- 辅助函数 ----

def _make_dmg(text, x, y, color, size="normal"):
    """创建一个浮动伤害数字"""
    base = 18 if size == "small" else (24 if size == "normal" else 32)
    return {"text": text, "x": x, "y": y, "vy": -70, "color": color, "life": 0.8, "size": base}


def _circle_hit(x1, y1, r1, x2, y2, r2):
    dx = x1 - x2
    dy = y1 - y2
    return (dx * dx + dy * dy) < (r1 + r2) ** 2
