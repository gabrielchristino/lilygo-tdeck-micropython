"""UI Manager for handling input field interactions"""

from lib.material_components import TextInput, NumericInput
from lib.touch import Touch
from lib.trackball import Trackball
from lib.sound import SoundManager # Mantido para referência, mas a instância é injetada

class UIManager:
    def __init__(self, display, touch, i2c, font, trackball, sound):
        self.display = display
        self.touch = touch
        self.i2c = i2c
        self.font = font
        self.inputs = []
        self.focused_input = None
        self.trackball = trackball # Usa a instância injetada
        self.sound = sound         # Usa a instância injetada

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

            # Manage focus change and redraw fields only if focus actually changed
            if new_focus != self.focused_input:
                # Clear previous focus
                if self.focused_input:
                    self.focused_input.focused = False
                    self.focused_input.draw(self.display)  # Redraw without focus border

                # Set new focus
                if new_focus:
                    new_focus.focused = True
                    new_focus.draw(self.display)  # Redraw with focus border
                    self.sound.play_touch_select()  # Play sound when field is selected by touch

                self.focused_input = new_focus

    def handle_trackball(self):
        """Process trackball events for navigation between fields"""
        direction, click = self.trackball.get_direction()

        if direction:
            current_index = -1
            if self.focused_input:
                try:
                    current_index = self.inputs.index(self.focused_input)
                except ValueError:
                    current_index = -1

            new_index = current_index

            if direction == 'up':
                new_index = max(0, current_index - 1)
            elif direction == 'down':
                new_index = min(len(self.inputs) - 1, current_index + 1)
            elif direction == 'left':
                new_index = max(0, current_index - 1)
            elif direction == 'right':
                new_index = min(len(self.inputs) - 1, current_index + 1)

            if new_index != current_index:
                # Change focus - only redraw if actually changing
                if self.focused_input:
                    self.focused_input.focused = False
                    self.focused_input.draw(self.display)

                if new_index >= 0:
                    self.inputs[new_index].focused = True
                    self.inputs[new_index].draw(self.display)
                    self.focused_input = self.inputs[new_index]
                    self.sound.play_navigation()  # Play sound when navigating with trackball
                else:
                    self.focused_input = None

        if click and self.focused_input:
            # Um clique do trackball em um campo focado é uma confirmação.
            # Toca o som de confirmação e retorna True para sinalizar ao app para sair.
            print(f"Valor final do campo '{self.focused_input.placeholder}': {self.focused_input.value}")
            self.sound.play_confirm()
            return True # Indica que um clique de confirmação foi processado

        return False # Nenhum clique de confirmação processado

    def handle_keyboard(self, get_key_func):
        """Process keyboard input for focused field"""
        if self.focused_input:
            key = get_key_func(self.i2c)
            if key:
                # Debug print to check if keys are being read
                print(f"Tecla recebida: {key}")
                # handle_key returns True if text was changed
                if self.focused_input.handle_key(key):
                    # Redraw only the text part for faster updates
                    self.focused_input.draw_text(self.display)
                    print(f"Campo '{self.focused_input.placeholder}' atualizado: '{self.focused_input.value}'")
                    self.sound.play_keypress()  # Play sound when typing
                elif key == b'\r':  # Enter key
                    print(f"Valor final do campo '{self.focused_input.placeholder}': {self.focused_input.value}")
                    self.sound.play_confirm()  # Play sound when pressing Enter
