import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state ="normal"
        self.hyper_life = 0

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
        self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.hyper_life -= 1
            self.image = pg.transform.laplacian(self.image)
            if self.hyper_life < 0:
                self.state = "normal"        
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"
    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()
class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: int = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0 # angle0を追加する
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam:
    """
    複数方向にビームを生成するクラス
    """
    def __init__(self, bird: Bird, num: int):
        self.bird = bird  # ビームを発射するこうかとん
        self.num = num  # 生成するビーム数
    def gen_beams(self) -> list[Beam]:
        """
        -50度から+50度の範囲で複数のBeamを生成する
        """
        beam_lst = [] # 生成したビームを格納するリスト
        step = 100 // (self.num - 1) # ビーム同士の角度差

        for angle in range(-50, 51, step):
            beam_lst.append(Beam(self.bird, angle)) # 指定角度のビームを生成してリストに追加

        return beam_lst


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

class Life:#追加
    """
    こうかとんの残機（ライフ）に関するクラス
    """
    def __init__(self, num: int):
        self.num = num
        self.image = pg.Surface((40, 40), pg.SRCALPHA)
        points = [(16*math.sin(t/100)**3 +20, -(13*math.cos(t/100)-5*math.cos(2*t/100)-2*math.cos(3*t/100)-math.cos(4*t/100)) +20) for t in range(0, 628)]
        pg.draw.polygon(self.image, (255, 0, 0), points)

    def update(self, screen: pg.Surface):
        # 画像の幅と高さの半分を計算
        half_w = self.image.get_width() // 2
        half_h = self.image.get_height() // 2

        for i in range(self.num):
            center_x = WIDTH - 50 - (i * 50)
            center_y = HEIGHT - 50
            screen.blit(self.image, (center_x - half_w, center_y - half_h))

        

  
class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 9999
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Emp:
    def __init__(self,emys,bombs):
        self.image = pg.Surface((WIDTH,HEIGHT))
        self.image.set_alpha(128)
        self.image.fill((255,255,0))


        for emy in emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)
        
        for bomb in bombs:
            bomb.speed /= 2
            bomb.state = "inactive" 

    def update(self,screen):
        screen.blit(self.image,(0,0))
        pg.display.update()
        time.sleep(0.05)
        return



class Shield(pg.sprite.Sprite):
    """
    こうかとんの前に防御壁を出すクラス
    """
    def __init__(self, bird: Bird, life: int = 400):
        super().__init__() # Spriteクラスのイニシャライザを呼び出す
        self.life = life # 防御壁の残り表示時間

        # 防御壁の画像（青い矩形）を生成
        self.image = pg.Surface((20, bird.rect.height * 2), pg.SRCALPHA)

        # 青色の矩形を描画 
        pg.draw.rect(
            self.image,
            (0, 0, 255),
            (0, 0, 20, bird.rect.height * 2)
        )

        # こうかとんの向きに合わせて回転
        vx, vy = bird.dire
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotate(self.image, angle)

        self.rect = self.image.get_rect() # 防御壁のRectを取得

        # こうかとんの前に配置
        self.rect.center = (
            bird.rect.centerx + vx * bird.rect.width,
            bird.rect.centery + vy * bird.rect.height
        )

    def update(self):
        """
        防御壁の残り時間を更新し，時間切れになったら削除する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()
            
            
class Gravity(pg.sprite.Sprite):
    """
    スコアを消費して画面全体を覆う重力場を発生させるクラス
    """
    def __init__(self, life):
        """
        重力場Surfaceを生成する
        引数 life：重力場の持続時間（フレーム数）
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0, 0, 0),(0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        
        self.life = life
        
        
    def update(self):
        """
        重力場の残り時間を1減らし，
        持続時間が終了したら削除する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    life = Life(3)  # 残機3追加
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()


    shields = pg.sprite.Group() # shieldsグループを追加
    gravities = pg.sprite.Group()


    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0

            # スペースキー押下でビームを発射
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if key_lst[pg.K_LSHIFT]:  # 左Shiftキーを押しながらスペースキーで弾幕を発射
                    beams.add(*NeoBeam(bird, 5).gen_beams())  # 5方向のビームを追加
                else:
                    beams.add(Beam(bird))  # 通常のビームを発射

            # eキー押下でEMPを発動
            if event.type == pg.KEYDOWN and event.key == pg.K_e and score.value > 20:
                score.value -= 20
                emp = Emp(emys, bombs)
                emp.update(screen)

            # zキー押下で防御壁を生成
            if event.type == pg.KEYDOWN and event.key == pg.K_z:
                if score.value > 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50  # スコアを50消費

            # xキー押下で重力場を発動
            if event.type == pg.KEYDOWN and event.key == pg.K_x and score.value >= 200:
                gravities.add(Gravity(400))
                score.value -= 200  # スコアを200消費
                
            
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value > 100:
                bird.state = "hyper" 
                bird.hyper_life =500
                score.value-=100
                
        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        # 防御壁と衝突した爆弾を削除
        for shield, bomb_lst in pg.sprite.groupcollide(shields, bombs, False, True).items():
            for bomb in bomb_lst:
                exps.add(Explosion(bomb, 50))    

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
        # EMPで無効化された爆弾
            if bomb.state == "inactive":
                continue

            # 無敵状態ではダメージを受けず，爆弾を破壊
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))
                score.value += 1
                continue

            # 通常時は残機を減らす
            life.num -= 1

            if life.num > 0:
                continue

            bird.change_img(8, screen)
            score.update(screen)
            life.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        # 重力場と衝突した敵機を撃破
        for emy in pg.sprite.groupcollide(emys, gravities, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        # 重力場と衝突した爆弾を消去
        for bomb in pg.sprite.groupcollide(bombs, gravities, True, False).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1
        
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state == "inactive":
                continue
            else:
            
                if bird.state == "hyper":
                    exps.add(Explosion(bomb, 50))
                    score.value += 1
                else: 
                    bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return

        screen.blit(bg_img, [0, 0])
        # 重力場の更新・描画 先頭に置かないとすべて黒くなるため注意
        gravities.update()
        gravities.draw(screen)
        
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        life.update(screen)#追加
        shields.update() # 防御壁の状態を更新
        shields.draw(screen) # 防御壁を描画
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
