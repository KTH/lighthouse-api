"""process.py

Util functions for working with command line calls"""

__author__ = 'tinglev@kth.se'

import subprocess
import logging

def run_with_output(cmd):
    try:
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
        logger.debug('Running command with output: "%s"', cmd)
        completed_process = subprocess.run(f'{cmd}', shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           close_fds=True)
        if completed_process.stderr:
            return completed_process.stderr
        return completed_process.stdout
    except subprocess.CalledProcessError as cpe:
        logger.error('Shell command gave error with output "%s"', str(cpe.output).rstrip('\n'))
        raise
