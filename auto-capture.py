#!/usr/bin/env python3

import argparse
import io
import os
import time
import pathlib
from datetime import datetime

import picamera
from PIL import Image


def main(interval, save_path):

    # Confirm that the provide save path is a valid path
    try:
        path = pathlib.Path(save_path)
        if not path.exists():
            raise FileNotFoundError("Not a valid path")

        if not path.is_dir():
            raise NotADirectoryError("Path is not a directory")

    except Exception as e:
        print(f"Unable to save to {save_path}, {e}")
        exit()

    with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:

        stream = io.BytesIO()
        camera.start_preview()

        # Camera warm-up time
        time.sleep(2)

        while True:
            camera.annotate_text = "Ready..."
            stream.seek(0)

            time_stamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            image_name = path.joinpath(f"{time_stamp}.jpg")

            camera.annotate_text = None
            camera.capture(stream, format='jpeg')
            img = Image.open(stream)
            img.save(image_name)

            camera.annotate_text = f"Saved at:\n{time_stamp}"
            print(f"Saved image to: {image_name}")

            time.sleep(interval)


if __name__ == '__main__':
    try:
        print(f"Capture starting, to stop press \"CTRL+C\"")

        # Accept arguments on the command line for the
        # interval between image captures, and the path
        # to save captured images to. Default to saving
        # in the current directory every 10 seconds
        parser = argparse.ArgumentParser()
        parser.add_argument("path", nargs="?", help="Path to image save location", default=os.getcwd())
        parser.add_argument("-i", "--interval", required=False, help="Seconds between image capture", default=10, type=int)
        args = parser.parse_args()

        main(args.interval, args.path)

    except KeyboardInterrupt:
        print("")
        print(f"Caught interrupt, exiting...")
