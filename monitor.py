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

import helper
import conf
import notifier
from website import Website, CheckFile, DiffFile

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

        # WRITE NEW CHECK FILE
        check_file = CheckFile(website).create(resp)
        website.add_check_file(check_file)

        if len(website.check_files) > 1:
            # DIFF LAST TWO CHECK FILES
            bs_diff, diff = website.get_diff()

            # CHECK RULES AND DECIDE IF TO CREATE A DIFF
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
                # WRITE DIFF FILE
                content = """
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
                """
                content += diff
                diff_file = check_file.create_diff_file(content)

                # notify for change
                diff_file.notify()
            else:
                helper.p("no change detected")
        return resp

if __name__ == '__main__':
    start()
