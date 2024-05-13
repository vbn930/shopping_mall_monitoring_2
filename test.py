from manager import web_driver_manager
from manager import log_manager
from manager import resource_monitor_manager
from crawler import ssf_crawler
from crawler import kakao_crawler
from crawler import gentle_monster_crawler

import datetime
import json
import time
from discord_webhook import DiscordWebhook, DiscordEmbed


def get_initial_setting_from_config(logger: log_manager.Logger):
    with open(".\config\kakao\kakao_config.json") as file:
        kakao_data = json.load(file)
    kakao_datas = kakao_data["information"]
    
    with open(".\config\ssf\ssf_config.json") as file:
        ssf_data = json.load(file)
    ssf_datas = ssf_data["information"]
    
    with open(".\config\gentle_monster\gentle_monster_config.json") as file:
        gentle_monster_data = json.load(file)
    gentle_monster_datas = gentle_monster_data["information"]
    
    with open(".\config\config.json") as file:
        config_data = json.load(file)
    
    proxies = config_data["proxies"]
    wait_time = config_data["wait_time"]
    
    proxy_objs = []
    for proxy in proxies:
        proxy_info = proxy.split(":")
        proxy_obj = web_driver_manager.Proxy(proxy_info[0], proxy_info[1], proxy_info[2], proxy_info[3])
        proxy_objs.append(proxy_obj)
    
    # restock_dict = dict()
    # for kakao_data in kakao_datas:
    #     restock_dict[kakao_data[0]] = list()
        
    # with open(f"./config/kakao/restock_check_list.json", 'w', encoding='utf-8') as file:
    #     json.dump(restock_dict, file, indent="\t")
    
    # restock_dict = dict()    
    # for ssf_data in ssf_datas:
    #     restock_dict[ssf_data[0]] = list()
    
    # with open(f"./config/ssf/restock_check_list.json", 'w', encoding='utf-8') as file:
    #     json.dump(restock_dict, file, indent="\t")
        
    # restock_dict = dict()
    # for gentle_monster_data in gentle_monster_datas:
    #     restock_dict[gentle_monster_data[0]] = list()
    
    # with open(f"./config/gentle_monster/restock_check_list.json", 'w', encoding='utf-8') as file:
    #     json.dump(restock_dict, file, indent="\t")
        
    return kakao_datas, ssf_datas, gentle_monster_datas, proxy_objs, wait_time

logger = log_manager.Logger(log_manager.LogType.DEBUG)
driver_manager = web_driver_manager.WebDriverManager(logger)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
driver_obj = driver_manager.create_driver(user_agent=user_agent)
kakao_datas, ssf_datas, gentle_monster_datas, proxy_objs, wait_time = get_initial_setting_from_config(logger=logger)

# items = kakao.find_items_in_list(driver_obj, "https://gift.kakao.com/brand/10941", "")

ssf = ssf_crawler.SSFCrawler(logger)
#kakao = kakao_crawler.KakaoCrawler(logger)
#gentle_monster = gentle_monster_crawler.GentleMonsterCrawler(logger)

# items = gentle_monster.find_items_in_list(driver_obj, "https://www.gentlemonster.com/kr/shop/list/collaborations/view-all?order=newest", "https://www.gentlemonster.com/kr/shop/item/aile-m/G2VTMNG0X3QP")

# for item in items:
#     gentle_monster.get_item_detail_info(driver_obj, item.url)

for ssf_data in ssf_datas:
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    ssf.start_task(driver_manager, f"{year}{month}{day}{hour}{minute}", ssf_data[0], ssf_data[1], ssf_data[2])

