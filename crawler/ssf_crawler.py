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
class SSFItem:
    name: str
    brand: str
    price: str
    discount: str
    img_url: str
    url: str
    id: str
    options: list

class SSFCrawler:
    def __init__(self, logger: log_manager.Logger):
        self.logger = logger
        self.file_manager = file_manager.FileManager()
        self.database = dict()
        self.items = list()
        
        self.database_init()
        self.file_manager.create_dir("./DB/SSF")
        self.file_manager.create_dir("./TEMP")
        
    def clear_data(self):
        self.database_init()
        self.items.clear()
    
    def database_init(self):
        self.database.clear()
        self.database["NAME"] = list()
        self.database["PRICE"] = list()
        self.database["DISCOUNT"] = list()
        self.database["SIZE"] = list()
        self.database["IMAGE"] = list()
        self.database["URL"] = list()
        
    def add_item_to_database(self, item: SSFItem):
        self.database["NAME"].append(item.name)
        self.database["PRICE"].append(item.price)
        self.database["DISCOUNT"].append(item.discount)
        
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
    
    def options_to_list(self, options: list):
        option_list = []
        for option in options:
            val = []
            val.append(option.size)
            val.append(option.is_soldout)
            option_list.append(val)
        
        return option_list

    def list_to_options(self, option_list: list):
        options = []
        for option in option_list:
            val = Option(option[0], option[1])
            options.append(val)

        return options
    
    def add_items_to_restock_check_list(self, brand):
        json_path = "./config/ssf/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)
        
        restock_check_list = data[brand]

        for item in self.items:
            restock_check_list.append([item.name, item.brand, item.img_url, item.url, item.id, False,  self.options_to_list(item.options)])
            
        data[brand] = restock_check_list

        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t", ensure_ascii=False)
    
    def get_restock_check_items(self, brand):
        json_path = "./config/ssf/restock_check_list.json"
        with open(json_path, encoding='UTF-8') as file:
            data = json.load(file)

        restock_check_list = data[brand]
        restock_list = []
        
        for item in restock_check_list:
            if item[5] == True:
                restock_item = SSFItem(name=item[0], brand=item[1], price="", discount="", img_url=item[2], url=item[3], id=item[4], options=self.list_to_options(item[6]))
                restock_list.append(restock_item)
                
        return restock_list
        
    def set_latest_item(self, json_path, brand, latest_item_url):
        with open(json_path) as file:
            data = json.load(file)
            
        data[brand] = latest_item_url
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent="\t")
    
    def get_last_page(self, total_item_cnt):
        last_page = 1
        last_page = total_item_cnt // 60
        remain = total_item_cnt % 60
        if remain != 0:
            last_page += 1
        self.logger.log_debug(f"SSF : Total {last_page} of pages ")
        return last_page
    
    def find_items_in_list(self, driver_obj: web_driver_manager.Driver, url, latest_item_id):
        items = []
        driver = driver_obj.driver
        
        driver_obj.get_page(url)
        total_item_cnt = driver.find_element(By.ID, "godTotalCount").text
        
        last_page = self.get_last_page(int(total_item_cnt))
        
        for i in range(1, last_page+1):
            page_url = f"{url}&currentPage={i}"
            driver_obj.get_page(page_url)
            
            item_list = driver.find_element(By.ID, "dspGood").find_elements(By.TAG_NAME, "li")

            for item in item_list:
                item_info = []
                item_info_element = item.find_element(By.CLASS_NAME, "info")
                
                name = item_info_element.find_element(By.CLASS_NAME, "name").text
                brand = item_info_element.find_element(By.CLASS_NAME, "brand").text
                img_url = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                id = item.get_attribute('data-prdno')
                
                if latest_item_id == id:
                    return items
                
                brand_str = brand.replace(" ", "-")
                
                script_line = f"javascript:goToProductDetail('{brand_str}', '{item.get_attribute('data-prdno')}','1',this,'godList');"
                
                sff_item = SSFItem(name=name, brand=brand, price="", discount="", img_url=img_url, url="", id=id, options=[])
                
                item_info.append(sff_item)
                item_info.append(script_line)
                
                items.append(item_info)

        return items
    
    def get_item_detail_info(self, driver_obj: web_driver_manager.Driver, script_line=None, ssf_item=None, url=None):
        driver = driver_obj.driver
        if script_line:
            driver.execute_script(script_line)
        else:
            driver.get(url)
        options = []
        
        item_price = ""
        item_discount = ""
        
        if driver_obj.is_element_exist(By.CLASS_NAME, 'cost'):
            item_price = driver.find_element(By.CLASS_NAME, 'cost').find_element(By.TAG_NAME, "del").text
            item_price = item_price + "원"
            
            item_discount = driver.find_element(By.CLASS_NAME, 'price').text
            item_discount = item_discount + "원"
        else:
            item_price = driver.find_element(By.CLASS_NAME, 'price').text  + "원"
            
        ssf_item.price = item_price
        ssf_item.discount = item_discount
        
        if driver_obj.is_element_exist(By.XPATH, '//*[@id="content"]/section/div[2]/div[2]/div[6]/div[1]/div/ul'):
            option_elements = driver.find_element(By.XPATH, '//*[@id="content"]/section/div[2]/div[2]/div[6]/div[1]/div/ul').find_elements(By.NAME, "sizeItmNo")
            for option_element in option_elements:
                option_text = ""
                option_attr = option_element.get_attribute("itmstatcd")
                option_soldout = False
                if option_attr == "SLDOUT":
                    option_soldout = True
                option = Option(size=option_text, is_soldout=option_soldout)
                options.append(option)
            
            option_elements = driver.find_element(By.XPATH, '//*[@id="content"]/section/div[2]/div[2]/div[6]/div[1]/div/ul').find_elements(By.TAG_NAME, "li")
            for i in range(len(option_elements)):
                option_text = option_elements[i].find_element(By.TAG_NAME, "label").text
                options[i].size = option_text
        
        ssf_item.options = options
        ssf_item.url = driver.current_url
        
        return ssf_item
    
    def get_new_items(self, driver_obj: web_driver_manager.Driver, brand, url, driver_manager, webhook_url):
        json_path = ".\config\ssf\latest_item_info.json"
        latest_item_url = self.get_latest_item(json_path, brand)
        new_items = self.find_items_in_list(driver_obj, url, latest_item_url)
        if len(new_items) != 0:
            self.set_latest_item(json_path, brand, new_items[0][0].id)
        
        self.logger.log_info(f"SSF_{brand}: 총 {len(new_items)}개의 신상품을 발견 하였습니다.")
        for i in range(len(new_items)):
            new_item = new_items[i][0]
            script_line = new_items[i][1]
            item = self.get_item_detail_info(driver_obj, script_line, new_item)
            driver_obj.driver.back()
            self.logger.log_info(f"신상품 {item.name}의 정보 수집을 완료하였습니다.")
            self.items.append(item)
            self.add_item_to_database(item)
            self.send_discord_web_hook(driver_manager, item, webhook_url)
        
        self.add_items_to_restock_check_list(brand)
        restock_item_list = self.get_restock_check_items(brand)
        self.logger.log_info(f"SFF_{brand} : 총 {len(restock_item_list)}개의 재고 확인 상품을 발견 하였습니다.")
        for restock_item in restock_item_list:
            prev_option = restock_item.options
            item = self.get_item_detail_info(driver_obj, url=restock_item.url, ssf_item=restock_item)
            driver_obj.driver.back()
            if prev_option != item.options:
                self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 수집을 완료하였습니다.")
                self.items.append(item)
                self.add_item_to_database(item)
                self.send_discord_web_hook(driver_manager, item, webhook_url)
            else:
                self.logger.log_info(f"재고 확인 상품 {restock_item.name}의 정보 변경 사항이 없습니다.")
        
    def save_db_data_as_excel(self, save_path, file_name):
        data_frame = pd.DataFrame(self.database)
        data_frame.to_excel(f"{save_path}/{file_name}.xlsx", index=False)
    
    def send_discord_web_hook(self, driver_manager, ssf_item: SSFItem, webhook_url):
        driver_manager.download_image(img_url=ssf_item.img_url, img_name="thumbnail", img_path="./TEMP", download_cnt=0)
        webhook = DiscordWebhook(url=webhook_url)
        embed = DiscordEmbed(title=ssf_item.name, url=ssf_item.url)
        with open("./TEMP/thumbnail.jpg", "rb") as f:
            webhook.add_file(file=f.read(), filename="thumbnail.jpg")
        embed.set_author(name="SSF_RESTOCK")
        embed.set_thumbnail(url="attachment://thumbnail.jpg")
        embed.add_embed_field(name="Brand", value=ssf_item.brand)
        if ssf_item.discount == "":
            embed.add_embed_field(name="Price", value=ssf_item.price)
        else:
            embed.add_embed_field(name="Price", value=ssf_item.price)
            embed.add_embed_field(name="Discount", value=ssf_item.discount)
        
        size_field_value = ""
        for option in ssf_item.options:
            option_value = option.size
            
            if option.is_soldout:
                option_value += "[:red_circle:] "
            else:
                option_value += "[:green_circle:] "
            
            size_field_value += option_value
        embed.add_embed_field(name="Option", value=size_field_value)
        embed.set_footer(text="AMNotify KR")
        embed.set_timestamp()
        webhook.add_embed(embed)
        webhook.execute()
        del webhook
        del embed
        time.sleep(1)
    
    def start_task(self, driver_manager: web_driver_manager.WebDriverManager, save_date, brand, brand_url, webhook_url):
        
        self.file_manager.create_dir(f"./DB/SSF/{brand}")
        
        driver_obj = driver_manager.drive_obj
        
        self.get_new_items(driver_obj, brand, brand_url, driver_manager, webhook_url)
        
        if len(self.items) != 0:
            self.save_db_data_as_excel(f"./DB/SSF/{brand}", f"{save_date}_{brand}")
            
        self.clear_data()