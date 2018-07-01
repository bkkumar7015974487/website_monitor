from subprocess import run, PIPE

"""Read all vars from .env and set them in Heroku"""

with open('.env', 'r') as _file:
    for line in _file:
        line = line.rstrip('\n')
        cmd = ['heroku', 'config:set', line]
        run(cmd, stdout=PIPE, shell=True, universal_newlines=True)
