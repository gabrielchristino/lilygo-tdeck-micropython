"""UI Manager for handling input field interactions"""

from lib.material_components import TextInput, NumericInput
from lib.touch import Touch

class UIManager:
    def __init__(self, display, touch, i2c, font):
        self.display = display
        self.touch = touch
        self.i2c = i2c
        self.font = font
        self.inputs = []
        self.focused_input = None

    def add_text_input(self, x, y, w, h, placeholder, bg_color, text_color):
        """Add a text input field"""
        input_field = TextInput(
            x=x, y=y, w=w, h=h,
            placeholder=placeholder,
            bg_color=bg_color,
            text_color=text_color,
            font=self.font,
        ).draw(self.display)
        self.inputs.append(input_field)
        return input_field

    def add_numeric_input(self, x, y, w, h, placeholder, bg_color, text_color):
        """Add a numeric input field"""
        input_field = NumericInput(
            x=x, y=y, w=w, h=h,
            placeholder=placeholder,
            bg_color=bg_color,
            text_color=text_color,
            font=self.font,
        ).draw(self.display)
        self.inputs.append(input_field)
        return input_field

    def handle_touch(self):
        """Process touch events for focus management"""
        event_type, x, y = self.touch.read()

        if event_type == Touch.TAP:
            new_focus = None
            for inp in self.inputs:
                if inp.is_touched((x, y)):
                    new_focus = inp
                    break

            # Manage focus change and redraw fields
            if new_focus != self.focused_input:
                if self.focused_input:
                    self.focused_input.focused = False
                    self.focused_input.draw(self.display)  # Redraw without focus border

                if new_focus:
                    new_focus.focused = True
                    new_focus.draw(self.display)  # Redraw with focus border

                self.focused_input = new_focus

    def handle_keyboard(self, get_key_func):
        """Process keyboard input for focused field"""
        if self.focused_input:
            key = get_key_func(self.i2c)
            if key:
                # handle_key returns True if text was changed
                if self.focused_input.handle_key(key):
                    # Redraw only the text part for faster updates
                    self.focused_input.draw_text(self.display)
                    print(f"Campo '{self.focused_input.placeholder}' atualizado: '{self.focused_input.value}'")
                elif key == b'\r':  # Enter key
                    print(f"Valor final do campo '{self.focused_input.placeholder}': {self.focused_input.value}")
