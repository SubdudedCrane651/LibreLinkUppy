import sys
import os
import time
import pygame
from gtts import gTTS

def parse_input():
    args = sys.argv[1:]
    language = "en"
    text_list = []

    # No arguments → play default audio
    if not args:
        return language, None, True

    # Handle --lang=xx
    if args[0].startswith("--lang="):
        language = args[0].split("=")[1]
        args = args[1:]  # remove the lang argument

    # Handle --in filename
    if args and args[0] == "--in":
        filename = args[1]
        with open(filename, "r", encoding="utf-8") as f:
            text_list = f.readlines()
        return language, text_list, False

    # Otherwise treat remaining args as text
    text_list = [" ".join(args)]
    return language, text_list, False

def safe_delete(path):
    """Try to delete a file with retries (Windows-safe)."""
    for _ in range(30):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except PermissionError:
            time.sleep(0.1)

def speak_chunks(mytext, language="en"):
    base = os.path.dirname(__file__)
    files = []
    count = 0

    # Initialize pygame ONCE
    pygame.mixer.init()

    for text in mytext:
        text = text.strip()
        if not text:
            continue

        print(text)

        audio_file = os.path.join(base, f"speak_{count}.mp3")
        files.append(audio_file)

        # Delete old file if exists
        safe_delete(audio_file)

        # Create NEW gTTS object each time
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(audio_file)

        # Play audio
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        # Wait for playback
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        count += 1

    # Release ALL locks
    pygame.mixer.music.stop()
    pygame.mixer.quit()

        # Delete all files safely
    for f in files:
        safe_delete(f)
   
language, mytext, play_default = parse_input()
speak_chunks(mytext, language)
