"""Material Design inspired components for MicroPython displays"""
import st7789py as st7789

class InputBase:
    """Base class for input components"""
    def __init__(self, x, y, w, h, bg_color, text_color, font, border_radius=8, placeholder=""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = font
        self.border_radius = border_radius
        self.placeholder = placeholder
        self.value = ""
        self.cursor_pos = 0
        self.focused = False
        
    def is_touched(self, touch_point):
        """Check if the input field was touched"""
        if not touch_point:
            return False
        x, y = touch_point
        return (self.x <= x <= self.x + self.w and 
                self.y <= y <= self.y + self.h)
        
    def _draw_rounded_rect(self, display, x, y, w, h, r, color):
        """Draw a rounded rectangle"""
        r = min(r, w//2, h//2)
        display.fill_rect(x+r, y, w-2*r, h, color)
        display.fill_rect(x, y+r, r, h-2*r, color)
        display.fill_rect(x+w-r, y+r, r, h-2*r, color)
        
        for corner_x, corner_y in [(x+r, y+r), (x+w-r-1, y+r),
                                 (x+r, y+h-r-1), (x+w-r-1, y+h-r-1)]:
            self._draw_corner(display, corner_x, corner_y, r, color)
            
    def _draw_corner(self, display, x, y, r, color):
        """Draw a rounded corner"""
        f = 1 - r
        dx = 1
        dy = -2 * r
        px = 0
        py = r

        while px < py:
            if f >= 0:
                py -= 1
                dy += 2
                f += dy
            px += 1
            dx += 2
            f += dx
            
            display.pixel(x + px, y + py, color)
            display.pixel(x - px, y + py, color)
            display.pixel(x + px, y - py, color)
            display.pixel(x - px, y - py, color)
            display.pixel(x + py, y + px, color)
            display.pixel(x - py, y + px, color)
            display.pixel(x + py, y - px, color)
            display.pixel(x - py, y - px, color)
            display.hline(x - px, y + py, 2 * px + 1, color)
            display.hline(x - px, y - py, 2 * px + 1, color)
            display.hline(x - py, y + px, 2 * py + 1, color)
            display.hline(x - py, y - px, 2 * py + 1, color)
    
    def draw(self, display):
        """Draw the input field"""
        # Always clear the border area first to remove any previous focus highlight
        display.fill_rect(self.x-2, self.y-2, self.w+4, self.h+4, st7789.color565(30, 30, 30))  # Use display background color

        # Draw focus border if focused
        if self.focused:
            if self.border_radius > 0:
                self._draw_rounded_rect(display, self.x-2, self.y-2, self.w+4, self.h+4,
                                      self.border_radius+2, st7789.BLUE)
            else:
                display.rect(self.x-2, self.y-2, self.w+4, self.h+4, st7789.BLUE)

        # Draw main input field
        if self.border_radius > 0:
            self._draw_rounded_rect(display, self.x, self.y, self.w, self.h,
                                  self.border_radius, self.bg_color)
        else:
            display.fill_rect(self.x, self.y, self.w, self.h, self.bg_color)

        text = self.value if self.value else self.placeholder
        text_y = self.y + (self.h - self.font.HEIGHT) // 2
        text_color = self.text_color if self.value else st7789.GRAY
        display.text(self.font, text, self.x + 5, text_y, text_color, self.bg_color)
        return self

    def draw_text(self, display):
        """Draw only the text part of the input field for faster updates."""
        # Clear previous text by drawing a filled rectangle over the text area
        display.fill_rect(self.x + 5, self.y + 5, self.w - 10, self.h - 10, self.bg_color)

        text = self.value if self.value else self.placeholder
        text_y = self.y + (self.h - self.font.HEIGHT) // 2
        text_color = self.text_color if self.value else st7789.GRAY
        display.text(self.font, text, self.x + 5, text_y, text_color, self.bg_color)
        return self
        
    def handle_key(self, key):
        """Handle keyboard input"""
        if key == b'\x08':  # Backspace
            if self.value:
                self.value = self.value[:-1]
                return True
        else:
            try:
                decoded = key.decode()
                if len(self.value) * self.font.WIDTH < (self.w - 10):  # Leave margin
                    self.value += decoded
                    return True
            except:
                pass
        return False

class TextInput(InputBase):
    """A Material Design inspired text input component"""
    def __init__(self, x, y, w, h, bg_color, text_color, font, border_radius=8, placeholder=""):
        super().__init__(x, y, w, h, bg_color, text_color, font, border_radius, placeholder)

class NumericInput(InputBase):
    """A Material Design inspired numeric input component"""
    def __init__(self, x, y, w, h, bg_color, text_color, font, border_radius=8, placeholder=""):
        super().__init__(x, y, w, h, bg_color, text_color, font, border_radius, placeholder)
        self._key_map = {
            'w': '1', 'e': '2', 'r': '3',
            's': '4', 'd': '5', 'f': '6',
            'z': '7', 'x': '8', 'c': '9', '0': '0'
        }
        
    def handle_key(self, key):
        """Handle keyboard input with number mapping"""
        if key == b'\x08':  # Backspace
            if self.value:
                self.value = self.value[:-1]
                return True
        elif key == b'\r':  # Enter
            return False
        else:
            try:
                decoded = key.decode().lower()
                if decoded in self._key_map:
                    if len(self.value) * self.font.WIDTH < (self.w - 10):
                        self.value += self._key_map[decoded]
                        return True
            except:
                pass
        return False

class Button:
    """A Material Design inspired button component"""
    
    def __init__(self, x, y, w, h, text, bg_color, text_color, font, border_radius=8):
        """Initialize a button
        
        Args:
            x (int): X position
            y (int): Y position 
            w (int): Width
            h (int): Height
            text (str): Button text
            bg_color (int): Background color in 565 format
            text_color (int): Text color in 565 format
            font: Font module to use for text
            border_radius (int): Border radius in pixels (default 8)
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color
        self.font = font
        self.border_radius = border_radius

    def contains(self, x, y):
        """Check if a point (x, y) is inside the button's bounds.
        
        Returns:
            bool: True if the point is inside, False otherwise.
        """
        return self.x <= x <= self.x + self.w and self.y <= y <= self.y + self.h

    def draw(self, display):
        """Draw the button on the display
        
        Args:
            display: Display object that implements required drawing methods
        """
        # Draw background with rounded corners if border_radius > 0
        if self.border_radius > 0:
            self._draw_rounded_rect(display, self.x, self.y, self.w, self.h, 
                                  self.border_radius, self.bg_color)
        else:
            display.fill_rect(self.x, self.y, self.w, self.h, self.bg_color)
            
        # Center and draw the text
        if self.text:
            # Get text dimensions 
            char_width = self.font.WIDTH
            char_height = self.font.HEIGHT
            text_width = len(self.text) * char_width
            text_height = char_height
            
            # Calculate centered position
            text_x = self.x + (self.w - text_width) // 2
            text_y = self.y + (self.h - text_height) // 2
            
            # Draw the text
            display.text(self.font, self.text, text_x, text_y, self.text_color, self.bg_color)
            
        return self

    def _draw_rounded_rect(self, display, x, y, w, h, r, color):
        """Draw a rounded rectangle
        
        Args:
            display: Display object
            x (int): X position
            y (int): Y position
            w (int): Width 
            h (int): Height
            r (int): Corner radius
            color (int): Color in 565 format
        """
        # Clamp radius to half of smallest dimension
        r = min(r, w//2, h//2)
        
        # Draw center rectangle
        display.fill_rect(x+r, y, w-2*r, h, color)
        
        # Draw side rectangles
        display.fill_rect(x, y+r, r, h-2*r, color)
        display.fill_rect(x+w-r, y+r, r, h-2*r, color)
        
        # Draw corners
        for corner_x, corner_y in [(x+r, y+r),        # Top left
                                 (x+w-r-1, y+r),      # Top right
                                 (x+r, y+h-r-1),      # Bottom left
                                 (x+w-r-1, y+h-r-1)]: # Bottom right
            self._draw_corner(display, corner_x, corner_y, r, color)

    def _draw_corner(self, display, x, y, r, color):
        """Draw a rounded corner using the Midpoint Circle Algorithm
        
        Args:
            display: Display object
            x (int): Circle center X
            y (int): Circle center Y 
            r (int): Radius
            color (int): Color in 565 format
        """
        f = 1 - r
        dx = 1
        dy = -2 * r
        px = 0
        py = r

        while px < py:
            if f >= 0:
                py -= 1
                dy += 2
                f += dy
            px += 1
            dx += 2
            f += dx
            
            display.pixel(x + px, y + py, color)
            display.pixel(x - px, y + py, color)
            display.pixel(x + px, y - py, color)
            display.pixel(x - px, y - py, color)
            display.pixel(x + py, y + px, color)
            display.pixel(x - py, y + px, color)
            display.pixel(x + py, y - px, color)
            display.pixel(x - py, y - px, color)
            # Preenche o arco com linhas horizontais
            display.hline(x - px, y + py, 2 * px + 1, color)
            display.hline(x - px, y - py, 2 * px + 1, color)
            display.hline(x - py, y + px, 2 * py + 1, color)
            display.hline(x - py, y - px, 2 * py + 1, color)
