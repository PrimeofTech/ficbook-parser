import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, SessionNotCreatedException
from time import sleep
from os import environ
from bs4 import BeautifulSoup
from datetime import datetime
from getpass import getpass
import sys
import threading
import os
import platform
import json
import time

from tinydb import TinyDB, Query
db = TinyDB('data/db.json')
Session = Query()


class Parser(threading.Thread):
    def __init__(self, sid, uname='', upswd='', headless=True, auto=True, verbose=False, databasereport=True,
                 chromeinpath=True):
        self.id = str(sid)
        self.uname = uname
        self.upswd = upswd
        self.headless = headless
        self.auto = auto
        self.verbose = verbose
        self.databasereport = databasereport
        self.chromeinpath = chromeinpath
        self._driver = ''
        self._fanfics = []
        self.data = {
            "sid": self.id,
            "user": "",
            "fanficCount": 0,
            "pageCount": 0,
            "fanfics": [],
            "fandoms": []
        }
        self.setstatus('parser:created')
        threading.Thread.__init__(self)

    def setstatus(self, status):
        if not self.databasereport:
            return
        db.update({'status': status}, Session.id == self.id)

    def print(self, *text):
        content = ''
        i = self.id
        for t in text:
            content += str(t)
        if len(self.id) > 10:
            i = self.id[:10] + '...'
        if self.verbose:
            print(f"[{i}] {content}")

    def run(self):
        self.initdriver()
        self.setstatus('parser:driver_initialized')
        self.print('Driver initialized...')
        # self.checkindex()
        # self.setstatus('parser:network_checked')
        # self.print('Network checked')
        if not self.login(self.uname, self.upswd):
            self.setstatus('parser:login_error')
            self.print('Login failed... Aborting!')
            self.close()
            return False, 'login_error'
        self.setstatus('parser:login_successful')
        self.print('Login was successful...')
        self.setstatus('parser:starting_extraction')
        self.print('Launching extraction...')
        success, data = self.startextraction(lambda pageno: self.setstatus(f'parser:extracting_page:{pageno}'))
        if not success:
            self.setstatus('parser:extraction_error')
            self.print('Extraction failed... Aborting!')
            self.close()
            return False, 'extraction_error'
        self.setstatus('parser:extraction_successful')
        self.print('Extraction was successful... Finishing!')
        if self.databasereport:
            db.update({'data': data}, Session.id == self.id)
        self.savetojson()
        self.close()
        return True, data

    def initdriver(self):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--window-size=800,600')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
            if self.headless:
                chrome_options.add_argument('--headless')
            if self.chromeinpath or (environ.get('chromeinpath') and environ.get('chromeinpath')):
                chrome_options.binary_location = ''
                self._driver = webdriver.Chrome(options=chrome_options)
            else:
                system = platform.system()
                executable = 'drivers/chromedriver86_'
                if system == 'Windows':
                    executable += 'win32.exe'
                elif system == 'Darwin':
                    executable += 'mac64'
                elif system == 'Linux':
                    executable += 'linux'
                else:
                    self.print(f'FATAL ERROR: Your platform cannot be recognized. ({platform.system()})')
                    quit()
                # executable = os.path.join(os.getcwd(), os.path.abspath(executable))
                executable = os.path.abspath(executable)
                if environ.get('RESOURCEPATH'):
                    executable = os.path.join(environ.get('RESOURCEPATH'), executable)
                self.print('Driver Path ', executable)
                self._driver = webdriver.Chrome(executable_path=executable, options=chrome_options)
        except SessionNotCreatedException as err:
            self.print(
                'FATAL ERROR: Please check that you have Chrome browser installed with version 86.')
            self.print(err)
            sys.exit()

    def checkindex(self):
        self._driver.get("https://ficbook.net")
        assert "Книга Фанфиков" in self._driver.title
        self.print('Network is OK.')

    def startextraction(self, pagenohandler=False):
        self.print('Starting extraction...')
        pageno = 1
        if pagenohandler:
            pagenohandler(pageno)
        self.print('Extracting page ', pageno)
        self._driver.get('https://ficbook.net/home/readedList')
        self.extractfanfics(self._driver.page_source)
        sleep(3)

        self.getnextpage(pageno, pagenohandler)
        sleep(1)
        self._driver.close()
        self.print('Extraction finished. Starting counting...')
        self.extractdata()
        self.print('Finished counting. Quitting...')
        self.showresults()
        return True, self.data
        # sleep(1)
        # sys.exit()

    def getnextpage(self, pageno, pagenohandler=False):
        # if pageno == 3:
        #     return
        try:
            nextpage = self._driver.find_element_by_xpath(
                '//*[@id="main"]/div[1]/section/section/div/div[1]/nav/div[3]/a').get_attribute('href')
            pageno += 1
            if pagenohandler:
                pagenohandler(pageno)
            self.print('Extracting page ', pageno)
            self._driver.get(nextpage)
            self.extractfanfics(self._driver.page_source)
            sleep(1)
            self.getnextpage(pageno, pagenohandler)
        except selenium.common.exceptions.NoSuchElementException:
            return

    def wait_for_either_xpath(self, *elements):
        while True:
            for i in range(len(elements)):
                try:
                    time.sleep(0.1)
                    result = self._driver.find_element_by_xpath(elements[i])
                    return i, result
                except selenium.common.exceptions.NoSuchElementException:
                    continue

    def login(self, uname, upswd):
        # # Button click
        # loginbutton = driver.find_element_by_xpath('//*[@id="jsLogin"]/a')
        # loginbutton.click()
        # sleep(5)
        #
        # # Login credentials
        # driver.find_element_by_xpath('//*[@id="mainLoginForm"]/div[1]/input').send_keys(UNAME)
        # driver.find_element_by_xpath('//*[@id="mainLoginForm"]/div[2]/input').send_keys(UPSWD)
        # driver.find_element_by_xpath('//*[@id="mainLoginForm"]/input').click()

        self._driver.get('https://ficbook.net/login')
        # Login credentials
        self._driver.find_element_by_xpath('//*[@id="main"]/div[1]/section/div/div[2]/form/div[1]/div/input').send_keys(
            uname)
        self._driver.find_element_by_xpath('//*[@id="login-password"]').send_keys(upswd)
        self._driver.find_element_by_xpath('//*[@id="main"]/div[1]/section/div/div[2]/form/button').click()

        try:
            i, element = self.wait_for_either_xpath('//*[@id="main"]/div[1]/section/div/div[2]/form/div[1]/div',
                                                    '//*[@id="dLabel"]/span[1]')
            if i == 0:
                return False
            else:
                del self.upswd
                unamespan = element.text
                assert uname in unamespan
                self.data['user'] = uname
                avatar = self._driver.find_element_by_xpath('//*[@id="dLabel"]/div/div/img').get_attribute('src')
                self.data['avatar'] = avatar
                return True
        except Exception as error:
            self.print(error)

    def loginvia(self, via='env'):
        if via == 'env' and (environ.get('UNAME') and environ.get('UPSWD')):
            self.login(environ.get('UNAME'), environ.get('UPSWD'))
        elif via == 'console':
            self.login(input('Your username: '), getpass('Your password: '))
        elif via == 'globals':
            global UNAME, UPSWD
            self.login(UNAME, UPSWD)

    def loginerror(self, driver):
        self.print('Login error')

    def extractfanfics(self, data):

        # data = data.replace(b'\n', b'').decode('utf-8')
        # data = re.sub('\s+', ' ', data)

        soup = BeautifulSoup(data, features="html.parser")
        res = soup.find_all('article', class_="block")
        for r in res:
            self._fanfics.append(r)

    def extractdata(self):
        self.print('Amount of fanfics ', len(self._fanfics))
        self.data['fanficCount'] = len(self._fanfics)

        for fanfic in self._fanfics:
            fanficData = {
                "title": fanfic.find('a', class_='visit-link').text,
                "link": 'https://ficbook.net' + fanfic.find('a', class_='visit-link')['href'],
                "string": f'{fanfic}'
            }

            fanficData['size'] = self.getsize(fanficData['string'])
            fanficData['fandom'] = self.getfandom(fanficData['string'])
            fanficData.pop('string')
            # self.print(len(PDATA['fanfics']) + 1, fanficData)
            self.data['fanfics'].append(fanficData)
            self.data['pageCount'] += fanficData['size']
            for fandom in fanficData['fandom']:
                found = False
                for index, item in enumerate(self.data['fandoms']):
                    if item['name'] == fandom:
                        item['amount'] += 1
                        found = True
                        break
                if not found:
                    self.data['fandoms'].append({
                        "name": fandom,
                        "amount": 1
                    })

        self.data['fandoms'].sort(reverse=True, key=lambda fandom: fandom['amount'])
        # self.print('RESULT: ', self.data)
        # self.savetojson()

    def getsize(self, fanfic_string):
        fanfic_string = fanfic_string.replace('\n', '')
        fanfic_string = fanfic_string.split('<dt>Размер:</dt>')
        fanfic_string.pop(0)
        fanfic_string = ''.join(fanfic_string)
        fanfic_string = fanfic_string.split('</dd>')[0]
        fanfic_string = fanfic_string.split('</strong>', 1)[1]
        fanfic_string = fanfic_string.split(',')[1].strip()
        # self.print(fanfic_string)
        fanfic_string = fanfic_string.split(' ')
        if 'написан' in fanfic_string[0]:
            fanfic_string.pop(0)
        return int(fanfic_string[0])

    def getfandom(self, fanfic_string):
        fanfic_string = fanfic_string.replace('\n', '')
        fanfic_string = fanfic_string.split('<dt>Фэндом:</dt>')
        fanfic_string.pop(0)
        fanfic_string = ''.join(fanfic_string)
        fanfic_string = fanfic_string.split('</dd>')[0].replace('<dd>', '')
        fanfic_string = [x.text for x in BeautifulSoup(fanfic_string, features="html.parser").find_all('a')]
        # self.print(', '.join(fanfic_string))
        return fanfic_string

    def savetojson(self):
        if not os.path.exists('data/out') or not os.path.exists('data/a'):
            os.makedirs('data/out', exist_ok=True)
            os.makedirs('data/a', exist_ok=True)
        jsondata = json.dumps(self.data, ensure_ascii=False)
        now = datetime.now()
        date = now.strftime("%Y%m%d")
        time = now.strftime("%H%M%S")
        file = open(f'data/out/{self.uname}_{date}_{time}.ficbookdata.json', 'w+', encoding='utf-8')
        file.write(jsondata)
        file.close()
        jsondata = {x: vars(self)[x] for x in list(vars(self)) if not str(x).startswith('_')}
        jsondata = json.dumps(jsondata)
        file = open(f'data/a/{self.id}', 'w+', encoding='utf-8')
        file.write(jsondata)
        file.close()

    def showresults(self):
        self.print(f"{'=' * 15} {self.data['user']} {'=' * 15}")
        self.print('RESULT: ', self.data)
        self.print(f"Total page read: {self.data['pageCount']}")
        self.print(f"Total fanfics read: {self.data['fanficCount']}")
        if self.data['fandoms'][0]:
            self.print(
                f"The most liked fandom is '{self.data['fandoms'][0]['name']}' with {self.data['fandoms'][0]['amount']} fanfics read.")
        self.print(f"The most recently you read '{self.data['fanfics'][0]['title']}'")
        self.print(f"{'=' * 15} {self.data['user']} {'=' * 15}")

    def close(self):
        self._driver.close()


# Testing credentials
UNAME = ''
UPSWD = ''

if __name__ == '__main__':
    # Testing multi-threading capabilities
    import uuid
    for i in range(4):
        print(f'Starting parser #{i + 1}')
        Parser(uuid.uuid4().hex, UNAME, UPSWD, headless=False, verbose=True, databasereport=False).start()
