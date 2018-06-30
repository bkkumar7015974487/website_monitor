from subprocess import run, PIPE

"""Store Heroki Sparkpost env variables in a local .env file.
Needed if you want to run the application also locally"""

env_keys = [
    'SPARKPOST_API_KEY',
    'SPARKPOST_API_URL',
    'SPARKPOST_SANDBOX_DOMAIN',
    'SPARKPOST_SMTP_HOST',
    'SPARKPOST_SMTP_PASSWORD',
    'SPARKPOST_SMTP_PORT',
    'SPARKPOST_SMTP_USERNAME'
]

with open('.env', 'w') as _file:
    for env_key in env_keys:
        cmd = ['heroku', 'config:get', env_key, '-s']
        print(f"Executing {' '.join(cmd)}")
        rv = run(cmd, stdout=PIPE, shell=True, universal_newlines=True)
        _file.write(rv.stdout)
