# slideshow_robust.py

import tkinter as tk
from PIL import Image, ImageTk
from screeninfo import get_monitors
import sys
import os
import random
import argparse  # Added for monitor selection
import logging

logger = logging.getLogger()
# --- Configuration ---
VIEW_TIME = 5
FADE_STEPS = 90  # Increased for smoother fade
FADE_DURATION = 2


def get_image_files(folder_path):
    """Returns a list of paths for all supported image files in a folder."""
    supported_formats = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if any(f.lower().endswith(ext) for ext in supported_formats)
    ]


def run_slideshow(folder_path, monitor_index):
    """Displays a randomized slideshow using a robust Toplevel window."""
    # 1. Get Monitor Information
    monitors = get_monitors()
    logger.info("🔎 Detecting Monitors...")
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
    all_images = get_image_files(folder_path)
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
        # (This function remains the same as before)
        nonlocal shuffled_deck
        if not shuffled_deck:
            shuffled_deck = all_images.copy()
            random.shuffle(shuffled_deck)
        image_path = shuffled_deck.pop()
        try:
            original = Image.open(image_path)
            img_aspect = original.width / original.height
            screen_aspect = m_width / m_height
            if img_aspect > screen_aspect:
                new_w, new_h = m_width, int(m_width / img_aspect)
            else:
                new_w, new_h = int(m_height * img_aspect), m_height
            resized = original.resize((new_w, new_h), Image.Resampling.LANCZOS)
            tk_image = ImageTk.PhotoImage(resized)
            image_label.config(image=tk_image)
            image_label.image = tk_image
            logger.info(f"Displaying: {os.path.basename(image_path)}")
        except Exception as e:
            logger.info(f"⚠️ Could not load image {os.path.basename(image_path)}: {e}")
            load_next_image()

    def fade(step, direction):
        # (This function remains the same as before)
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
        root.quit()  # Use quit() for the hidden root window

    display_window.bind("<Escape>", close_window)
    image_label.bind("<Button-1>", close_window)

    logger.info(f"Found {len(all_images)} images. Starting slideshow...")
    start()
    root.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fullscreen image slideshow.")
    parser.add_argument("folder", help="Path to the image folder.")
    parser.add_argument(
        "--monitor",
        type=int,
        help="The index of the monitor to display on (e.g., 0, 1)."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        logger.info(f"Error: Folder not found at '{args.folder}'")
        sys.exit(1)

    run_slideshow(args.folder, args.monitor)