from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from dataclasses import dataclass
import zipfile
import requests
import os

from manager import log_manager

@dataclass
class Proxy:
    host: str
    port: str
    username: str
    password: str
    
class Driver:
    def __init__(self, logger: log_manager.Logger, driver: WebDriver, proxy: Proxy):
        self.logger = logger
        self.driver = driver
        self.proxy = proxy
        
    def get_page(self, url, max_wait_time=30):
        is_page_loaded = False
        cnt = 0
        while(is_page_loaded == False):
            if cnt >= 10:
                break
            try:
                self.driver.implicitly_wait(30)
                self.driver.get(url)
                self.logger.log_debug(f"Get *{url}* page")
                is_page_loaded = True
            except Exception as e:
                self.logger.log_debug(f"Page load failed : {e}")
                is_page_loaded = False
                cnt += 1
    
    def is_element_exist(self, by, value, element=None):
        self.driver.implicitly_wait(5)
        is_exist = False
        try:
            if element != None:
                element.find_element(by, value)
            else:
                self.driver.find_element(by, value)
            is_exist = True
        except NoSuchElementException:
            is_exist = False
        return is_exist
    
    def __del__(self):
        self.driver.quit()
        del self.driver


class WebDriverManager():
    def __init__(self, logger: log_manager.Logger):
        self.logger = logger
        self.drive_obj = None
            
    def create_driver(self, user_agent=None, proxy=None, is_headless=False, is_udc=False, enable_img_loading=False):
        chrome_options = webdriver.ChromeOptions()
        
        if proxy:
            PROXY_HOST = proxy.host  # rotating proxy or host
            PROXY_PORT = proxy.port # port
            PROXY_USER = proxy.username # username
            PROXY_PASS = proxy.password # password

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        
            pluginfile = './config/proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
        
        if user_agent:
            chrome_options.add_argument('--user-agent=%s' % user_agent)
        
        if is_headless:
            chrome_options.add_argument('headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option('excludeSwitches', ['disable-popup-blocking'])
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        service = Service(excutable_path=ChromeDriverManager().install())

        driver = webdriver.Chrome(options=chrome_options, service=service)
        driver.minimize_window()
        
        log_msg = ""
        if proxy:
            log_msg = f"Driver created with proxy({proxy.host}:{proxy.port})"
        else:
            log_msg = f"Driver created without proxy"
        
        self.logger.log_debug(log_msg)
        self.drive_obj = Driver(self.logger, driver, proxy)
        return self.drive_obj
    
    def download_image(self, img_url, img_name, img_path, download_cnt, proxy=None):
        min_size = 50
        
        #만약 다운로드 시도횟수가 5번을 넘는다면 다운로드 불가능한 이미지로 간주
        if download_cnt > 5:
            self.logger.log_debug(f"Img size is under {min_size}KB or cannot download image \'{img_name}\'")
            return
        try:
            if proxy:
                proxy_str = f"{proxy[0]}:{proxy[1]}:{proxy[2]}:{proxy[3]}"
                r = requests.get(img_url,headers={'User-Agent': 'Mozilla/5.0'}, timeout=20, proxies={'http':proxy_str,'https':proxy_str})
            else:
                r = requests.get(img_url,headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
            with open(f"{img_path}/{img_name}.jpg", "wb") as outfile:
                outfile.write(r.content)
        except Exception as e:
            self.logger.log_debug(f"Image \'{img_url}\' download failed with error : {e}")
            return
        #KB 단위의 이미지 사이즈
        img_size = os.path.getsize(f"{img_path}/{img_name}.jpg") / 1024

        #만약 이미지 크기가 일정 크기 이하라면 다운로드가 실패한것으로 간주, 다시 다운로드
        if img_size < min_size:
            self.logger.log_debug(f"Image \'{img_url}\' download failed")
            self.download_image(img_url, img_name, img_path, download_cnt + 1)
        else:
            self.logger.log_debug(f"Image \'{img_url}\' download completed")
        return
    
    def delete_driver(self):
        if self.drive_obj != None:
            del self.drive_obj
            self.drive_obj = None
            self.logger.log_debug("Driver deleted")
            
    def __del__(self):
        self.delete_driver()