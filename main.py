# -*- coding: UTF-8 -*-

import cookielib
import urllib3
import socket
import re
from bs4 import BeautifulSoup as bsp
import Queue
import signal
import sys

#only grab name as number as threshold
name_threshold = 5000
force_quit = 0

def signal_handler(sig, frame):
    global force_quit
    print('[Ctrl+C]')
    force_quit = 1
    

def _grab_one_req_(html_data, unique_name_set, unique_url_set, global_url_set):
    html_text=""

    global name_threshold
    
    #if get done
    if html_data.status == 200:
        print("len=%d, current name number=%d"%(len(html_data.data), len(unique_name_set)) )
        html_text = html_data.data
        # print("header:%s"%(html_data.headers) )
    
    #parse html to find <a>url</a>
    soup = bsp(html_text, "html.parser", from_encoding="utf-8")
    
    #get all links
    links = soup.find_all('a', href=re.compile(r"^http") )
    
    for link in links:
        cur_link = link['href']
        
        #skip url in global_url_set
        if not cur_link in global_url_set or len(global_url_set) == 0:
            unique_url_set.add(link['href'])
            global_url_set.add(link['href'])

            match = re.search(r'^http[s]?:\/\/(.*)', cur_link, re.I)
            if match is not None:
                name = re.sub(r'[\?\_\.\-\=\#]', '/', match.group(1), 0)

                zhre = re.compile('[\u4e00-\u9fa5]+')

                #code conver
                u_name = u''.join(name).encode('utf-8').strip()

                name_match_zh = zhre.search(u_name) 

                #filter names with chinese char 
                if name_match_zh:
                    # print(name_match_zh.group(0))
                    pass
                else:
                    if(len(unique_name_set) == name_threshold):
                        return
                    unique_name_set.add("/%s"%(name) )
    

def _main_():
    #register terminal signal handler
    signal.signal(signal.SIGINT, signal_handler)

    root_url = "https://www.chinaz.com"

    #timeout is important
    http = urllib3.PoolManager(timeout=5.0)
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'''}
    url_queue = Queue.Queue()

    #enqueue root url
    url_queue.put(root_url)
    
    #name and url set
    name_set = set()
    global_url_set = set()

    #record var
    refuse_cnt = 0
    timeout_cnt = 0

    #parse and grab repeatly
    while force_quit != 1 and not url_queue.empty() and len(name_set) < name_threshold:
        #dequeue one url
        url = url_queue.get()
        print("process %s"%(url))

        #involve get request with url
        try:
            ret = http.request('GET', url, headers)
            if ret.status == 200:
                print("[got html data, do grab]")
            else:
                print("[timeout, skip it]")
                timeout_cnt += 1
                continue
        except:
                print("[connect refuse, ignore]")
                refuse_cnt += 1
                continue

       
        #grab it
        url_set = set()
        _grab_one_req_(ret, name_set, url_set, global_url_set)
        
        #enqueue all urls grabed
        for uni_url in url_set:
            url_queue.put(uni_url)
    
    print("%d name totally"%(len(name_set)) )
    idx=1
    for name in name_set:
        print("%d\t: %s"%(idx, name)) 
        idx += 1

    print("record:")
    print("connect refuse=%d"%(refuse_cnt))
    print("connect timeout=%d"%(timeout_cnt))
    
    # print("%d url totally"%(len(name_set)) )
    # idx=1
    # for url in url_set:
    #     print("%d\t: %s"%(idx, url)) 
    #     idx += 1

#start here
_main_()

# url = "www/baidu/com/中"

# zhre = re.compile('[\u4e00-\u9fa5]+')

# name_match = zhre.search(url) 

# #filter names with chinese char 
# if name_match:
#     print(url)
    






