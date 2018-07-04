import os
import helper

DATA_DIR = "data" # directory for the saved website checks and diffs
CHECK_FILE_ENDING = ".check.html" # file ending of the website checks
DIFF_FILE_ENDING = ".diff.html" # file ending for the diff

if not 'DYNO' in os.environ:
    from dotenv import load_dotenv
    load_dotenv(verbose=True, dotenv_path='.env')

MAX_DIFF_FILES = 5
MAX_CHECK_FILES = 5

APP_NAME = "Website Monitor"
