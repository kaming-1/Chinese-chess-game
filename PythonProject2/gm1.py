
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
import json
import os
from kivy.core.image import Image as CoreImage
from kivy.clock import Clock
from kivy.uix.slider import Slider

from chessboard import ChessBoard, PIECE_CHARS, COLS, ROWS
from ai_opponent import AiOpponent

# 棋子与规则函数已拆分到 chess_pieces.py（inside_board/inside_palace/find_general 等）

class BoardWidget(RelativeLayout):
    def __init__(self, ai_depth=1, **kwargs):
        super().__init__(**kwargs)
        # 设置窗口默认大小为 500x603（比例 50:60）
        Window.size = (500, 603)
        Window.clearcolor = (0.95, 0.9, 0.8, 1)
        # 尝试加载棋盘背景图片（尝试同目录、image 子目录，或在子树中搜索）
        self.bg_texture = None
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, 'chessboard_image.jpg'),
            os.path.join(base_dir, 'chessboard_image.png'),
            os.path.join(base_dir, 'image', 'chessboard_image.jpg'),
            os.path.join(base_dir, 'image', 'chessboard_image.png'),
        ]
        found = None
        for p in candidates:
            if os.path.exists(p):
                found = p
                break
        if not found:
            # 回退：在项目子树里查找首个匹配文件
            for root, dirs, files in os.walk(base_dir):
                for fn in files:
                    if fn.startswith('chessboard_image.'):
                        found = os.path.join(root, fn)
                        break
                if found:
                    break
        if found:
            try:
                self.bg_texture = CoreImage(found).texture
            except Exception as e:
                print('加载背景图失败:', e)
                self.bg_texture = None

        # 预加载棋子图片（如果存在）。优先查找子目录 image/black_chess 和 image/red_chess，
        # 同时兼容旧的 image 根目录中以 "black_将.png" 或 "red_帅.png" 命名的文件。
        self.piece_textures = {}
        img_dir = os.path.join(base_dir, 'image')
        char_to_code = {'车': 'R', '马': 'H', '相': 'E', '象': 'E', '仕': 'A', '士': 'A',
                        '帅': 'K', '将': 'K', '炮': 'C', '砲': 'C', '兵': 'P', '卒': 'P'}
        # 构建待扫描目录列表：优先黑/红子目录，然后回退到根目录
        candidate_dirs = []
        if os.path.isdir(img_dir):
            for sub in ('black_chess', 'red_chess', 'black', 'red'):
                p = os.path.join(img_dir, sub)
                if os.path.isdir(p):
                    color = 'b' if 'black' in sub else 'r'
                    candidate_dirs.append((p, color))
            # 最后加入根目录（不指定颜色，依赖文件名判断）
            candidate_dirs.append((img_dir, None))

        for dir_path, forced_color in candidate_dirs:
            try:
                for fn in os.listdir(dir_path):
                    if not fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                        continue
                    name = os.path.splitext(fn)[0]
                    piece_char = None
                    color_prefix = None
                    # 如果目录本身表明颜色，则优先使用目录颜色
                    if forced_color:
                        color_prefix = forced_color
                        # 尝试用整个文件名或按下划线后半部分识别棋子字符
                        parts = name.split('_')
                        if len(parts) >= 2:
                            piece_char = parts[-1]
                        else:
                            piece_char = parts[0]
                    else:
                        # 兼容旧命名：black_将.png 或 red_帅.png
                        parts = name.split('_')
                        if len(parts) >= 2:
                            color_token = parts[0].lower()
                            piece_char = parts[1]
                            if 'black' in color_token or color_token in ('b', '黑', 'hei'):
                                color_prefix = 'b'
                            elif 'red' in color_token or color_token in ('r', '红', 'hong'):
                                color_prefix = 'r'
                            else:
                                color_prefix = 'b' if color_token.startswith('b') else ('r' if color_token.startswith('r') else None)
                        else:
                            # 无下划线且未指定目录颜色，无法确定颜色 -> 跳过
                            continue
                    if not color_prefix or not piece_char:
                        continue
                    code = char_to_code.get(piece_char)
                    if not code:
                        # 有时文件名可能使用英文码（R,H,...），尝试直接取第一个字符
                        if piece_char and piece_char.upper() in ('R','H','E','A','K','C','P'):
                            code = piece_char.upper()
                        else:
                            continue
                    key = color_prefix + code
                    path = os.path.join(dir_path, fn)
                    try:
                        tex = CoreImage(path).texture
                        self.piece_textures[key] = tex
                    except Exception as e:
                        print(f'加载棋子图片失败 {path}:', e)
            except Exception:
                # 忽略无法读取的目录
                continue

        # 选择一个支持中文的字体（Windows 常见字体），用于按钮/标签以避免显示方块
        self.font_name = None
        font_candidates = [
            r"C:\Windows\Fonts\msyh.ttf",
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttf",
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\simsun.ttc",
        ]
        for p in font_candidates:
            if os.path.exists(p):
                self.font_name = p
                break

        self.chess = ChessBoard()
        self.board = self.chess.board
        self.ai_opponent = AiOpponent(self.chess, ai_depth)
        self.cell_w = self.width / COLS
        self.cell_h = self.height / ROWS
        self.selected = None
        self.piece_widgets = []
        self.turn = 'r'  # 红方先手
        # 状态标签（使用中文字体以避免方块字符）
        if self.font_name:
            self.status_lbl = Label(text='红方回合', size_hint=(None,None), pos=(10,10), font_name=self.font_name)
        else:
            self.status_lbl = Label(text='红方回合', size_hint=(None,None), pos=(10,10))
        self.add_widget(self.status_lbl)
        # 回合显示（位于楚河汉界处），使用只读 Button 以便有背景
        if self.font_name:
            self.turn_label = Button(text='回合: 0', size_hint=(None,None), size=(140,30), disabled=True, font_name=self.font_name)
        else:
            self.turn_label = Button(text='回合: 0', size_hint=(None,None), size=(140,30), disabled=True)
        self.add_widget(self.turn_label)
        # 历史栈：存储棋盘快照和回合（已保留以备将来扩展）
        self.history = []
        self.game_over = False
        self._end_buttons_visible = False
        # 先添加控件，再在 _redraw 末尾保证它们位于顶部
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        # 清除 canvas 并移除旧的棋子控件（只移除由 _add_piece_widget 标记的 widget），保留按钮和状态标签
        self.canvas.before.clear()
        self.canvas.after.clear()
        self.canvas.clear()
        for child in list(self.children):
            if getattr(child, '_is_piece', False):
                self.remove_widget(child)
        self.piece_widgets = []
        w, h = self.width, self.height
        margin = 10
        # If widget size not set (e.g. just created), fall back to Window size
        try:
            if (not w or not h) or (w < 200 or h < 200):
                w, h = Window.size
        except Exception:
            try:
                w, h = (500, 603)
            except Exception:
                w, h = (500, 603)
        board_w = w - margin*2
        board_h = h - margin*2
        # 防御性检查：确保 self.board 有效
        try:
            if not hasattr(self, 'board') or not isinstance(self.board, list) or len(self.board) != ROWS:
                self.chess = ChessBoard()
                self.board = self.chess.board
                self.ai_opponent.set_board(self.chess)
        except Exception:
            self.chess = ChessBoard()
            self.board = self.chess.board
            self.ai_opponent.set_board(self.chess)
        # 统计现有棋子数用于调试
        try:
            piece_count = sum(1 for row in self.board for p in row if p)
        except Exception:
            piece_count = 0
        self.cell_w = board_w / COLS if COLS else 0
        self.cell_h = board_h / ROWS if ROWS else 0
        x0, y0 = margin, margin
        with self.canvas:
            # 背景图（若可用）
            if self.bg_texture:
                Rectangle(pos=(x0, y0), size=(board_w, board_h), texture=self.bg_texture)
            else:
                Color(1, 1, 1)
                Rectangle(pos=(x0, y0), size=(board_w, board_h))
                Color(0,0,0)
                # 竖线
                for c in range(COLS):
                    x = x0 + c * self.cell_w + self.cell_w/2
                    Line(points=[x, y0 + self.cell_h/2, x, y0 + board_h - self.cell_h/2], width=1)
                # 横线
                for r in range(ROWS):
                    y = y0 + r * self.cell_h + self.cell_h/2
                    Line(points=[x0 + self.cell_w/2, y, x0 + board_w - self.cell_w/2, y], width=1)
        # 绘制棋子
        for r in range(ROWS):
            for c in range(COLS):
                p = self.board[r][c]
                if p:
                    # optionally log which piece is being drawn (disabled)
                    self._add_piece_widget(p, r, c)
        # 高亮选中格
        if self.selected:
            r,c = self.selected
            # 将选中高亮放在棋盘之上但在控件之下，使用 canvas.before 保证不遮挡按钮
            with self.canvas:
                Color(1,0,0,0.25)
                Rectangle(pos=(x0 + c*self.cell_w + self.cell_w*0.1, y0 + r*self.cell_h + self.cell_h*0.1), size=(self.cell_w*0.8, self.cell_h*0.8))
        # 更新状态文本
        if not getattr(self, '_end_buttons_visible', False):
            self.status_lbl.text = ("红方回合" if self.turn == 'r' else "黑方回合") + (" - 将军!" if self.is_in_check(self.turn) else "")
        # 更新位于楚河汉界处的回合显示（居中）
        move_count = len(self.history)
        self.turn_label.text = f'回合: {move_count} | {"红方" if self.turn == "r" else "黑方"}'
        # 自适应尺寸
        tw = min(180, max(100, int(board_w * 0.25)))
        th = max(20, int(self.cell_h * 0.6))
        self.turn_label.size = (tw, th)
        tx = x0 + (board_w - tw) / 2
        ty = y0 + (4.5) * self.cell_h - th / 2 + 35
        # 上移 35px（较之前 50px 向下 15px）
        self.turn_label.pos = (tx, ty)
        # 把状态栏和按钮放在窗口顶端固定高度区域，避免使用 cell_h 导致位置落在棋盘中间
        top_bar_height = 30
        top_y = self.height - margin - top_bar_height
        # 设置状态标签尺寸和位置
        self.status_lbl.font_size = min(18, max(12, int(top_bar_height * 0.6)))
        self.status_lbl.size = (board_w, top_bar_height)
        self.status_lbl.pos = (10, top_y)
        # 确保状态标签和回合标签位于最上层（重添加到 widget 列表末尾）
        for ctrl in (self.status_lbl, self.turn_label):
            if ctrl in self.children:
                self.remove_widget(ctrl)
                self.add_widget(ctrl)

        # 若已结束并且确认为胜利/对局终结，显示居中“再来一局”和“返回主界面”按钮
        show_end_buttons = getattr(self, 'game_over', False) and (('胜' in (getattr(self, 'status_lbl', None) and getattr(self.status_lbl, 'text', '') ) ) or getattr(self, '_end_buttons_visible', False))
        if show_end_buttons:
            # create replay button if needed
            if not hasattr(self, 'replay_btn'):
                if getattr(self, 'font_name', None):
                    self.replay_btn = Button(text='再来一局', size_hint=(None, None), size=(160, 48), font_name=self.font_name)
                else:
                    self.replay_btn = Button(text='再来一局', size_hint=(None, None), size=(160, 48))
                self.replay_btn.disabled = True
                if self.replay_btn not in self.children:
                    self.add_widget(self.replay_btn)
            # create back button if needed
            if not hasattr(self, 'back_btn'):
                if getattr(self, 'font_name', None):
                    self.back_btn = Button(text='返回主界面', size_hint=(None, None), size=(160, 48), font_name=self.font_name)
                else:
                    self.back_btn = Button(text='返回主界面', size_hint=(None, None), size=(160, 48))
                self.back_btn.disabled = True
                if self.back_btn not in self.children:
                    self.add_widget(self.back_btn)
            # after delay, enable and bind the click handlers (so a prior touch release can't trigger them)
            def _enable_and_bind(dt):
                if hasattr(self, 'replay_btn') and not getattr(self.replay_btn, '_replay_bound', False):
                    self.replay_btn.bind(on_release=lambda *_: self.restart_game())
                    self.replay_btn._replay_bound = True
                if hasattr(self, 'back_btn') and not getattr(self.back_btn, '_back_bound', False):
                    self.back_btn.bind(on_release=lambda *_: self.return_to_main())
                    self.back_btn._back_bound = True
                if hasattr(self, 'replay_btn'):
                    self.replay_btn.disabled = False
                if hasattr(self, 'back_btn'):
                    self.back_btn.disabled = False
            Clock.schedule_once(_enable_and_bind, 0.7)
            # position buttons in the center stack
            bw = board_w
            bh = board_h
            bx = x0 + (bw - 160) / 2
            by = y0 + (bh - 48) / 2
            spacing = 12
            # replay on top, back below
            if hasattr(self, 'replay_btn'):
                self.replay_btn.pos = (bx, by + (spacing/2 + 24))
            if hasattr(self, 'back_btn'):
                self.back_btn.pos = (bx, by - (spacing/2 + 24))
            # Ensure end buttons are topmost: re-add them last
            for btn_attr in ('replay_btn', 'back_btn'):
                if hasattr(self, btn_attr):
                    btn = getattr(self, btn_attr)
                    if btn in list(self.children):
                        # remove and re-add to bring to front
                        self.remove_widget(btn)
                    self.add_widget(btn)
        else:
            # leave removal to restart_game; avoid unexpected deletion during redraw
            pass

    def _add_piece_widget(self, piece, r, c):
        # 优先使用图片纹理（若已预加载），否则回退为文本标签
        textures = getattr(self, 'piece_textures', {}) or {}
        tex = textures.get(piece)
        x = 10 + c*self.cell_w
        y = 10 + r*self.cell_h
        size_w = self.cell_w * 0.9
        size_h = self.cell_h * 0.9
        if tex:
            # 保持图片纵横比，适配到单元格内
            draw_w = size_w
            draw_h = size_h
            tw = getattr(tex, 'width', None) or (tex.size[0] if hasattr(tex, 'size') else None)
            th = getattr(tex, 'height', None) or (tex.size[1] if hasattr(tex, 'size') else None)
            if tw and th and tw > 0 and th > 0:
                tex_ratio = tw / th
                cell_ratio = size_w / size_h if size_h else 1
                if cell_ratio > tex_ratio:
                    # cell is wider relative to height; limit by height
                    draw_h = size_h
                    draw_w = tex_ratio * draw_h
                else:
                    # limit by width
                    draw_w = size_w
                    draw_h = draw_w / tex_ratio
            x_off = (self.cell_w - draw_w) / 2
            y_off = (self.cell_h - draw_h) / 2
            # draw the piece in canvas.after so it appears above board lines and background
            with self.canvas:
                Rectangle(pos=(x + x_off, y + y_off), size=(draw_w, draw_h), texture=tex)
            # 记录占位信息（非 widget）
            self.piece_widgets.append(('tex', piece, r, c))
        else:
            color = (1,0,0,1) if piece.startswith('r') else (0,0,0,1)
            code = piece[1]
            ch = PIECE_CHARS.get(code, code)
            if getattr(self, 'font_name', None):
                lbl = Label(text=ch, color=color, font_size=min(self.cell_w, self.cell_h)*0.5, font_name=self.font_name)
            else:
                lbl = Label(text=ch, color=color, font_size=min(self.cell_w, self.cell_h)*0.5)
            lbl.size_hint = (None, None)
            lbl.size = (self.cell_w, self.cell_h)
            lbl.pos = (x, y)
            # label added for piece (no debug log)            # 标记为棋子控件，方便在重绘时只移除这些控件
            lbl._is_piece = True
            self.add_widget(lbl)
            self.piece_widgets.append(lbl)

    # ---------------- game logic ----------------
    def is_enemy(self, p1, p2):
        return self.chess.is_enemy(p1, p2)

    def occupied(self, board, r, c):
        return board[r][c] is not None

    def generate_pseudo_moves(self, board, r, c):
        # Delegate to ChessBoard which operates on its own board state
        return self.chess.generate_pseudo_moves(r, c)

    def is_in_check(self, color):
        return self.chess.is_in_check(color)

    def generals_face(self, board):
        return self.chess.generals_face()

    def move_causes_self_check(self, sr, sc, tr, tc):
        return self.chess.move_causes_self_check(sr, sc, tr, tc)

    def has_any_legal_move(self, color):
        return self.chess.has_any_legal_move(color)

    # ---------------- 简单 AI（黑方） ----------------
    def _do_ai_move(self, dt=None):
        # 仅在黑方回合调用
        if self.turn != 'b':
            return
        # 如果黑方无合法着法，则判红方胜
        if not self.has_any_legal_move('b'):
            self.status_lbl.text = "红方胜"
            self.game_over = True
            self._end_buttons_visible = True
            self._redraw()
            return
        mv = self.ai_opponent.choose_move('b')
        if not mv:
            self.status_lbl.text = "红方胜"
            self.game_over = True
            self._end_buttons_visible = True
            self._redraw()
            return
        sr, sc, tr, tc = mv
        captured = self.ai_opponent.apply_move(mv)
        self.history.append((sr, sc, tr, tc, captured))
        if len(self.history) > 200:
            self.history.pop(0)
        # 切换回合
        self.turn = 'b' if self.turn == 'r' else 'r'
        # 检查是否将死（对手是否被将死）
        if self.is_in_check(self.turn) and not self.has_any_legal_move(self.turn):
            self.status_lbl.text = ("黑方胜" if self.turn == 'r' else "红方胜")
            self.game_over = True
            self._end_buttons_visible = True
        self._redraw()

    # ---------------- 输入处理 ----------------
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        # If end buttons are visible or game_over, allow clicking them by manually dispatching
        if getattr(self, 'game_over', False) or getattr(self, '_end_buttons_visible', False):
            for btn_name in ('replay_btn', 'back_btn'):
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    if btn and btn.collide_point(*touch.pos):
                        if getattr(btn, 'disabled', False):
                            return True
                        try:
                            btn.trigger_action(duration=0)
                        except Exception:
                            btn.dispatch('on_release')
                        return True

        # 让按钮/滑块等子控件优先处理点击事件
        for child in list(self.children):
            if child is not self and isinstance(child, (Button, Slider)):
                if child.collide_point(*touch.pos):
                    return False
        # 若已结束则屏蔽棋盘交互（仍允许顶部控件交互）
        if getattr(self, 'game_over', False):
            return True
        local_x = touch.x - 10
        local_y = touch.y - 10
        c = int(local_x // self.cell_w)
        r = int(local_y // self.cell_h)
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return False
        p = self.board[r][c]
        if self.selected is None:
            if p and p[0] == self.turn:
                self.selected = (r,c)
        else:
            sr, sc = self.selected
            if (sr,sc) == (r,c):
                self.selected = None
            else:
                # 尝试走子
                piece = self.board[sr][sc]
                if not piece:
                    self.selected = None
                else:
                    legal_targets = self.generate_pseudo_moves(self.board, sr, sc)
                    if (r,c) in legal_targets and not self.move_causes_self_check(sr,sc,r,c):
                        # 记录增量历史用于悔棋（sr,sc -> r,c, 被吃掉的棋子）
                        captured = self.board[r][c]
                        self.history.append((sr, sc, r, c, captured))
                        if len(self.history) > 200:
                            self.history.pop(0)
                        # 应用走子
                        self.board[r][c] = self.board[sr][sc]
                        self.board[sr][sc] = None
                        # 切换回合
                        self.turn = 'b' if self.turn == 'r' else 'r'
                        # 检查是否将死
                        if self.is_in_check(self.turn) and not self.has_any_legal_move(self.turn):
                            self.status_lbl.text = ("黑方胜" if self.turn == 'r' else "红方胜")
                            self.game_over = True
                            self._end_buttons_visible = True
                        self.selected = None
                        # 若切换到黑方（AI），短延迟后让 AI 行棋
                        if self.turn == 'b':
                            Clock.schedule_once(self._do_ai_move, 0.5)
                    else:
                        # 非法走：若点击己方棋子则切换选中
                        if p and p[0] == self.turn:
                            self.selected = (r,c)
                        else:
                            # 保持选中
                            pass
        self._redraw()
        return True

    def restart_game(self, *args):
        """Reset board to initial state and start a new game."""
        self.chess = ChessBoard()
        self.board = self.chess.board
        self.ai_opponent.set_board(self.chess)
        self.history = []
        self.turn = 'r'
        self.game_over = False
        self._end_buttons_visible = False
        self.selected = None
        self.status_lbl.text = '红方回合'
        # robustly remove replay/back buttons from whichever parent they're attached to
        for attr in ('replay_btn', 'back_btn'):
            if hasattr(self, attr):
                btn = getattr(self, attr)
                parent = getattr(btn, 'parent', None)
                if parent is not None:
                    parent.remove_widget(btn)
                btn.unbind(on_release=None)
                delattr(self, attr)
        # ensure UI updates
        self._redraw()

    def return_to_main(self, *args):
        """Return to the main menu (replace app root)."""
        from kivy.app import App
        app = App.get_running_app()
        # create MainInterface and set as root
        from main_interface import MainInterface
        menu = MainInterface()
        parent = getattr(self, 'parent', None)
        if parent is not None:
            parent.remove_widget(self)
        from kivy.core.window import Window as _Window
        if self in list(_Window.children):
            _Window.remove_widget(self)
        try:
            app.root = menu
            from kivy.core.window import Window as _Window
            if menu not in list(_Window.children):
                _Window.add_widget(menu)
        except Exception:
            app.root = menu
        Clock.schedule_once(lambda dt: menu._redraw(), 0)


class XiangqiApp(App):
    def build(self):
        from main_interface import MainInterface
        return MainInterface()

if __name__ == '__main__':
    XiangqiApp().run()
