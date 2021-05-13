#!/usr/bin/env python3

import argparse
import io
import os
import pathlib
import time
from datetime import datetime
from enum import Enum

import picamera
from PIL import Image
from lobe import ImageModel


class Labels(str, Enum):
    INTERESTING = 'interesting'
    NOT_INTERESTING = 'not interesting'


def validate_path(path_string):
    # accept a path string and confirm that it
    # both exists and is a directory
    try:
        path = pathlib.Path(path_string).expanduser()
        if not path.exists():
            raise FileNotFoundError("not a valid path")
        if not path.is_dir():
            raise NotADirectoryError("path is not a directory")
        return path
    except Exception as e:
        raise Exception(f"Unable to save to {path_string}, {e}")


def main(check, interval, save_path, model_path):
    # Confirm that the provided save path and model paths are valid
    try:
        path_save = validate_path(save_path)
        print(f"Saving images to {save_path}")

        path_model = validate_path(model_path)
        print(f"Loading models from {model_path}")

    except Exception as err:
        print(err)
        exit()

    # Load Lobe model
    model = ImageModel.load(path_model)
    with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:

        # Start camera preview
        stream = io.BytesIO()
        camera.start_preview()

        # Camera warm-up time
        time.sleep(2)

        while True:

            # Start stream at the first byte
            stream.seek(0)

            time_stamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

            # Clear the last prediction text
            # and capture an image from the camera
            camera.annotate_text = None
            camera.capture(stream, format='jpeg')
            img = Image.open(stream)

            # Run inference on the image
            result = model.predict(img)
            label = result.prediction
            confidence = result.labels[0][1]

            # Add label text to camera preview
            camera.annotate_text = f"{label}\n{confidence}\n{time_stamp}"

            # if the image was predicted interesting, save it to the provided path
            # and wait the interval set for interesting images
            if label == Labels.INTERESTING:
                save_filename = path_save.joinpath(f"{time_stamp}.jpg")
                img.save(save_filename)
                time.sleep(interval)

            # if the image was predicted uninteresting, save it to a sub-directory
            # (for use to make the interesting/not-interesting model better)
            # and wait the interval set for uninteresting images
            elif label == Labels.NOT_INTERESTING:
                if not path_save.joinpath('uninteresting').exists():
                    os.mkdir(path_save.joinpath('uninteresting'))
                save_filename = path_save.joinpath('uninteresting').joinpath(f"un-{time_stamp}.jpg")
                img.save(save_filename)
                time.sleep(check)

            # if some other label is predicted, there's a problem with the model
            # print something out and exit execution
            else:
                print(f"Unexpected result: {label}")
                exit()


if __name__ == '__main__':

    try:
        # Set the script to accept arguments
        # path: the directory to save captured images in (default: current directory)
        # model: the directory that contains the Tensor Light model (default: ~/model)
        # check: the interval to wait until checking for something interesting (default 60 seconds)
        # interval: the interval to wait between capturing an interesting image
        parser = argparse.ArgumentParser()
        parser.add_argument("path", nargs='?', help="Path to image save location", default=os.getcwd())
        parser.add_argument("model", nargs='?', help="Path to Tensor Light model", default='~/model')
        parser.add_argument("-c", "--check", required=False, help="Seconds between image checks", default=60, type=int)
        parser.add_argument("-i", "--interval", required=False, help="Seconds between image capture", default=1, type=int)
        args = parser.parse_args()

        print(f"Capture starting, to stop press \"CTRL+C\"")
        main(args.check, args.interval, args.path, args.model)

    except KeyboardInterrupt:
        print("")
        print(f"Caught interrupt, exiting...")
