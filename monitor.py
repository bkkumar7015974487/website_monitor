from timeit import default_timer
import asyncio
import time
import os
from urllib.parse import urlparse
import glob
import difflib
import sys
import hashlib

import yaml
from path import Path
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from lxml.html.diff import htmldiff

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# async and aiohttp based on https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959

def demo_async(urls):
    """Fetch list of web pages asynchronously."""
    start_time = default_timer()

    loop = asyncio.get_event_loop() # event loop
    future = asyncio.ensure_future(fetch_all(urls)) # tasks to do
    loop.run_until_complete(future) # loop until done

    tot_elapsed = default_timer() - start_time
    print('Total time: {0:5.2f}'.format(tot_elapsed))

async def fetch_all(urls):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict() # dictionary of start times for each url
    async with ClientSession() as session:
        for url in urls:
            task = asyncio.ensure_future(fetch(url, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses

async def fetch(url, session):
    """Fetch a url, using specified ClientSession."""
    fetch.start_time[url] = default_timer()
    async with session.get(url) as response:
        resp = await response.text()
        elapsed = default_timer() - fetch.start_time[url]
        print(f'{url} {response.status} {elapsed:5.2f}')

        os.makedirs("data", exist_ok=True)
        with Path("data"):
            # write new
            url_dir = urlparse(url).netloc + urlparse(url).path
            url_dir = url_dir.replace("/", '_')
            timestamp = time.time()
            os.makedirs(f"{url_dir}", exist_ok=True)
            with open(f"{url_dir}/{timestamp}.txt", 'w', encoding="utf-8") as f:
                f.write(resp)

            # read
            with Path(url_dir):
                content_sorted = sorted(glob.glob(f"*.txt"))

                if len(content_sorted) > 1:
                    # this means we have save an old version, compare it to the most recent one

                    # first check if there was a change at all by comparing cecksums
                    hashes = []
                    for content_file in [ content_sorted[-2], content_sorted[-1] ]:
                        dprint(f"file: {content_file}")
                        soup = BeautifulSoup(open(content_file, encoding="utf-8"), 'lxml')
                        for script in soup(["script", "style"]):
                            script.decompose()

                        css_selector = get_css_selector(url)
                        if css_selector:
                            dprint(f"css_selector: {css_selector}")
                            cont = soup.select(css_selector)
                            if len(cont) > 1:
                                sys.exit('!! selector not unique')
                            if not cont:
                                sys.exit('!! selector no results')
                            cont = cont[0]
                        else:
                            cont = soup.html()

                        hashes.append({'cont': str(cont)})

                    # hashes[0] = old version
                    # hashes[1] = new version

                    diff = htmldiff(hashes[0]['cont'], hashes[1]['cont'])
                    bs_diff = BeautifulSoup(diff, 'lxml')
                    ins_del = bs_diff.find_all(['ins', 'del'])
                    if ins_del:
                        print("?? change detected, writing diff.html")
                        diff = htmldiff(hashes[0]['cont'], hashes[1]['cont'])
                        with open(f"diff.html", 'w', encoding="utf-8") as f:

                            f.write("""\
                            <!DOCTYPE html>
                            <html>
                            <head>
                            <style>
                                ins {background-color: lightgreen;}
                                del {background-color: LightPink ;}
                            </style>
                            </head>
                            <body>
                            """)
                            f.write(diff)
                            f.write("""\
                            </body>
                            </html>
                            """)
                    else:
                        dprint("no change detected")
        return resp

def dprint(msg):
    #print(f"   {msg}")
    pass

def get_css_selector(url):
    with open(f"{BASE_PATH}/conf.yaml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if 'css_selector' in cfg['urls'][url]:
        return cfg['urls'][url]['css_selector']

if __name__ == '__main__':
    with open(f"{BASE_PATH}/conf.yaml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    urls = [ el for el in cfg['urls'] ]

    while True:
        demo_async(urls)
        time.sleep(60*5)

