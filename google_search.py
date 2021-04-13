import urllib
from bs4 import BeautifulSoup
import requests
import urllib.request

def google_search(text=None, page=1):
    if not text:
        text = 'hello'
    text = urllib.parse.quote_plus(text)

    url = 'https://google.com/search?q=' + text + '&num=100'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}

    response = requests.get(url, headers=headers)
    #response = urllib.request.urlopen(url, headers

    ##with open('C:/Users/LUV/Desktop/a.html', encoding='utf8') as fh:
    ##    a = fh.read()

    soup = BeautifulSoup(response.text, "html.parser")#response.text

    search_blocks = soup.find_all("div", class_="hlcw0c")

    if search_blocks:
        search_results = []
        for block in search_blocks:
            search_results.extend(block.find_all("div", class_="g"))
    else:
        search_results = soup.find_all(lambda tag: tag.name == 'div' and
                                       tag.get('class') == ['g'])

    lb = (page-1)*10
    ub = page*10
    #print(search_results[lb:ub])
    links = []
    for result in search_results[lb:ub]:
        link_el = result.find("div", class_="yuRUbf")
        
        if link_el:
            link_el = link_el.find('a')
        else:
            continue

        if link_el:
            link = link_el.get('href')
        else:
            continue
        
        links.append(link) #result.find("div", class_="yuRUbf").find('a').get('href')

    titles = []
    for result in search_results[lb:ub]:
        title_el = result.find("h3", class_="LC20lb DKV0Md")
        
        if title_el:
            title = title_el.get_text()
        else:
            continue
        
        titles.append(title) #result.find("h3", class_="LC20lb DKV0Md").get_text()

    descriptions = []
    for result in search_results[lb:ub]:
        description_el = result.find("span", class_="aCOpRe")
        
        if description_el:
            description = description_el.get_text()
        else:
            continue
        
        descriptions.append(description) #result.find("span", class_="aCOpRe").get_text()

    if links:
        log = 'success'
    else:
        log = 'No more results to fetch. Please try a lower group number.'

    return titles, links, descriptions, log
    
if __name__ == '__main__':
    titles, links, descriptions, log = google_search('dog', page=50)
    
    print(links)
    print(titles)
    print(descriptions)
    print(log)



