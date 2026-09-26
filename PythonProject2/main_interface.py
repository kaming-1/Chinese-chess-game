from kivy.uix.relativelayout import RelativeLayout
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.clock import Clock
import os

from kivy.core.window import Window
Window.size = 500, 603

class MainInterface(RelativeLayout):
    """Simple main interface with background and Start button.
        简约的主界面，带有背景和启动按钮。
    This was extracted from gm1.MainMenu so the main UI operations live
    in a separate module.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base_dir = os.path.dirname(__file__)
        self.bg_texture = CoreImage(os.path.join(base_dir, 'image', 'chessboard_image.jpg')).texture
        # center Start button, choose font if available 中央“开始”按钮，选择字体（如果可用）
        font_name = r"C:\Windows\Fonts\simsun.ttc"
        self.start_btn = Button(text='开始游戏', size_hint=(None,None),
                                    size=(160,48), font_name=font_name)
        # Use on_release and schedule the start on the next frame to avoid UI-state issues
        # 使用on_release并计划在下一帧开始，以避免UI状态问题
        self.start_btn.bind(on_release=lambda *_: Clock.schedule_once(lambda dt: self.start_game(), 0))
        self.add_widget(self.start_btn)
        self.bind(size=self._redraw, pos=self._redraw)

        self.setting_btn = Button(text='设置', size_hint=(None, None),
                                  size=(160, 48), font_name=font_name)
        self.setting_btn.bind(on_release=lambda *_: Clock.schedule_once(lambda dt: self.settings(), 0))
        self.add_widget(self.setting_btn)
        self.bind(size=self._redraw, pos=self._redraw)

        self._redraw()

    def _redraw(self, *args):
        # position background and center button 位置背景和中心按钮
        self.canvas.clear()
        w,h = self.width, self.height
        with self.canvas:
            if self.bg_texture:
                Rectangle(pos=(0,0), size=(w,h), texture=self.bg_texture)
            else:
                Color(0.95,0.9,0.8)
                Rectangle(pos=(0,0), size=(w,h))
        # center the start button
        self.start_btn.pos = ((w - self.start_btn.width)/2, (h - self.start_btn.height)/2 + 30)
        # ensure button on top
        if self.start_btn in self.children:
            self.remove_widget(self.start_btn)
            self.add_widget(self.start_btn)
        self.setting_btn.pos = ((w - self.setting_btn.width)/2, (h - self.setting_btn.height)/2 - 30)
        # ensure button on top
        if self.setting_btn in self.children:
            self.remove_widget(self.setting_btn)
            self.add_widget(self.setting_btn)


    def start_game(self):
        # replace application root with the BoardWidget to ensure proper sizing/layout 用BoardWidget替换应用程序根，以确保适当的大小/布局
            # remove/hide start button immediately so it cannot remain visible 立即删除/隐藏开始按钮，使其无法保持可见
            if hasattr(self, 'start_btn') and self.start_btn in self.children:
                self.remove_widget(self.start_btn)
            # create the board lazily to avoid import-time cycles
            from gm1 import BoardWidget
            from setting_interface import SettingsInterface
            board = BoardWidget(ai_depth=SettingsInterface.ai_depth)
            board.size_hint = (1,1)
            board.pos = (0,0)

            # prefer using the App to swap root so layout/sizing behaves normally
            from kivy.app import App
            app = App.get_running_app()
            # try removing the previous root from its parent/window to avoid it remaining visible
            old_root = app.root
            if old_root is not None:
                if hasattr(old_root, 'parent') and old_root.parent:
                    old_root.parent.remove_widget(old_root)

                    from kivy.core.window import Window as _Window
                    if old_root in list(_Window.children):
                        _Window.remove_widget(old_root)

                # set and ensure board is attached to the window if necessary
            app.root = board

            from kivy.core.window import Window as _Window

            if board not in _Window.children:
                _Window.add_widget(board)

                # schedule a redraw on the next frame when sizes are settled
            Clock.schedule_once(lambda dt: board._redraw(), 0)
                # fallback: add to this menu and size to fill
            self.clear_widgets()


    def settings(self):
        if hasattr(self, 'setting_btn') and self.setting_btn in self.children:
            self.remove_widget(self.setting_btn)
        from setting_interface import SettingsInterface
        si = SettingsInterface()
        Window.add_widget(si)

