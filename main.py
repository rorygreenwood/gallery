import logging
import os
import random
import tkinter as tk
from PIL import Image, ImageTk
from screeninfo import get_monitors

logger = logging.getLogger()

# --- Optimized Configuration for Pi 5 ---
VIEW_TIME = 5
FADE_STEPS = 40  # Lowered for smoother performance on Pi
FADE_DURATION = 1.5 # Seconds
LOCAL_CACHE = './local_cache/'

class PiSlideshow:
    def __init__(self, folder_path, monitor_index):
        self.folder_path = folder_path
        self.all_images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not self.all_images:
            raise RuntimeError(f"No images found in {folder_path}")

        # 1. Setup Monitors
        monitors = get_monitors()
        target = monitors[monitor_index] if monitor_index is not None and monitor_index < len(monitors) else monitors[0]
        self.m_width, self.m_height = target.width, target.height

        # 2. Setup Tkinter
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.display_window = tk.Toplevel(self.root)
        self.display_window.attributes('-fullscreen', True)
        self.display_window.config(cursor="none", bg="black") # Hide cursor for Kiosk mode
        
        self.image_label = tk.Label(self.display_window, bg='black')
        self.image_label.pack(expand=True, fill="both")

        self.shuffled_deck = []
        self.current_pil = None
        
        # Bindings
        self.display_window.bind("<Escape>", lambda e: self.root.quit())
        self.image_label.bind("<Button-1>", lambda e: self.root.quit())

    def get_processed_image(self):
        """Loads, resizes, and crops the next image to match screen dimensions."""
        if not self.shuffled_deck:
            self.shuffled_deck = self.all_images.copy()
            random.shuffle(self.shuffled_deck)

        image_path = os.path.join(self.folder_path, self.shuffled_deck.pop())
        
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB") # Ensure matching modes for blending
                img_aspect = img.width / img.height
                screen_aspect = self.m_width / self.m_height

                if img_aspect > screen_aspect:
                    # Wider than screen
                    new_h = self.m_height
                    new_w = int(new_h * img_aspect)
                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    x_offset = random.randint(0, new_w - self.m_width)
                    return resized.crop((x_offset, 0, x_offset + self.m_width, self.m_height))
                else:
                    # Taller than screen
                    new_w = self.m_width
                    new_h = int(new_w / img_aspect)
                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    y_offset = random.randint(0, new_h - self.m_height)
                    return resized.crop((0, y_offset, self.m_width, y_offset + self.m_height))
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return self.get_processed_image()

    def cross_fade(self, old_pil, new_pil, step=0):
        """Blends two images pixel-by-pixel for a smooth transition."""
        if step <= FADE_STEPS:
            alpha = step / FADE_STEPS
            # Core Logic: This replaces the window-level alpha fade
            blended = Image.blend(old_pil, new_pil, alpha)
            
            tk_img = ImageTk.PhotoImage(blended)
            self.image_label.config(image=tk_img)
            self.image_label.image = tk_img # Critical: Keep reference
            
            delay = int((FADE_DURATION / FADE_STEPS) * 1000)
            self.display_window.after(delay, self.cross_fade, old_pil, new_pil, step + 1)
        else:
            self.current_pil = new_pil
            # Wait for VIEW_TIME, then start next cycle
            self.display_window.after(VIEW_TIME * 1000, self.next_cycle)

    def next_cycle(self):
        new_pil = self.get_processed_image()
        if self.current_pil is None:
            # First run: no fade
            self.current_pil = new_pil
            tk_img = ImageTk.PhotoImage(new_pil)
            self.image_label.config(image=tk_img)
            self.image_label.image = tk_img
            self.display_window.after(VIEW_TIME * 1000, self.next_cycle)
        else:
            self.cross_fade(self.current_pil, new_pil)

    def run(self):
        self.next_cycle()
        self.root.mainloop()

def run_slideshow(folder_path, monitor_index):
    app = PiSlideshow(folder_path, monitor_index)
    app.run()

if __name__ == '__main__':
    run_slideshow(folder_path='local_cache', monitor_index=0)