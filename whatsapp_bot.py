#WHATSAPP BOT PYTHON PROJECT

#This project uses selenium library to automate interaction with site "web.whatsapp.com" and perform
#actions like sending messages, sending files etc. to chat.

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

import time
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import shutil
import multiprocessing
import queue
import base64
import requests
import urllib

import pandas as pd

#User defined modules 
from google_search import google_search
from read_gmail import get_mail
from youtube_search import youtube_search
from image_search import image_search
from youtube_download import download_audio
#from send_msg import send_msg
from speech2text import speech2text
from recognize_face import add_user_by_face

#Function to send text message(post) to chat. 
def send_msg(post, driver, wait=None):
    input_field_el = driver.find_elements_by_xpath("//div[contains(@class, 'copyable-text selectable-text')]")[1]

    lines = post.replace('\r\n', '\n').split('\n')
    for part in lines:
        input_field_el.send_keys(part)
        ActionChains(driver).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.SHIFT).key_up(Keys.ENTER).perform()
    
    if wait:
        try:
            WebDriverWait(driver, wait).until(EC.presence_of_element_located((By.XPATH,
                                                                              "//div[@style='transform: translateY(0px);']")))
        except TimeoutException:
            pass
    send_btn_el = driver.find_elements_by_tag_name('button')[-1]
    send_btn_el.click()

#Function to get data saved by site in system's memory 
def get_file_content_chrome(driver, uri):
    result = driver.execute_async_script("""
    var uri = arguments[0];
    var callback = arguments[1];
    var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'arraybuffer';
    xhr.onload = function(){ callback(toBase64(xhr.response)) };
    xhr.onerror = function(){ callback(xhr.status) };
    xhr.open('GET', uri);
    xhr.send();
    """, uri)
    if type(result) == int :
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)

#Function which contains main loop which reads the input in form of text messages, voice messages, images and
#parses the input and outputs the requested data.
def main():
    #MAIN LOOP
    while True:

        #Loop to send requested youtube links
        while True:
            try:
                titles, links, infos, log, site = search_q.get(block=False)

                if log == 'success':
                    if site == 'youtube':
                        for l, i in zip(links, infos):
                            channel, uploaded, views, length = i
                            post = f'{l}\n\n*Channel: {channel}*\nUploaded {uploaded}\n{views} views\nLength: {length}'
                            send_msg(post, driver, wait=7)

                else:
                    send_msg(log, main_driver)
            except queue.Empty:
                break

        #Loop to send requested files
        while True:
            try:
                filepaths, log = file_q.get(block=False)

                if log == 'success':
                    filepaths_str = map(str, filepaths)
                    all_files = '\n'.join(filepaths_str)
                    
                    attach_el = driver.find_element_by_xpath("//div[@title='Attach']").click()
                    doc_el = driver.find_element_by_xpath("//input[@type='file']")
                    doc_el.send_keys(all_files)
                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//span[@data-testid="send"]')))
                    driver.find_element_by_xpath("//span[@data-testid='send']/parent::*").click()

                    for path in filepaths:
                        path.unlink(missing_ok=True)

                else:
                    send_msg(log, main_driver)
            except queue.Empty:
                break

        #Checking for any active timer requests
        if any([active_user[user]['timer']['timer_state'] for user in active_user]):
            for user in active_user:
                if active_user[user]['timer']['timer_state'] is True:
                    t_stop = time.perf_counter()
                    #print(t_stop)
                    if t - (t_stop - active_user[user]['timer']['t_start']) <= 0.5:
                        active_user[user]['timer']['timer_state'] = False
                        post = f'{user}, {time_per} elapsed.'
                        send_msg(post, driver)

        #Checking for any active gmail requests
        if any([active_user[user]['gmail']['state'] for user in active_user]):
            for user in active_user:
                if active_user[user]['gmail']['state'] is True:
                    t_stop = datetime.now()
                    if t_stop - active_user[user]['gmail']['t_start'] > timedelta(minutes=2):
                        username = active_user[user]['gmail']['username']
                        password = active_user[user]['gmail']['password']
                        mails, log = get_mail(username, password, user, active_user[user]['gmail']['t_start'])

                        if log == 'success':
                            if mails:
                                send_msg(f'{len(mails)} new mail(s) for *{user}*.', driver)
                            for mail in mails: 
                                subject, from_, date, date_str, body, attachment = mail

                            #if date > active_user[user]['gmail']['t_start']:
                                active_user[user]['gmail']['t_start'] = datetime.now()
                                post = f'From: {from_}\r\n'\
                                       + f'Date: {date_str}\r\n'\
                                       + f'Subject: {subject}\r\n\r\n'\
                                       + f'{body}'
                                send_msg(post, driver)

                                if attachment:
                                    send_msg('Attachment(s):', driver)
                                    
                                    files = map(str, attachment)

                                    all_files = '\n'.join(files)

                                    attach_el = driver.find_element_by_xpath("//div[@title='Attach']").click()
                                    doc_el = driver.find_element_by_xpath("//input[@type='file']")
                                    doc_el.send_keys(all_files)
                                    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//span[@data-testid="send"]')))
                                    driver.find_element_by_xpath("//span[@data-testid='send']/parent::*").click()
                                    #WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CLASS_NAME, '_3doiV'))).click()

                                    for file in attachment:
                                        file.unlink(missing_ok=True)

                        else:
                            send_msg(log, driver)

        #Reading last chat
        chats_el = driver.find_element_by_xpath("//div[contains(@aria-label, 'Message list')]")
        chats_el = chats_el.find_elements_by_xpath("./*")

        try:
            chats_el = [x for x in chats_el if x.get_attribute('data-id') is not None]
        except:
            continue

        #Checking if last chat message is an image and if it is an image then activating bot for the sender,
        #if image contains face of sender(matched from profile pic).
        try:
            chats_el[-1].find_element_by_tag_name('img')

            WebDriverWait(chats_el[-1], 5).until(EC.presence_of_element_located((By.XPATH, '//img[contains(@src,"blob")]')))

            last_chat_el = chats_el[-1].find_elements_by_tag_name('img')
            last_chat_el = [x for x in last_chat_el if 'blob' in x.get_attribute('src')]

            if last_chat_el:
                sender = chats_el[-1].find_elements_by_xpath(".//span[contains(@dir, 'auto')]")

                if len(sender) == 1:
                    sender_name = 'Luv'
                    sender_time = sender[-1].text
                else:
                    sender_name = sender[0].text
                    sender_time = sender[1].text
            else:
                raise NoSuchElementException

            if sender_name in active_user.keys():
                raise NoSuchElementException

            if 'selectable-text' not in last_chat_el[0].get_attribute('class'):
                uri = last_chat_el[0].get_attribute('src')
                img_data = get_file_content_chrome(driver, uri)
            
                file_path = Path(fr'{sender_name}\image.jpg')
                file_path.parent.mkdir(parents=True, exist_ok=True)
                open(file_path, 'wb').write(img_data)

                new_user, log = add_user_by_face(file_path)

                if log == 'success':
                    active_user[new_user] = {'timer': {'t_start': None, 'timer_state': False},
                                             'gmail': {'t_start': None, 'latest_id': None, 'state': False,
                                                       'username': None, 'password': None}
                                            }
                                             
                    post = f'Hi {new_user}!\n[Bot Active]'
                    send_msg(post, driver)
                else:
                    send_msg(log, driver)
                #file_path.unlink(missing_ok=True)
                
        except (NoSuchElementException, TimeoutException):
            #print('no')
            pass
        except StaleElementReferenceException:
            continue

        #Checking if last chat message is a voice message and if it is a voice message then converting
        #the speech to text to be queried.   
        try:
            last_chat_el = chats_el[-1].find_element_by_tag_name('audio')

            sender = chats_el[-1].find_elements_by_xpath(".//span[contains(@dir, 'auto')]")
            if len(sender) == 1:
                sender_name = 'Luv'
                sender_time = sender[-1].text
            else:
                sender_name = sender[0].text
                sender_time = sender[1].text
            #print(sender_name, sender_time)

            uri = last_chat_el.get_attribute('src')
            speech_data = get_file_content_chrome(driver, uri)
            
            file_path = Path(fr'{sender_name}\speech.oga')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            open(file_path, 'wb').write(speech_data)

            text, log = speech2text(file_path)

            file_path.unlink(missing_ok=True)

            if log != 'success':
                send_msg(log, driver)
                continue

        except:
            try:
                last_chat_el_text = chats_el[-1].find_element_by_class_name("copyable-text").find_elements_by_xpath("./*")[-1]

                text = last_chat_el_text.text
                last_chat_el_sender = chats_el[-1].find_element_by_class_name('copyable-text')
                sender = last_chat_el_sender.get_attribute('data-pre-plain-text')
                sender_time, sender_name = sender.split(']')
                sender_name = sender_name[1:-2]
                sender_time = datetime.strptime(sender_time, '[%I:%M %p, %m/%d/%Y')
            except:
                continue


        #PARSING QUERIES
        if True: #sender_time > bot_init_time:
            if text.lower() == 'deactivate' and sender_name == 'Luv':
                break
                    
            if text.lower() == 'hi bot':
                post = f'Hi {sender_name}!\n[Bot Active]'
                if sender_name not in active_user.keys(): #bot_active_for
                    active_user[sender_name] = {'timer': {'t_start': None, 'timer_state': False},
                                                'gmail': {'t_start': None, 'latest_id': None, 'state': False,
                                                          'username': None, 'password': None}
                                                }
                    #bot_active_for.append(sender_name)
                send_msg(post, driver)
            
            elif text.lower() == 'bye bot':
                post = f'Bye {sender_name}!\n[Bot Inactive]'
                if sender_name in active_user.keys():
                    del active_user[sender_name]
                #shutil.rmtree(f'{sender_name}', ignore_errors=True)
                send_msg(post, driver)
            
            elif text.lower()[:4] == 'bot ':
                if sender_name in active_user.keys():

                    if text.lower()[4:8] == 'time' and len(text) == 8:
                        post = f'Current Date\Time\n\n'\
                               + f'Country: India\n\nTime Zone: Asia/Kolkata\n'\
                               + f'{datetime.now().strftime("%I:%M %p")}'\
                               + f', {datetime.now().strftime("%H:%M")}\n'\
                               + f'{datetime.now().strftime("%d-%b-%Y")}'

                        send_msg(post, driver)

                    elif text.lower()[4:9] == 'time ' and text.lower()[9:] != '':
                        post = ''
                        country = text.lower()[9:]
                        for con, tz in tz_list:
                            if con.lower() == country.lower():
                                post += f'\n\nTime Zone: {tz}\n'\
                                        + f'{datetime.now(pytz.timezone(tz)).strftime("%I:%M %p")}'\
                                        + f', {datetime.now(pytz.timezone(tz)).strftime("%H:%M")}\n'\
                                        + f'{datetime.now(pytz.timezone(tz)).strftime("%d-%b-%Y")}'

                        if post:
                            post = f'Current Date\Time\n\n'\
                                   + f'Country: {country.title()}'\
                                   + post
                            send_msg(post, driver)
                        else:
                            send_msg(f'Unable to find time of country: {country}', driver)

                    elif text.lower()[4:11] == 'search ':
                        if text[-1] == ')':
                            if text[-3] == '(' and text[-2].isdigit():
                                page = int(text[-2])
                                query = text[11:-3].strip()
                            elif text[-4] == '(' and text[-2].isdigit() and text[-3].isdigit():
                                page = int(text[-3:-1])
                                query = text[11:-4].strip()
                        else:
                            page = 1
                            query = text[11:].strip()

                        if not query:
                            send_msg('Please provide a valid search query', driver)
                        else:
                            send_msg(f'Fetching {query} search results, please wait few seconds...', driver)
                            titles, links, descriptions, log = google_search(query, page)

                            if log == 'success':
                                for t, l, d in zip(titles, links, descriptions):
                                    post = f'{l}\n\n{d}' #*{t}*\n
                                    send_msg(post, driver, wait=10)
                            else:
                                send_msg(log, driver)

                    elif text.lower()[4:10] == 'timer ':
                        if active_user[sender_name]['timer']['timer_state']:
                            send_msg(f'{sender_name}, previous timer is running. Please wait for current timer to stop.', driver)

                        else:
                            hours = minutes = seconds = 0
                            time_per = text[10:].lower()
                            try:
                                if 'h' in time_per:
                                    hours = int(time_per.split('h')[0])
                                    if 'm' in time_per:
                                        minutes = int(time_per.split('h')[1].split('m')[0])
                                        if 's' in time_per:
                                            seconds = int(time_per.split('h')[1].split('m')[1].split('s')[0])
                                    t = hours*3600 + minutes*60 + seconds

                                elif 'm' in time_per:
                                    minutes = int(time_per.split('m')[0])
                                    if 's' in time_per:
                                        seconds = int(time_per.split('m')[1].split('s')[0])
                                    t = hours*3600 + minutes*60 + seconds

                                elif 's' in time_per:
                                    seconds = int(time_per.split('s')[0])
                                    t = hours*3600 + minutes*60 + seconds

                            except:
                                send_msg(f'Invalid time format.', driver)

                            else:
                                send_msg(f'{time_per} timer started.', driver)
                                active_user[sender_name]['timer']['timer_state'] = True
                                active_user[sender_name]['timer']['t_start'] = time.perf_counter()
                            #print(t_start)
                            #timer_state = True

                    elif text.lower()[4:10] == 'gmail ':
                        if text.lower()[10:] == 'stop':
                            if active_user[sender_name]['gmail']['state'] == True:
                                active_user[sender_name]['gmail']['state'] = False
                                send_msg(f'GMAIL Notification for {sender_name} deactivated.', driver)
                            else:
                                send_msg(f'GMAIL Notification for {sender_name} is not activated.', driver)

                        else:
                            (active_user[sender_name]['gmail']['username'],
                             active_user[sender_name]['gmail']['password']) = text[10:].split()

                            if ( active_user[sender_name]['gmail']['username'] == '' or
                                 active_user[sender_name]['gmail']['password'] == ''):
                                send_msg('Invalid username or password.', driver)
                            else:
                                send_msg(f'GMAIL Notification for {sender_name} activated.', driver)
                                active_user[sender_name]['gmail']['t_start'] = datetime.now()
                                active_user[sender_name]['gmail']['state'] = True

                    elif text.lower()[4:13] == 'make note':
                        note = text[14:]
                        p = Path(f'{sender_name}\\notes.txt')
                        p.parent.mkdir(parents=True, exist_ok=True)
                        if p.is_file():
                            note = '\n\n' + note
                        
                        with open(p, 'a') as text_file:
                            text_file.write(note)

                        send_msg(f'{sender_name}, note is saved.', driver)

                    elif text.lower()[4:] == 'show note':
                        p = Path(f'{sender_name}\\notes.txt')
                        if p.is_file():
                            with open(p, 'r') as text_file:
                                note = text_file.read()
                            send_msg(note, driver)
                        else:
                            send_msg(f'{sender_name}, no notes found.', driver)

                    elif text.lower()[4:12] == 'youtube ':
                        if text[-1] == ')' and text[-3] == '(' and text[-2].isdigit():
                            page = int(text[-2])
                            query = text[12:-3].strip()
                        else:
                            page = 1
                            query = text[12:].strip()

                        #print(page)

                        if query:
                            send_msg(f'Fetching {query} videos, please wait few seconds...', driver)

                            youtube_process = multiprocessing.Process(target=youtube_search, args=((search_q, query, page)))
                            youtube_process.start()
                        else:
                            send_msg('Invalid video search query.', driver)

                    elif text.lower()[4:10] == 'image ':
                        if text[-1] == ')' and text[-3] == '(' and text[-2].isdigit():
                            page = int(text[-2])
                            query = text[10:-3].strip()
                        else:
                            page = 1
                            query = text[10:].strip()

                        if query:
                            send_msg(f'Fetching {query} images, please wait few seconds...', driver)
                            Path(f'{sender_name}').mkdir(parents=True, exist_ok=True)
                            
                            process_image = multiprocessing.Process(target=image_search, args=(file_q, query, sender_name, page))
                            process_image.start()
                        else:
                            send_msg('Invalid image search query.', driver)

                    elif text.lower()[4:10] == 'audio ':
                        link = text[10:]
                        if link:
                            send_msg('Fetching audio file, please wait few seconds...', driver)
                            process_audio = multiprocessing.Process(target=download_audio, args=(file_q, link, sender_name))
                            process_audio.start()
                        else:
                            send_msg('Invalid youtube link.', driver)

                    elif text.lower()[4:9] == 'help ':
                        command = text[9:]

                        if command == 'time':
                            post = '*time* [<country_name>] command:\n'\
                                   + 'By default returns current date/time of India(if country is not specified).\n'\
                                   + 'Otherwise returns date/time of specified country with all time zones.\n\n'\
                                   + 'Usage:\nbot time\nbot time Australia'
                            send_msg(post, driver)

                        elif command == 'timer':
                            post = '*timer* <time_period> command:\n'\
                                   + 'Starts a timer for specified time peroid and notifies user when time has elapsed.\n'\
                                   + 'Use characters "h", "m" and "s" to specify hours, minutes and seconds respectively. '\
                                   + 'For example "1m20s" means 1 minute and 20 seconds\n\n'\
                                   + 'Usage:\n'\
                                   + 'bot timer 20s\nbot timer 2m45s\nbot timer 2h'
                            send_msg(post, driver)

                        elif command == 'search':
                            post = '*search* <query> [(<group_no.>)] command:\n'\
                                   + 'Return ten google search results.\n'\
                                   + '```(<group_no.>)``` argument is optional and specifies the group of search results. '\
                                   + 'For example (1) means first group of ten results, (2) means second group of ten results and so on.\n\n'\
                                   + 'Usage:\n'\
                                   + 'bot search how to make cake\n'\
                                   + 'bot search how to make cake (3)'
                            send_msg(post, driver)

                        elif command == 'gmail':
                            post = '*gmail* <username> <password> command:\n'\
                                   + 'Checks for the e-mail account every two minutes for any new mail(s)'\
                                   + '(after this command is executed) and returns mails with attachments.\n\n'\
                                   + 'Usage:\n'\
                                   + 'bot gmail abc@gmail.com 123456'
                            send_msg(post, driver)

                        elif command == 'gmail stop':
                            post = '*gmail stop* command:\n'\
                                   + 'Stops checking for any mails for the given account.\n\n'\
                                   + 'Usage:\n'\
                                   + 'bot gmail stop'
                            send_msg(post, driver)

                        elif command == 'make note':
                            post = '*make note* <text> command:\n'\
                                   + 'Saves a text note to a permanent file which can be viewed later.\n\n'\
                                   + 'Usage:\n'\
                                   + 'bot make note my gmail password is 123456.'
                            send_msg(post, driver)

                        elif command == 'show note':
                            post = '*show note* command:\n'\
                                    + 'Returns note(s) saved(if any) by yourself.\n\n'\
                                    + 'Usage:\n'\
                                    + 'bot show note'
                            send_msg(post, driver)

                        elif command == 'youtube':
                            post = '*youtube* <query> [(<group_no.>)] command:\n'\
                                    + 'Return ten video search results from youtube.\n'\
                                    + '```(<group_no.>)``` argument is optional and specifies the group of search results. '\
                                    + 'For example (1) means first group of ten results, (2) means second group of ten results and so on.\n\n'\
                                    + 'Usage:\n'\
                                    + 'bot youtube linkin park\n'\
                                    + 'bot youtube linkin park (3)'
                            send_msg(post, driver)

                        elif command == 'image':
                            post = '*image* <query> [(<group_no.>)] command:\n'\
                                    + 'Return ten(atmost) images  from google image search results.\n'\
                                    + '```(<group_no.>)``` argument is optional and specifies the group of search results. '\
                                    + 'For example (1) means first group of ten results, (2) means second group of ten results and so on.\n\n'\
                                    + 'Usage:\n'\
                                    + 'bot image dog\n'\
                                    + 'bot image dog (3)'
                            send_msg(post, driver)

                        elif command == 'audio':
                            post = '*audio* <youtube_link> command:\n'\
                                    + 'Returns audio of the provided youtube video link.\n\n'\
                                    + 'Usage:\n'\
                                    + 'bot audio https://www.youtube.com/watch?v=jEJI6Nf1aWU'
                            send_msg(post, driver)

                        else:
                            post = f'No such command: "{command}"'
                            send_msg(post, driver)
                    
                    else:
                        send_msg(f'Invalid command: "{text[4:]}"', driver)
                    
if __name__ == '__main__':
    bot_init_time = datetime.now() - timedelta(minutes=1)

    df = pd.read_csv('country_wise_tz.csv', index_col=0)
    tz_list = df[['Country Name', 'Time Zone']].values.tolist()

    chrome_opt = webdriver.ChromeOptions()
    chrome_opt.add_argument(r"user-data-dir=C:\Users\LUV\AppData\Local\Google\Chrome\User Data")
    #chrome_opt.add_argument(r"--headless")

    driver = webdriver.Chrome(executable_path=
                              r'F:\PYTHON\chromedriver_win32\chromedriver.exe',
                              options=chrome_opt)

    driver.get("https://web.whatsapp.com/")

    while True:
        try:
            contact_el = driver.find_element_by_xpath("//span[@title='BOT']")#Family😊
            contact_el.click()
            break
        except:
            continue

    time.sleep(5)

    main_el = driver.find_element_by_id('main')
    header_el = main_el.find_element_by_tag_name('header')
    header_el.find_element_by_xpath('.//div[@role="button"]').click()

    time.sleep(2)

    group_info_el = driver.find_element_by_class_name('copyable-area')
    pp_image_el = group_info_el.find_elements_by_xpath('.//div[@style="height: 49px; width: 49px;"]')
    
    name_el = group_info_el.find_elements_by_xpath('.//span[@title]')
    names = [x.text for x in name_el if x.text == x.get_attribute('title') and 'selectable-text' not in x.get_attribute('class')]
    names = ['Luv' if s == 'You' else s for s in names]
    
    for el, name in zip(pp_image_el, names):
        image_link = el.find_element_by_tag_name('img').get_attribute('src')

        file_content = get_file_content_chrome(driver, image_link)
        p = Path(f'profile_pictures\\{name}.jpg')
        
        open(p, 'wb').write(file_content)

    group_info_el.find_element_by_tag_name('button').click()

    time.sleep(1)


    post = '[BOT Server Active]\n\n'\
           + 'To activate bot for yourself use command:\nhi bot\n'\
           + 'To deactivate bot for yourself use command:\nbye bot\n\n'\
           + 'Bot Commands:\n'\
           + '```->bot time [<country_name>]\n'\
           + '->bot timer <time_period>\n'\
           + '->bot search <query> [(<group_no.>)]\n'\
           + '->bot gmail <username> <password>\n'\
           + '  ->bot gmail stop\n'\
           + '->bot make note <text>\n'\
           + '  ->bot show note\n'\
           + '->bot youtube <query> [(<group_no.>)]\n'\
           + '->bot image <query> [(<group_no.>)]\n'\
           + '->bot audio <youtube_link>\n'\
           + '->bot help <command_name>```\n\n'\
           + '*Note*: Option within ```[]``` is optional.\n'\
           + 'Use command "bot help" for more infromation on commands.\nHelp example:\nbot help gmail'
    send_msg(post, driver)

    active_user = {}
    file_q = multiprocessing.Queue()
    search_q = multiprocessing.Queue()
    mail_q = multiprocessing.Queue()
    speech_q = multiprocessing.Queue()

    main()

    driver.close()
    driver.quit()


