import os

DATA_DIR = "data" # directory for the saved website checks and diffs
CHECK_FILE_ENDING = ".check.html" # file ending of the website checks
DIFF_FILE_ENDING = ".diff.html" # file ending for the diff

if not 'DYNO' in os.environ:
    # if we do not start this tool via heroku, we need to
    # take care that the vars in .env are loaded
    from dotenv import load_dotenv
    load_dotenv(verbose=True, dotenv_path='.env')

# Max files keept in data dir. A check_file for a diff_file is
# always kept, even if MAX_CHECK_FILES was reached
MAX_DIFF_FILES = 5
MAX_CHECK_FILES = 5

APP_NAME = "Website Monitor"
