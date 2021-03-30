'''download image'''
import configparser # Read config file.
import os # Just os module?
import logging # Logging errors.
from pathlib import Path # Create a directory if needed.
import urllib.request # Download image.
import shutil # Clear directory.

def get_image(image_url, isbn):
    '''Get api request'''

    current_dir = (os.path.dirname(os.path.realpath(__file__)))
    Path(os.path.join(current_dir, "logs")).mkdir(parents=True, exist_ok=True)
    logging_path = os.path.join(current_dir, "logs", "image.log")

    logging.basicConfig(filename=logging_path, level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger=logging.getLogger(__name__)

    config = configparser.ConfigParser()
    config.read(os.path.join(current_dir, 'config', 'conf.ini'))
    image_folder = config.get("General", "image_folder")

    try:
        image_path = os.path.join(current_dir, image_folder)
        image_path = Path(image_path)
        if image_path.exists() and image_path.is_dir():
            shutil.rmtree(image_path)
        Path(image_path).mkdir(parents=True, exist_ok=True)

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

    try:
        request = urllib.request.urlretrieve(image_url, os.path.join(image_path, str(isbn)+".jpg"))
        if request[0]:
            return request[0]

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

    return None
