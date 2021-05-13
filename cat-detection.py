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
    UNINTERESTING = 'uninteresting'


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

def make_subdir(root, dirname):
    directory = root.joinpath(dirname)
    if not directory.exists():
        os.mkdir(directory)
    return directory

def main(check, interval, save_to, interest, categories):
    # Confirm that the provided save path and model paths are valid
    try:
        path_save = validate_path(save_to)
        print(f"Saving images to {save_to}")

        path_interest = validate_path(interest)
        print(f"Loading model from {interest}")

        path_categories = validate_path(categories)
        print(f"Loading model from {categories}")

    except Exception as err:
        print(err)
        exit()

    # Load Lobe models
    interest = ImageModel.load(path_interest)
    categories = ImageModel.load(path_categories)

    with picamera.PiCamera(resolution=(224, 224), framerate=30) as camera:

        # Create a subdirectory for uninteresting images
        path_uninteresting = make_subdir(path_save, 'uninteresting')

        # Read the list of labels from the category model directory
        # and create subdirectories for each label, save the path
        # references for later use
        save_paths = dict()
        with open(path_categories.joinpath('labels.txt'), 'r') as labels_file:
            labels = [line.strip() for line in labels_file.readlines()]
            for label in labels:
                save_paths[label] = make_subdir(path_save, label)

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
            result = interest.predict(img)
            label = result.prediction

            # if the image was predicted interesting, save it to the provided path
            # in a subdirectory based on the label predicted
            if label == Labels.INTERESTING:
                result = categories.predict(img)
                label = result.prediction
                save_filename = save_paths[label].joinpath(f"{time_stamp}.jpg")
                img.save(save_filename)
                camera.annotate_text = f"{label}\n{time_stamp}"
                time.sleep(interval)

            # if the image was predicted uninteresting, save it to a subdirectory
            # (for use to make the interesting/not-interesting model better)
            # and wait the interval set for uninteresting images
            elif label == Labels.UNINTERESTING:
                save_filename = path_uninteresting.joinpath(f"un-{time_stamp}.jpg")
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
        # interest: the directory that contains the interest checking model (default: ~/models/interest)
        # categories: the directory that contains the categorization model (default: ~/models/categories)
        # check: the interval to wait until checking for something interesting (default 60 seconds)
        # interval: the interval to wait between capturing an interesting image
        parser = argparse.ArgumentParser()
        parser.add_argument("path", nargs='?', help="Path to image save location", default=os.getcwd())
        parser.add_argument("interest", nargs='?', help="Path to interest model", default='~/models/interest')
        parser.add_argument("categories", nargs='?', help="Path to category model", default='~/models/categories')
        parser.add_argument("-c", "--check", required=False, help="Seconds between image checks", default=60, type=int)
        parser.add_argument("-i", "--interval", required=False, help="Seconds between image capture", default=1, type=int)
        args = parser.parse_args()

        print(f"Capture starting, to stop press \"CTRL+C\"")
        main(args.check, args.interval, args.path, args.interest, args.categories)

    except KeyboardInterrupt:
        print("")
        print(f"Caught interrupt, exiting...")
