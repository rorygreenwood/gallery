# slideshow_robust.py

import logging
import os
import random
import tkinter as tk

from PIL import Image, ImageTk
from screeninfo import get_monitors

logger = logging.getLogger()
# --- Configuration ---
VIEW_TIME = 5
FADE_STEPS = 90  # Increased for smoother fade
FADE_DURATION = 2

LOCAL_CACHE = './local_cache/'

def run_slideshow(folder_path, monitor_index):
    """Displays a randomized slideshow using a robust Toplevel window."""
    # 1. Get Monitor Information
    monitors = get_monitors()
    for i, m in enumerate(monitors):
        logger.info(f"  Monitor {i}: {m}")

    if monitor_index is None:
        # Auto-detect secondary monitor if no index is provided
        target_monitor = next((m for m in monitors if not m.is_primary), monitors[0])
    else:
        try:
            target_monitor = monitors[monitor_index]
        except IndexError:
            logger.info('invalid monitor index')
            return

    # 2. Get and validate image files

    all_images = os.listdir(folder_path)
    if not all_images:
        logger.info(f"Error: No supported images found in '{folder_path}'")
        return

    # 3. Create the main, INVISIBLE root window
    root = tk.Tk()
    root.withdraw()  # This hides the main window

    # 4. Create the VISIBLE Toplevel window for display
    display_window = tk.Toplevel(root)
    display_window.title("Slideshow")

    m_width, m_height = target_monitor.width, target_monitor.height

    # Position the window on the target monitor *before* making it fullscreen
    display_window.geometry(f"+{target_monitor.x}+{target_monitor.y}")

    # Force tkinter to process the move before going fullscreen
    display_window.update()

    # Set geometry and make it a borderless, fullscreen window
    display_window.attributes('-fullscreen', True)

    # More aggressive methods to keep it on top
    display_window.lift()
    display_window.focus_force()

    image_label = tk.Label(display_window, bg='black')
    image_label.pack(expand=True, fill="both")

    shuffled_deck = []
    fade_step_delay = int((FADE_DURATION / FADE_STEPS) * 1000)

    def load_next_image():
        nonlocal shuffled_deck
        if not shuffled_deck:
            shuffled_deck = all_images.copy()
            random.shuffle(shuffled_deck)

        # Pop a filename and create the full path
        image_name = shuffled_deck.pop()
        image_path = os.path.join(folder_path, image_name)

        try:
            original = Image.open(image_path)

            img_w, img_h = original.width, original.height
            img_aspect = img_w / img_h
            screen_aspect = m_width / m_height

            # This is the new "cover" logic
            if img_aspect > screen_aspect:
                # Image is WIDER than the screen (e.g., 16:9 image on 4:3 screen)
                # Scale based on height, so the width overflows
                new_h = m_height
                new_w = int(new_h * img_aspect)

                resized = original.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # Pick a random horizontal (x) position to crop from
                max_x = new_w - m_width
                crop_x = random.randint(0, max_x)

                # Crop a screen-sized portion
                cropped = resized.crop((crop_x, 0, crop_x + m_width, m_height))

            else:
                # Image is TALLER than the screen (e.g., 9:16 image on 16:9 screen)
                # Scale based on width, so the height overflows
                new_w = m_width
                new_h = int(new_w / img_aspect)

                resized = original.resize((new_w, new_h), Image.Resampling.LANCZOS)

                # Pick a random vertical (y) position to crop from
                max_y = new_h - m_height
                crop_y = random.randint(0, max_y)

                # Crop a screen-sized portion
                cropped = resized.crop((0, crop_y, m_width, crop_y + m_height))

            tk_image = ImageTk.PhotoImage(cropped)
            image_label.config(image=tk_image)
            image_label.image = tk_image
            logger.info(f"Displaying: {image_name}")

        except Exception as e:
            logger.info(f"Could not load image {image_name}: {e}")
            # Use .after() to avoid deep recursion on multiple bad images
            display_window.after(100, load_next_image)

    def fade(step, direction):
        alpha = (FADE_STEPS - step) / FADE_STEPS if direction == 'out' else step / FADE_STEPS
        display_window.attributes("-alpha", alpha)
        if step < FADE_STEPS:
            display_window.after(fade_step_delay, fade, step + 1, direction)
        else:
            if direction == 'out':
                load_next_image()
                fade(step=0, direction='in')
            else:
                display_window.after(VIEW_TIME * 1000, fade, 0, 'out')

    def start():
        load_next_image()
        display_window.attributes("-alpha", 1.0)
        display_window.after(VIEW_TIME * 1000, fade, 0, 'out')

    def close_window(event=None):
        root.quit()

    display_window.bind("<Escape>", close_window)
    image_label.bind("<Button-1>", close_window)
    start()
    root.mainloop()
