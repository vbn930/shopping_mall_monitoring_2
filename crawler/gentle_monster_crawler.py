from dataclasses import dataclass
from manager import file_manager
from manager import web_driver_manager
from manager import log_manager
import json
import pandas as pd
import time

from selenium.webdriver.common.by import By
from discord_webhook import DiscordWebhook, DiscordEmbed

@dataclass
class Option:
    size: str
    is_soldout: bool

@dataclass
class GentleMonsterItem:
    name: str
    price: str
    discount: str
    img_url: str
    url: str
    options: list

class GentleMonsterCrawler:
    def __init__(self, logger: log_manager.Logger):
        self.logger = logger
        self.file_manager = file_manager.FileManager()
        self.database = dict()
        self.items = list()
        
        self.database_init()
        self.file_manager.create_dir("./DB/GentleMonster")
        self.file_manager.create_dir("./TEMP")
        
    def clear_data(self):
        self.database_init()
        self.items.clear()
    
    def database_init(self):
        self.database.clear()
        self.database["NAME"] = list()
        self.database["PRICE"] = list()
        self.database["RESTOCK"] = list()
        self.database["SIZE"] = list()
        self.database["IMAGE"] = list()
        self.database["URL"] = list()
        
    def add_item_to_database(self, item: GentleMonsterItem):
        self.database["NAME"].append(item.name)
        self.database["PRICE"].append(item.price)
        self.database["RESTOCK"].append(item.discount)
        
        size_str = ""
        for option in item.options:
            text = option.size
            if option.is_soldout:
                text += "(품절)"

            size_str += text
            if option.size != item.options[-1].size:
                size_str += ", "
        
        self.database["SIZE"].append(size_str)
        self.database["IMAGE"].append(item.img_url)
        self.database["URL"].append(item.url)
        
    def get_latest_item(self, json_path, brand):
        with open(json_path) as file:
            data = json.load(file)
            
        latest_item_url = ""
        
        if brand in data:
            latest_item_url = data[brand]
        else:
            data[brand] = latest_item_url
        
        return latest_item_url
    
    def add_items_to_restock_check_list(self, brand):
        json_path = "./config/gentle_monster/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)
        
        restock_check_list = data[brand]
        for item in self.items:
            restock_check_list.append([item.name, item.img_url, item.url, False, item.discount])
            
        data[brand] = restock_check_list
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t", ensure_ascii=False)
    
    def get_restock_check_items(self, brand):
        json_path = "./config/gentle_monster/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)

        restock_check_list = data[brand]
        restock_list = []
        
        for item in restock_check_list:
            if item[3] == True:
                restock_item = GentleMonsterItem(name=item[0], price="", discount=item[4], img_url=item[1], url=item[2], options=[])
                restock_list.append(restock_item)
                
        return restock_list
        
    def set_latest_item(self, json_path, brand, latest_item_url):
        with open(json_path) as file:
            data = json.load(file)
            
        data[brand] = latest_item_url
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t")
    
    def find_items_in_list(self, driver_obj: web_driver_manager.Driver, url, latest_item_url):
        driver = driver_obj.driver
        driver.maximize_window()
        driver_obj.get_page(url)
        
        time.sleep(5)
        
        if driver_obj.is_element_exist(By.ID, "onetrust-accept-btn-handler"):
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
        
        #스크롤 내리기 전 위치
        scroll_location = driver.execute_script("return document.body.scrollHeight")

        while True:
            items = []
            
            #현재 스크롤의 가장 아래로 내림
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

            product_elements = driver.find_element(By.CLASS_NAME, "product-list__wrapper.inline").find_elements(By.TAG_NAME, "li")
            for product_element in product_elements:
                item_details = product_element.find_element(By.CLASS_NAME, "product__link")
                name = item_details.get_attribute("product-name")
                item_url = item_details.get_attribute("href")
                if latest_item_url == item_url:
                    driver.minimize_window()
                    return items
                item = GentleMonsterItem(name=name, price="", discount="", img_url="", url=item_url, options=[])
                items.append(item)
            
            #전체 스크롤이 늘어날 때까지 대기
            time.sleep(10)

            #늘어난 스크롤 높이
            scroll_height = driver.execute_script("return document.body.scrollHeight")

            #늘어난 스크롤 위치와 이동 전 위치 같으면(더 이상 스크롤이 늘어나지 않으면) 종료
            if scroll_location == scroll_height:
                break

            #같지 않으면 스크롤 위치 값을 수정하여 같아질 때까지 반복
            else:
                #스크롤 위치값을 수정
                scroll_location = driver.execute_script("return document.body.scrollHeight")
        driver.minimize_window()
        return items
    
    def get_item_detail_info(self, driver_obj: web_driver_manager.Driver, item_url):
        driver = driver_obj.driver
        driver_obj.get_page(item_url)
        options = []
        
        item_price = driver.find_element(By.CLASS_NAME, 'product-info__top.clearfix').find_element(By.TAG_NAME, "div").text
        if driver_obj.is_element_exist(By.CLASS_NAME, "detail__btn-list"):
            item_discount = driver.find_element(By.CLASS_NAME, "detail__btn-list").text
            if "품절" in item_discount:
                item_discount = "품절"
            else:
                item_discount = "구매 가능"
        else:
            item_discount = "재입고 예정"
        img_url = driver.find_element(By.XPATH, '//*[@id="container_sq"]/div[1]/div/div[1]/div[1]/div/div[1]/div/img').get_attribute("src")
        
        return options, item_price, item_discount, img_url
    
    def get_new_items(self, driver_obj: web_driver_manager.Driver, brand, url, driver_manager, webhook_url):
        json_path = ".\config\gentle_monster\latest_item_info.json"
        latest_item_url = self.get_latest_item(json_path, brand)
        new_items = self.find_items_in_list(driver_obj, url, latest_item_url)
        self.items += new_items
        if len(new_items) != 0:
            self.set_latest_item(json_path, brand, new_items[0].url)
        
        self.logger.log_info(f"Gentle Monster_{brand} : 총 {len(self.items)}개의 신상품을 발견 하였습니다.")
        for i in range(len(self.items)):
            item_option, item_price, item_discount, item_img_url = self.get_item_detail_info(driver_obj, self.items[i].url)
            self.items[i].options = item_option
            self.items[i].price = item_price
            self.items[i].img_url = item_img_url
            self.items[i].discount = item_discount
            self.logger.log_info(f"신상품 {self.items[i].name}의 정보 수집을 완료하였습니다.")
            self.add_item_to_database(self.items[i])
            self.send_discord_web_hook(driver_manager, self.items[i], webhook_url)
        
        self.add_items_to_restock_check_list(brand)
        restock_item_list = self.get_restock_check_items(brand)
        self.logger.log_info(f"Gentle Monster_{brand} : 총 {len(restock_item_list)}개의 재고 확인 상품을 발견 하였습니다.")
        for restock_item in restock_item_list:
            item_option, item_price, item_discount, item_img_url = self.get_item_detail_info(driver_obj, restock_item.url)
            if restock_item.options != item_option:
                restock_item.options = item_option
                restock_item.price = item_price
                restock_item.img_url = item_img_url
                restock_item.discount = item_discount
                self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 수집을 완료하였습니다.")
                self.items.append(restock_item)
                self.add_item_to_database(restock_item)
                self.send_discord_web_hook(driver_manager, restock_item, webhook_url)
            else:
                self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 변경 사항이 없습니다.")
        
    def save_db_data_as_excel(self, save_path, file_name):
        data_frame = pd.DataFrame(self.database)
        data_frame.to_excel(f"{save_path}/{file_name}.xlsx", index=False)
        
    def send_discord_web_hook(self, driver_manager, newitem: GentleMonsterItem, webhook_url):
        driver_manager.download_image(img_url=newitem.img_url, img_name="thumbnail", img_path="./TEMP", download_cnt=0)
        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(title=newitem.name, url=newitem.url)
        with open("./TEMP/thumbnail.jpg", "rb") as f:
            webhook.add_file(file=f.read(), filename="thumbnail.jpg")
        embed.set_author(name="GENTLE_MONSTER_RESTOCK")
        embed.set_thumbnail(url="attachment://thumbnail.jpg")
        if newitem.discount == "":
            embed.add_embed_field(name="Price", value=newitem.price)
        else:
            embed.add_embed_field(name="Price", value=newitem.price)
            embed.add_embed_field(name="Restock", value=newitem.discount)
        
        embed.set_footer(text="AMNotify KR")
        embed.set_timestamp()
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
        
    def start_task(self, driver_manager: web_driver_manager.WebDriverManager, save_date, brand, brand_url, webhook_url):
        
        self.file_manager.create_dir(f"./DB/GentleMonster/{brand}")
        
        driver_obj = driver_manager.drive_obj
        
        self.get_new_items(driver_obj, brand, brand_url, driver_manager, webhook_url)
        
        if len(self.items) != 0:
            self.save_db_data_as_excel(f"./DB/GentleMonster/{brand}", f"{save_date}_{brand}")
            
        self.clear_data()