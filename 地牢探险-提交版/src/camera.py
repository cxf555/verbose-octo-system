"""相机：视口跟随玩家"""
import settings


class Camera:
    def __init__(self, map_width, map_height):
        self.x = 0
        self.y = 0
        self.map_pixel_w = map_width * settings.TILE_SIZE
        self.map_pixel_h = map_height * settings.TILE_SIZE

    def update(self, target_x, target_y):
        """跟随目标，保持目标在屏幕中央，不超出地图边界"""
        scr_w = settings.SCREEN_WIDTH
        scr_h = settings.SCREEN_HEIGHT

        self.x = target_x - scr_w // 2
        self.y = target_y - scr_h // 2

        # 限制不超出地图
        self.x = max(0, min(self.x, self.map_pixel_w - scr_w))
        self.y = max(0, min(self.y, self.map_pixel_h - scr_h))

        # 如果地图小于屏幕，居中
        if self.map_pixel_w < scr_w:
            self.x = (self.map_pixel_w - scr_w) // 2
        if self.map_pixel_h < scr_h:
            self.y = (self.map_pixel_h - scr_h) // 2

    def world_to_screen(self, wx, wy):
        """世界坐标转屏幕坐标"""
        return (wx - self.x, wy - self.y)

    def screen_to_world(self, sx, sy):
        """屏幕坐标转世界坐标"""
        return (sx + self.x, sy + self.y)
