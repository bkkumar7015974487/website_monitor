from timeit import default_timer
import asyncio
import time
import os
import glob
import difflib
import sys
import hashlib

from path import Path
from bs4 import BeautifulSoup
from aiohttp import ClientSession
from lxml.html.diff import htmldiff

import helper
import conf

""" async and aiohttp based on https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959 """

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def demo_async(config_urls):
    """Fetch list of web pages asynchronously."""
    start_time = default_timer()

    loop = asyncio.get_event_loop() # event loop
    future = asyncio.ensure_future(fetch_all(config_urls)) # tasks to do
    loop.run_until_complete(future) # loop until done

    tot_elapsed = default_timer() - start_time
    print('Total time: {0:5.2f}'.format(tot_elapsed))

async def fetch_all(config_urls):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict() # dictionary of start times for each url
    async with ClientSession() as session:
        for url_name, url_config in config_urls.items():
            task = asyncio.ensure_future(fetch(url_name, url_config, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses

async def fetch(url_name, url_config, session):
    """Fetch a url, using specified ClientSession."""
    fetch.start_time[url_name] = default_timer()
    async with session.get(url_config['url']) as response:
        resp = await response.text()
        elapsed = default_timer() - fetch.start_time[url_name]
        print(f"{response.status} {elapsed:5.2f} {url_name:25}s {url_config['url']}")

        os.makedirs(conf.DATA_DIR, exist_ok=True)
        with Path(conf.DATA_DIR):
            # write new
            url_dir = helper.get_valid_filename(url_name)
            timestamp = time.time()
            os.makedirs(f"{url_dir}", exist_ok=True)
            with open(f"{url_dir}/{timestamp}{conf.CHECK_FILE_ENDING}", 'w', encoding="utf-8") as f:
                f.write(resp)

            # read
            with Path(url_dir):
                content_sorted = sorted(glob.glob(f"*{conf.CHECK_FILE_ENDING}"))

                if len(content_sorted) > 1:
                    # this means we have save an old version, compare it to the most recent one

                    # first check if there was a change at all by comparing cecksums
                    hashes = []
                    for content_file in [ content_sorted[-2], content_sorted[-1] ]:
                        helper.dprint(f"file: {content_file}")
                        soup = BeautifulSoup(open(content_file, encoding="utf-8"), 'lxml')
                        for script in soup(["script", "style"]):
                            script.decompose()

                        if 'css_selector' in url_config:
                            css_selector = url_config['css_selector']
                            helper.dprint(f"css_selector: {css_selector}")
                            cont = soup.select(css_selector)
                            if len(cont) > 1:
                                sys.exit('!! selector not unique')
                            if not cont:
                                sys.exit(f"!! selector '{css_selector}' no results")
                            cont = cont[0]
                        else:
                            cont = soup.html()

                        hashes.append({
                            'file_name': content_file.rstrip(conf.CHECK_FILE_ENDING),
                            'cont': str(cont)
                            })

                    # hashes[0] = old version
                    # hashes[1] = new version

                    diff = htmldiff(hashes[0]['cont'], hashes[1]['cont'])
                    bs_diff = BeautifulSoup(diff, 'lxml')
                    ins_del = bs_diff.find_all(['ins', 'del'])
                    if ins_del:
                        diff = htmldiff(hashes[0]['cont'], hashes[1]['cont'])
                        diff_file = f"{hashes[0]['file_name']}_to_{hashes[1]['file_name']}_{conf.DIFF_FILE_ENDING}"
                        print(f"?? change detected, writing diff to {diff_file}")
                        with open(diff_file, 'w', encoding="utf-8") as f:
                            f.write(diff)
                    else:
                        helper.dprint("no change detected")
        return resp

if __name__ == '__main__':
    #demo_async(helper.get_config_urls())
    while True:
        demo_async(helper.get_config_urls())
        time.sleep(60)

