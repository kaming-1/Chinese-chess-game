from kivy.uix.relativelayout import RelativeLayout
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
import os

class SettingsInterface(RelativeLayout):
    """
    此类用于 绘制设置界面 和 调整部分设置
    """
    ai_depth = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # look for chessboard image in project or image/ directory
        base_dir = os.path.dirname(__file__)
        self.bg_texture = CoreImage(os.path.join(base_dir, 'image', 'chessboard_image.jpg')).texture
        # center Start button, choose font if available 中央“开始”按钮，选择字体（如果可用）
        font_name = r"C:\Windows\Fonts\simsun.ttc"
        self.main_btn = Button(text='主界面', size_hint=(None, None),
                               size=(160, 48), font_name=font_name)
        # Use on_release and schedule the start on the next frame to avoid UI-state issues
        # 使用on_release并计划在下一帧开始，以避免UI状态问题
        self.main_btn.bind(on_release=lambda *_: Clock.schedule_once(lambda dt: self.main_itf(), 0))
        self.add_widget(self.main_btn)
        self.depth_label = Label(text=f'AI 深度: {self.ai_depth}',
                                 size_hint=(None, None), size=(180, 36),
                                 font_name=font_name)
        self.depth_slider = Slider(min=1, max=5, value=self.ai_depth, step=1,
                                   size_hint=(None, None), size=(240, 36))
        self.depth_slider.bind(value=self.on_depth_change)
        self.add_widget(self.depth_label)
        self.add_widget(self.depth_slider)
        self.bind(size=self._redraw, pos=self._redraw)
        self._redraw()

    def on_depth_change(self, instance, value):
        SettingsInterface.ai_depth = max(1, int(round(value)))
        self.depth_label.text = f'AI 深度: {SettingsInterface.ai_depth}'

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
        center_x = (w - self.depth_slider.width) / 2
        self.depth_label.pos = ((w - self.depth_label.width) / 2,
                                (h - self.depth_slider.height) / 2 + 55)
        self.depth_slider.pos = (center_x, (h - self.depth_slider.height) / 2 + 10)
        self.main_btn.pos = ((w - self.main_btn.width) / 2,
                             (h - self.main_btn.height) / 2 - 65)
        # ensure button on top
        for widget in (self.depth_label, self.depth_slider, self.main_btn):
            if widget in self.children:
                self.remove_widget(widget)
                self.add_widget(widget)


    def main_itf(self):
        if hasattr(self, 'main_btn') and self.main_btn in self.children:
            self.remove_widget(self.main_btn)
        if hasattr(self, 'depth_label') and self.depth_label in self.children:
            self.remove_widget(self.depth_label)
        if hasattr(self, 'depth_slider') and self.depth_slider in self.children:
            self.remove_widget(self.depth_slider)

        from main_interface import MainInterface
        mi = MainInterface()

        from kivy.core.window import Window as _Window
        _Window.add_widget(mi)



if __name__ == '__main__':
    from kivy.app import App

    from kivy.core.window import Window
    Window.size = 500, 603

    class Myapp(App):
        def build(self):
            return SettingsInterface()

    Myapp().run()
