__author__ = 'tinglev@kth.se'

import os

def get_lighthouse_image():
    return os.getenv('LIGHTHOUSE_IMAGE')

def get_storage_conn_string():
    return os.getenv('STORAGE_CONN_STRING')