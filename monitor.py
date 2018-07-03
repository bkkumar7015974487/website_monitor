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
import notifier
from website import Website

""" async and aiohttp based on https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959 """

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def start():
    """Fetch list of web pages asynchronously."""
    websites = Website.all()
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
        helper.p(f"{response.status} {elapsed:5.2f}s {website.name:25} {website.url} {website.css_selector}")

        os.makedirs(conf.DATA_DIR, exist_ok=True)
        with Path(conf.DATA_DIR):
            #
            # WRITE NEW CHECK FILE
            #
            timestamp = time.time()
            os.makedirs(website.slug, exist_ok=True)
            check_file_name = f"{website.slug}/{timestamp}{conf.CHECK_FILE_ENDING}"
            with open(check_file_name, 'w', encoding="utf-8") as f:
                f.write(resp)
            check_file = website.add_check_file(check_file_name)

            #
            # DIFF ALL CHECK FILES
            #
            with Path(website.slug):
                content_sorted = sorted(glob.glob(f"*{conf.CHECK_FILE_ENDING}"))

                if len(content_sorted) > 1:
                    # this means we have save an old version, compare it to the most recent one

                    # first check if there was a change at all by comparing cecksums
                    hashes = []
                    for content_file in [ content_sorted[-2], content_sorted[-1] ]:
                        soup = BeautifulSoup(open(content_file, encoding="utf-8"), 'lxml')
                        for script in soup(["script", "style", "ins", "del"]):
                            # strip out some tags
                            script.decompose()

                        if website.css_selector:
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
                    helper.p(f"Check diff between {hashes[0]['file_name']} and {hashes[1]['file_name']}:")

                    #
                    # CHECK RULES AND DECIDE IF TO CREATE A DIFF
                    #
                    do_diff = []
                    do_diff_threshold = []
                    ins_del_tags = ('').join([el.get_text() for el in bs_diff.find_all(['ins', 'del'])])
                    if len(ins_del_tags) > 0:
                        # per default, we always create diff if there was any change at all
                        do_diff = 'True'
                        # now we check the configures threshold
                        for tag in ['ins', 'del']:
                            for typee in ['numbers', 'letters']:
                                s = ('').join([el.get_text() for el in bs_diff.find_all(tag)])
                                count = 0
                                if typee == 'numbers':
                                    count = sum(c.isdigit() for c in s)
                                elif typee == 'letters':
                                    count = sum(c.isalpha() for c in s)
                                helper.p(f"--> {tag} {typee} count is {count}")
                                if count > 0:
                                    # only actually do anything if for this tag/type was a change
                                    threshold = website.get_threshold(tag, typee)
                                    helper.p(f"--> {tag} {typee} threshold is {threshold}")
                                    if threshold == 0:
                                        # 0 is the default value if there was nothing configured
                                        #do_diff.extend(['True', 'or'])
                                        do_diff_threshold.append('True')
                                        helper.p(f"--> {tag} {typee} TRUE because threshold == 0")
                                    elif threshold < 0:
                                        # a negative value means, that a change of this type is ignored completely
                                        do_diff_threshold.append('False')
                                        helper.p(f"--> {tag} {typee} FALSE because threshold < 0")
                                    else:
                                        # a positive value, let's check it agains the actual count
                                        if count < threshold:
                                            # there was a change, but the amount is too low
                                            do_diff_threshold.append('False')
                                            helper.p(f"--> {tag} {typee} FALSE because count ({count}) < threshold ({threshold})")
                                        else:
                                            do_diff_threshold.append('True')
                                            helper.p(f"--> {tag} {typee} TRUE because count ({count}) > threshold ({threshold})")
                        do_diff_threshold = "(" + " or ".join(do_diff_threshold) + ")" # merge by OR, because one TRUE is enough to create a diff

                        do_diff = " and ".join([do_diff, do_diff_threshold]) # merge by AND, because a FALSE in the detailed check overwrites the genreal TRUE
                        helper.p(f"--> Summary: {do_diff} evals to {eval(do_diff)}")

                    if do_diff and eval(do_diff):
                        #
                        # WRITE DIFF FILE
                        #
                        diff_file_name = f"{hashes[1]['file_name']}{conf.DIFF_FILE_ENDING}"
                        helper.p(f"writing diff to {diff_file_name}")
                        with open(diff_file_name, 'w', encoding="utf-8") as f:
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
                        diff_file = check_file.add_diff_file(diff_file_name)
                        website.notify(html=f"<a href={diff_file.url}>diff</a>")
                    else:
                        helper.p("no change detected")
        return resp

if __name__ == '__main__':
    start()
