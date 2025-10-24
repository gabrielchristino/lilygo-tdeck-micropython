"""Material Design inspired components for MicroPython displays"""

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

