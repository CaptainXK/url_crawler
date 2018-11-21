# -*- coding: UTF-8 -*-
import urllib3
import socket
import re
from bs4 import BeautifulSoup as bsp
import queue
import signal
import sys
import traceback
import chardet

#name set
name_set = set()

#only grab name as number as threshold
name_threshold = 20000
force_quit = 0

def signal_handler(sig, frame):
    global force_quit
    print('[Ctrl+C]')
    force_quit = 1
    
def url_slash_process(url):
    #remove all non 'a-zA-Z0-9' characters
    url = re.sub(r'[^0-9a-zA-Z/]', '/', url, 0)

    #add '/' for start
    url = '/' + url
    
    #remove '/' in the tail
    url = re.sub(r'\/$', '', url, 0)
    
    #merge duplicated '/'
    url = re.sub(r'\/[\/]+', '/', url, 0)

    return url

def _grab_one_req_(html_data, unique_name_set, unique_url_set, global_url_set):
    html_text=""
    web_coding=""

    global name_threshold
    
    #if get done
    if html_data.status == 200:
        web_coding = chardet.detect(html_data.data)['encoding']
        print("web page data len=%d, coding=%s, current name number=%d"%(len(html_data.data), web_coding, len(unique_name_set)) )
        html_text = html_data.data
    
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
                name = url_slash_process(match.group(1))

                unique_name_set.add(name)
                if(len(unique_name_set) == name_threshold):
                    break
    

def _main_():
    #register terminal signal handler
    signal.signal(signal.SIGINT, signal_handler)

    root_url = "http://www.chinaz.com"

    #timeout is important
    http = urllib3.PoolManager(timeout=5.0)
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'''}
    url_queue = queue.Queue()

    #enqueue root url
    url_queue.put(root_url)
    
    #name and url set
    global_url_set = set()
    global name_set

    #record var
    refuse_cnt = 0
    timeout_cnt = 0

    global name_threshold

    #parse and grab repeatly
    while force_quit != 1 and not url_queue.empty() and len(name_set) < name_threshold:
        #dequeue one url
        url = url_queue.get()
        print("process %s"%(url))

        #involve get request with url
        try:
            ret = http.request('GET', url, headers)
            if ret.status == 200:
                # print("[got html data, do grab]")
                pass
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
    # idx=1
    # for name in name_set:
    #     print("%d\t: %s"%(idx, name)) 
    #     idx += 1

    print("record:")
    print("connect refuse=%d"%(refuse_cnt))
    print("connect timeout=%d"%(timeout_cnt))
    
def de_encode_test():
    urls = ['/www/51cto/com/php/search/php/q/程序', '/www/51cto/com/php/search/php/q', 'www/blueidea/com/common/searchbykey/asp/keyword/字体设计']

    zhre = re.compile(u'[\u4e00-\u9fa5]+')

    for url in urls:
        u_url = url.decode('utf-8')
        name_match = zhre.search(u_url) 
        if name_match:
            print(url)

def parse_name_set():
    unique_names = set()
    names_dict = dict()

    for name in name_set:
        components = name.split('/')
        cur_name_len = len(components)

        if str(cur_name_len) in names_dict:
            names_dict[str(cur_name_len)] += 1
        else:
            names_dict[str(cur_name_len)] = 1


        for comp in components:
            unique_names.add(comp)

    print("[parse name set]") 
    print("%d unique words in total"%( len(unique_names) ))

    #traverse the dict
    names_rec_items = names_dict.items()
    name_sorted_list = sorted(names_rec_items, key = lambda x:x[0] )
    for name_len, nb in name_sorted_list:
        print("%d:%d"%(int(name_len), int(nb)))


#start here
_main_()
parse_name_set()
# de_encode_test()

# url = 'a&&/b/c/d/a///s/'
# url_slash_process(url)






