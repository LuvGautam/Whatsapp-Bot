import urllib
from bs4 import BeautifulSoup
import requests
import urllib.request
import time

from selenium import webdriver

def youtube_search(q, text=None, page=1):
    site = 'youtube'
    
    if text is None:
        text = 'how to make khichdi'
    text = urllib.parse.quote_plus(text)
    
    chrome_opt = webdriver.ChromeOptions()
    #chrome_opt.add_argument("--start-maximized")
    chrome_opt.add_argument('--headless')

    driver = webdriver.Chrome(executable_path=
                              r'F:\PYTHON\chromedriver_win32\chromedriver.exe',
                              options=chrome_opt)

    url = 'https://www.youtube.com/results?search_query=' + text
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

    driver.get(url)
    #time.sleep(5)
    
    while True:
        search_blocks = []
        
        soup = BeautifulSoup(driver.page_source, "html.parser")#response.text

        all_search = soup.find("div", id="contents")

        groups = all_search.find_all("ytd-item-section-renderer", recursive=False)
        #print(len(groups))
        for group in groups:
            group = group.find('div', id='contents')
            search_blocks.extend(group.find_all("ytd-video-renderer",
                                                class_="style-scope ytd-item-section-renderer")) #recursive=False
##        print(len(search_blocks))
##        return 1,2,3
        
        n_result = len(search_blocks)
        if n_result >= page*10:
            search_blocks = search_blocks[(page-1)*10:page*10]
            log = 'success'
            break
        else:
            driver.execute_script("window.scrollTo(0, 10000);")
            #driver.execute_script(f'document.getElementsByTagName("ytd-video-renderer")[{n_result-1}].scrollIntoView();')
            time.sleep(2)

    #print(search_blocks)

    titles = []
    links = []
    infos = []

    for result in search_blocks:
            titles.append(result.find('h3').find('a').get('title'))
            links.append('https://www.youtube.com' +
                         result.find('h3').find('a').get('href'))
            infos.append(result.find('h3').find('a').get('aria-label'))

    for i, (title, info) in enumerate(zip(titles, infos)):
        info = info[len(title):].split()

        ago_i = info.index('ago')
        
        channel = ' '.join(info[1:ago_i-2])
        uploaded = ' '.join(info[ago_i-2:ago_i+1])
        views = info[-2]
        length = ' '.join(info[ago_i+1:-2])
        
        infos[i] = (channel, uploaded, views, length)

    driver.close()
    driver.quit()

    q.put((titles, links, infos, log, site))
    #return (titles, links, infos, log)


if __name__ == '__main__':
    titles, links, infos = youtube_search('linkin park', page=2)
    print('done')
