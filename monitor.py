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
import numpy

import helper
import conf
import notifier

""" async and aiohttp based on https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959 """

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def start():
    """Fetch list of web pages asynchronously."""
    websites = helper.get_all_websites()
    start_time = default_timer()

    loop = asyncio.new_event_loop() # create event loop
    asyncio.set_event_loop(loop) # set event loop
    future = asyncio.ensure_future(fetch_all(websites)) # tasks to do
    loop.run_until_complete(future) # loop until done

    tot_elapsed = default_timer() - start_time
    helper.p('Total time: {0:5.2f}'.format(tot_elapsed))

async def fetch_all(websites):
    """Launch requests for all web pages."""
    tasks = []
    fetch.start_time = dict() # dictionary of start times for each url
    async with ClientSession() as session:
        for website in websites:
            task = asyncio.ensure_future(fetch(website, session))
            tasks.append(task) # create list of tasks
        _ = await asyncio.gather(*tasks) # gather task responses

async def fetch(website, session):
    """Fetch a url, using specified ClientSession."""
    fetch.start_time[website.slug] = default_timer()
    async with session.get(website.url) as response:
        resp = await response.text()
        elapsed = default_timer() - fetch.start_time[website.slug]
        helper.p(f"{response.status} {elapsed:5.2f}s {website.name:25} {website.url}")

        os.makedirs(conf.DATA_DIR, exist_ok=True)
        with Path(conf.DATA_DIR):
            # write new
            timestamp = time.time()
            os.makedirs(website.slug, exist_ok=True)
            with open(f"{website.slug}/{timestamp}{conf.CHECK_FILE_ENDING}", 'w', encoding="utf-8") as f:
                f.write(resp)

            # read
            with Path(website.slug):
                content_sorted = sorted(glob.glob(f"*{conf.CHECK_FILE_ENDING}"))

                if len(content_sorted) > 1:
                    # this means we have save an old version, compare it to the most recent one

                    # first check if there was a change at all by comparing cecksums
                    hashes = []
                    for content_file in [ content_sorted[-2], content_sorted[-1] ]:
                        helper.p(f"file: {content_file}")
                        soup = BeautifulSoup(open(content_file, encoding="utf-8"), 'lxml')
                        for script in soup(["script", "style", "ins", "del"]):
                            # strip out some tags
                            script.decompose()

                        if website.css_selector:
                            helper.p(f"css_selector: {website.css_selector}")
                            cont = soup.select(website.css_selector)
                            if len(cont) > 1:
                                sys.exit('!! selector not unique')
                            if not cont:
                                sys.exit(f"!! selector '{website.css_selector}' no results")
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

                    # check if diff
                    helper.p("Check if diff:")
                    do_diff = []
                    for tag in ['ins', 'del']:
                        s = ('').join([el.get_text() for el in bs_diff.find_all(tag)])
                        for typee in ['numbers', 'letters', 'spaces', 'other']:
                            count = sum(c.isdigit() for c in s)
                            threshold = website.get_threshold(tag, typee)
                            if threshold == -1:
                                # never trigger change based on this
                                helper.p(f"  {tag} {typee} FALSE because threshold=-1")
                                do_diff.append(False)
                            elif threshold == 0:
                                # ignore this value completely
                                pass
                            elif threshold > 0:
                                if count > threshold:
                                    helper.p(f"  {tag} {typee} TRUE because count ({count}) > threshold ({threshold})")
                                    do_diff.append(True)
                                else:
                                    helper.p(f"  {tag} {typee} FALSE because count ({count}) < threshold ({threshold})")
                                    do_diff.append(False)
                    helper.p(f"Summary: {do_diff}")

                    if numpy.any(do_diff):
                        diff_file = f"{hashes[0]['file_name']}_to_{hashes[1]['file_name']}_{conf.DIFF_FILE_ENDING}"
                        helper.p(f"?? change detected, writing diff to {diff_file}")
                        with open(diff_file, 'w', encoding="utf-8") as f:
                            f.write("""
                            <style>
                                ins {
                                    text-decoration: none;
                                    background-color: #d4fcbc;
                                    color: black;
                                    font-size: 22;
                                }

                                del {
                                    text-decoration: line-through;
                                    background-color: #fbb6c2;
                                    color: #555;
                                    font-size: 18;
                                }
                                body {
                                    color: lightgray;
                                }
                                a {
                                    color: lightgray;
                                }
                            </style>
                            """)
                            f.write(diff)
                        website.notify(text=f"<a href=http://{helper.gethostname()}/url/{website.slug}>/diff/{diff_file}>diff</a>")
                    else:
                        helper.p("no change detected")
        return resp

if __name__ == '__main__':
    start()
