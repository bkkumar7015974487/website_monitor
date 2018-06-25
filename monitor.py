from timeit import default_timer
import asyncio
import time
import os
from urllib.parse import urlparse
import glob
import difflib
import sys
import hashlib

from path import Path
from bs4 import BeautifulSoup
from aiohttp import ClientSession

# page = requests.get('https://wow.curseforge.com/projects/keystroke-launcher')
# based on https://gist.github.com/dmahugh/b043ecbc4c61920aa685e0febbabb959

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
        print('{0:30}{1:5.2f}'.format(url, elapsed))

        os.makedirs("data", exist_ok=True)
        with Path("data"):
            # write new
            url_dir = urlparse(url).netloc
            timestamp = time.time()
            os.makedirs(f"{url_dir}", exist_ok=True)
            with open(f"{url_dir}/{timestamp}.txt", 'w', encoding="utf-8") as f:
                f.write(resp)

            # read
            with Path(url_dir):
                content_sorted = sorted(glob.glob(f"*.txt"))
                # print(content_sorted)
                # print(content_sorted[:-2])

                if len(content_sorted) > 1:
                    #file1 = open(content_sorted[-1], 'r')
                    #file2 = open(content_sorted[-2], 'r')
                    # parse html
                    hashes = []
                    for content_file in [ content_sorted[-2], content_sorted[-1] ]:
                        soup = BeautifulSoup(open(content_file, encoding="utf-8"), 'lxml')
                        cont = soup.select(".primary-content")[0]
                        hash = hashlib.md5(cont.encode('utf-8')).hexdigest()
                        hashes.append(hash)

                    if hashes[0] == hashes[1]:
                        print("--> No changes")
                    else:
                        print("--> Changes")

                    # print(hash1)
                    # for script in soup(["script", "style"]):
                    #     script.decompose()    # rip out script and style tags
                    # text = soup.get_text("\n", strip=True)


                    # print(f"Comparing from {content_sorted[-1]} to {content_sorted[-2]}")
                    # file1 = open(content_sorted[-1], 'r')
                    # file2 = open(content_sorted[-2], 'r')

                    #sys.stdout.writelines(difflib.context_diff(content_sorted[-1], content_sorted[-2]))

                    # diff = difflib.ndiff(file1.readlines(), file2.readlines())
                    # delta = ''.join(x[2:] for x in diff if x.startswith('- '))
                    # print(delta)

                    # diff = difflib.ndiff(file1.readlines(), file2.readlines())
                    # for l in diff:
                    #     print(l)

                    # html_diff = difflib.HtmlDiff()
                    # html = html_diff.make_file(file1.readlines(), file2.readlines())
                    # with open("out.html", 'w') as f:
                    #     f.write(html)

        return resp

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

if __name__ == '__main__':
    # URL_LIST = ['https://facebook.com',
    #             'https://github.com',
    #             'https://google.com',
    #             'https://microsoft.com',
    #             'https://yahoo.com']
    URL_LIST = ['https://wow.curseforge.com/projects/keystroke-launcher']
    demo_async(URL_LIST)
