'''WordPress API integrator'''
import base64  # Data encodings.
import configparser  # Read config file.
import inspect  # Get function name.
import logging  # Logging errors.
import os  # Just os module?
from pathlib import Path  # Create a directory if needed.similarity.

import requests  # Requests HTTP Library.

current_dir = (os.path.dirname(os.path.realpath(__file__)))
Path(os.path.join(current_dir, "logs")).mkdir(parents=True, exist_ok=True)
logging_path = os.path.join(current_dir, "logs", "WP.log")

# DEBUG -> WARNING :
logging.basicConfig(filename=logging_path, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class WordPress: # pylint: disable=too-few-public-methods
    '''WordPress class'''
    def __init__(self, image):
        '''init WordPress class'''
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
        self.wp_url = config.get("WordPress", "url")
        self.wp_user = config.get("WordPress", "user")
        self.wp_pass = config.get("WordPress", "password")
        self.token = base64.standard_b64encode((self.wp_user + ':' + self.wp_pass).encode('utf-8'))
        self.header = {'Authorization': 'Basic ' + self.token.decode('utf-8')}
        self.image = image
        self.error_codes = [401, 404, 500]
        self.error_catch = []

    def post_wp_image(self):
        '''Get WordPress api request'''
        try:
            media = {'file': open(self.image,'rb')}

            response = requests.post(self.wp_url + '/media', headers=self.header, files=media)

            # Send none if status code found in error codes
            if int(response.status_code) in self.error_codes:
                self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                return None

            image_path = response.json()["guid"]["raw"]
        except Exception as error: # pylint: disable=broad-except
            logger.info(error)
        return image_path

def main(image):
    '''Upload image to WordPress media'''
    media = WordPress(image=image)
    request = media.post_wp_image()
    return request
