from settings import ENEMY_BULLET_SPEED
from sprites.boss import Boss, BossMinion
from sprites.bullet import Bullet


class BossManager:
    def __init__(self):
        self.boss = None
        self.shoot_timer = 0
        self.minion_timer = 0

    def spawn(self) -> None:
        self.boss = Boss()
        self.shoot_timer = 0
        self.minion_timer = 0

    def update(self, dt: int, player_center_x: int, enemy_bullets, minions) -> None:
        if not self.boss:
            return

        self.boss.update(dt)

        self.shoot_timer += dt
        shoot_interval = 600 if self.boss.phase == 2 else 800
        if self.shoot_timer >= shoot_interval:
            self.shoot_timer = 0
            if self.boss.phase == 2:
                for ox in (-10, 0, 10):
                    enemy_bullets.add(
                        Bullet(player_center_x + ox, self.boss.rect.bottom,
                               ENEMY_BULLET_SPEED + 2, is_player=False, vx=ox * 0.3)
                    )
            else:
                x, y = self.boss.try_shoot()
                enemy_bullets.add(
                    Bullet(x, y, ENEMY_BULLET_SPEED + 2, is_player=False)
                )

        self.minion_timer += dt
        if self.boss.phase == 2 and self.minion_timer >= 3000:
            self.minion_timer = 0
            minions.add(BossMinion(self.boss.rect.centerx, self.boss.rect.bottom))

    def reset(self) -> None:
        self.boss = None
        self.shoot_timer = 0
        self.minion_timer = 0
