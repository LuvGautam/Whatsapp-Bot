import urllib
from bs4 import BeautifulSoup
import requests
import urllib.request
import time
from pathlib import Path

from selenium import webdriver

#from send_msg import send_msg

def image_search(q, text=None, sender_name='Luv', page=1):
    #print('hi')
    if text is None:
        text = 'cat'

    text = urllib.parse.quote_plus(text)
        
    chrome_opt = webdriver.ChromeOptions()
    #chrome_opt.add_argument("--start-maximized")
    #chrome_opt.add_argument("--incognito")
    chrome_opt.add_argument('--headless')
    #ffox_opt = webdriver.FirefoxOptions()
    #ffox_opt.add_argument('--headless')

    driver = webdriver.Chrome(executable_path=
                              r'F:\PYTHON\chromedriver_win32\chromedriver.exe',
                              options=chrome_opt)

    url = "https://www.google.com/search?q=" + text + "&source=lnms&tbm=isch"
    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

    driver.get(url)

    all_results = driver.find_element_by_xpath("//div[@jsname='r5xl4']")

    image_blocks = all_results.find_elements_by_xpath("//div[@jsname='N9Xkfe' and @jscontroller='H9MIue']")

    o_result = len(image_blocks)
        
    while True:
        
        if o_result >= page * 10:
            image_blocks = image_blocks[(page-1)*10:page*10]
            log = 'success'
            break
        else:
            driver.execute_script(f'''
                                    var xpath = function(xpathToExecute){{
                                    var result = [];
                                    var nodesSnapshot = document.evaluate(xpathToExecute, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null );
                                    for ( var i=0 ; i < nodesSnapshot.snapshotLength; i++ ){{
                                        result.push( nodesSnapshot.snapshotItem(i) );
                                    }}
                                      return result;
                                    }}
                                    xpath("//div[@jsname='N9Xkfe']")[{o_result-1}].scrollIntoView();''')
            time.sleep(2)

            all_results = driver.find_element_by_xpath("//div[@jsname='r5xl4']")

            image_blocks = all_results.find_elements_by_xpath("//div[@jsname='N9Xkfe' and @jscontroller='H9MIue']")

            n_result = len(image_blocks)

            if n_result <= o_result:
                image_blocks = []
                log = 'No more results to fetch. Please try a lower group number.'
                break
            else:
                o_result = n_result

    #print(log)

    #print(image_blocks)

    links = []
    for i in range(len(image_blocks)):
        image_blocks[i].click()
        link_el = image_blocks[i].find_element_by_tag_name('a')
        link = link_el.get_attribute('href')
        link = urllib.parse.unquote(link)
        link = link.split('&imgrefurl=')[0]
        link = link[37:]
        links.append(link)
        #time.sleep(1)

    filepaths = []
    for i, link in enumerate(links, start=1):
        try:
            req = requests.get(link)
        except:
            continue
        type_, format_ = req.headers.get('content-type').split('/')
        if ';' in format_:
            format_ = format_.split(';')[0]
        #print(req.headers.get('content-type'))
        p = Path(f'{sender_name}\\{text}{i}.{format_}')
        
        if type_ == 'image':
            open(p, 'wb').write(req.content)
            filepaths.append(p.resolve())

    driver.close()
    driver.quit()

##    if main_driver:
##        if log == 'success':
##            filepaths_str = map(str, filepaths)
##            all_files = '\n'.join(filepaths_str)
##            
##            attach_el = main_driver.find_element_by_xpath("//div[@title='Attach']").click()
##            doc_el = main_driver.find_element_by_xpath("//input[@type='file']")
##            doc_el.send_keys(all_files)
##            WebDriverWait(main_driver, 30).until(EC.presence_of_element_located((By.XPATH, '//span[@data-testid="send"]')))
##            main_driver.find_element_by_xpath("//span[@data-testid='send']/parent::*").click()
##
##        else:
##            send_msg(log, main_driver)
    q.put((filepaths, log))
    #return filepaths, log

if __name__ == '__main__':
    p = Path('Luv')
    p.mkdir(parents=True, exist_ok=True)
    paths, log = image_search('dog', str(p), page=1)
    print(log)
    
    
