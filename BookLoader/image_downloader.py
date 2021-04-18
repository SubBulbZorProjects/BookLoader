'''download image'''
import configparser  # Read config file.
import glob  # Filename globing utility.
import logging  # Logging errors.
import os  # Just os module?
import shutil  # Clear directory.
from pathlib import Path  # Create a directory if needed.

import requests  # Download image.
import requests_cache  # Cache scrapped image.


def get_image(image_url, isbn):
    '''Get api request'''

    current_dir = (os.path.dirname(os.path.realpath(__file__)))

    Path(os.path.join(current_dir, "logs")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(current_dir, "cache")).mkdir(parents=True, exist_ok=True)

    logging_path = os.path.join(current_dir, "logs", "image.log")
    cache = os.path.join(current_dir, "cache", "scraper_cache")

    logging.basicConfig(filename=logging_path, level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger=logging.getLogger(__name__)

    config = configparser.ConfigParser()
    config.read(os.path.join(current_dir, 'config', 'conf.ini'))
    image_folder = config.get("General", "image_folder")

    requests_cache.install_cache(cache, backend='sqlite', expire_after=300)

    try:
        image_path = os.path.join(current_dir, image_folder)
        image_path = Path(image_path)
        image_files = glob.glob(os.path.join(image_path, "*"))
        if image_path.exists() and image_path.is_dir():
            for image in image_files:
                try:
                    Path(image).unlink()
                except OSError as error:
                    print("Error: %s : %s" % (image, error.strerror))

        else:
            Path(image_path).mkdir(parents=True, exist_ok=True)

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

    try:
        path = os.path.join(image_path, str(isbn)+".jpg")
        request = requests.get(image_url, stream=True)

        if request.status_code == 200:
            with open(path, 'wb') as file:
                request.raw.decode_content = True
                shutil.copyfileobj(request.raw, file)
                # print(request.from_cache)
                return path

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

    return None
