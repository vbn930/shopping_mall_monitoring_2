from manager import web_driver_manager
from manager import log_manager
from manager import resource_monitor_manager
from crawler import kakao_crawler
from crawler import ssf_crawler
from crawler import gentle_monster_crawler

import datetime
import json
import time

# pyinstaller -n "KAKAO_SSF_GENTLEMONSTER_MONITORING_PROGRAM_1.2" --clean --onefile main.py

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
    
    # Kakao
    with open(f"./config/kakao/restock_check_list.json", encoding='UTF-8') as file:
        restock_dict = json.load(file)
    
    logger.log_info(f"카카오 선물하기 브랜드 총 {len(kakao_datas)}개를 발견 하였습니다!")
    for kakao_data in kakao_datas:
        logger.log_info(f"카카오 선물하기 브랜드 {kakao_data[0]}의 설정 값을 성공적으로 세팅했습니다.")
        if kakao_data[0] not in restock_dict:
            restock_dict[kakao_data[0]] = list()
        
    with open(f"./config/kakao/restock_check_list.json", 'w', encoding='utf-8') as file:
        json.dump(restock_dict, file, indent="\t")
    
    # SSF
    with open(f"./config/ssf/restock_check_list.json", encoding='UTF-8') as file:
        restock_dict = json.load(file)  
    
    logger.log_info(f"SSF 브랜드 총 {len(ssf_datas)}개를 발견 하였습니다!")
    for ssf_data in ssf_datas:
        logger.log_info(f"SSF 브랜드 {ssf_data[0]}의 설정 값을 성공적으로 세팅했습니다.")
        if ssf_data[0] not in restock_dict:
            restock_dict[ssf_data[0]] = list()
    
    with open(f"./config/ssf/restock_check_list.json", 'w', encoding='utf-8') as file:
        json.dump(restock_dict, file, indent="\t")
    
    # gentle_monster
    with open(f"./config/gentle_monster/restock_check_list.json", encoding='UTF-8') as file:
        restock_dict = json.load(file)  
    
    logger.log_info(f"Gentle Monster 브랜드 총 {len(gentle_monster_datas)}개를 발견 하였습니다!")    
    for gentle_monster_data in gentle_monster_datas:
        logger.log_info(f"Gentle Monster 브랜드 {gentle_monster_data[0]}의 설정 값을 성공적으로 세팅했습니다.")
        if gentle_monster_data[0] not in restock_dict:
            restock_dict[gentle_monster_data[0]] = list()
    
    with open(f"./config/gentle_monster/restock_check_list.json", 'w', encoding='utf-8') as file:
        json.dump(restock_dict, file, indent="\t")
        
    return kakao_datas, ssf_datas, gentle_monster_datas, proxy_objs, wait_time

def run_monitoring(logger: log_manager.Logger, resource_monitor: resource_monitor_manager.ResourceMonitor,
                   driver_manager: web_driver_manager.WebDriverManager, 
                   kakao: kakao_crawler.KakaoCrawler, ssf: ssf_crawler.SSFCrawler, gentle_monster: gentle_monster_crawler.GentleMonsterCrawler,
                   kakao_datas, ssf_datas, gentle_monster_datas, proxies):
    
    driver_obj = None
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    if len(proxies) != 0:
        curr_proxy = proxies.pop(0)
        driver_obj = driver_manager.create_driver(proxy=curr_proxy, user_agent=user_agent)
        proxies.append(curr_proxy)
    else:
        driver_obj = driver_manager.create_driver(user_agent=user_agent)
     
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    logger.log_info("카카오 선물하기 크롤링을 시작합니다!")
    for kakao_data in kakao_datas:
        logger.log_info(f"카카오 선물하기의 {kakao_data[0]} 브랜드 크롤링을 시작합니다!")
        kakao.start_task(driver_manager=driver_manager, save_date=f"{year}{month}{day}{hour}{minute}", brand=kakao_data[0], brand_url=kakao_data[1], webhook_url=kakao_data[2])
        
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    logger.log_info("SSF 크롤링을 시작합니다!")    
    for ssf_data in ssf_datas:
        logger.log_info(f"SSF의 {ssf_data[0]} 브랜드 크롤링을 시작합니다!")
        ssf.start_task(driver_manager=driver_manager, save_date=f"{year}{month}{day}{hour}{minute}", brand=ssf_data[0], brand_url=ssf_data[1], webhook_url=ssf_data[2])
        
    now = datetime.datetime.now()
    year = f"{now.year}"
    month = "%02d" % now.month
    day = "%02d" % now.day
    hour = "%02d" % now.hour
    minute = "%02d" % now.minute
    
    logger.log_info("Gentle Monster 크롤링을 시작합니다!")
    for gentle_monster_data in gentle_monster_datas:
        logger.log_info(f"Gentle Monster의 {gentle_monster_data[0]} 브랜드 크롤링을 시작합니다!")
        gentle_monster.start_task(driver_manager=driver_manager, save_date=f"{year}{month}{day}{hour}{minute}", brand=gentle_monster_data[0], brand_url=gentle_monster_data[1], webhook_url=gentle_monster_data[2])
    
    driver_manager.delete_driver()
    resource_monitor.print_current_resource_usage()

    logger.save_log()

def run_resource_monitoring(resource_monitor: resource_monitor_manager.ResourceMonitor):
    resource_monitor.print_current_resource_usage()

if __name__ == '__main__':
    # logger = log_manager.Logger(log_manager.LogType.DEBUG)
    # driver_manager = web_driver_manager.WebDriverManager(logger)
    # hoopcity = hoopcity_crawler.HoopcityCrawler(logger)
    # kasina = kasina_crawler.KasinaCrawler(logger)
    # resource_monitor = resource_monitor_manager.ResourceMonitor(logger)
        
    # hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies, wait_time = get_initial_setting_from_config(logger, "./config/config.json")
        
    # run_monitoring(logger, resource_monitor, driver_manager, hoopcity, kasina, hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies)
    
    try:
        logger = log_manager.Logger(log_manager.LogType.BUILD)
        driver_manager = web_driver_manager.WebDriverManager(logger)
        kakao = kakao_crawler.KakaoCrawler(logger)
        ssf = ssf_crawler.SSFCrawler(logger)
        gentle_monster = gentle_monster_crawler.GentleMonsterCrawler(logger)
        resource_monitor = resource_monitor_manager.ResourceMonitor(logger)
        
        kakao_datas, ssf_datas, gentle_monster_datas, proxy_objs, wait_time = get_initial_setting_from_config(logger)
        
        # schedule.every(wait_time).minutes.do(run_monitoring, logger, resource_monitor, driver_manager, hoopcity, kasina, discord_webhook_url, proxies)
        # schedule.every(5).minutes.do(run_resource_monitoring, resource_monitor)
        
        # run_monitoring(logger, resource_monitor, driver_manager, hoopcity, kasina, hoopcity_discord_webhook_url, kasina_discord_webhook_url, proxies)

        while True:
            # schedule.run_pending()
            run_monitoring(logger=logger, resource_monitor=resource_monitor, driver_manager=driver_manager, 
                           kakao=kakao, ssf=ssf, gentle_monster=gentle_monster, kakao_datas=kakao_datas, ssf_datas=ssf_datas, gentle_monster_datas=gentle_monster_datas, 
                           proxies=proxy_objs)
            logger.log_info(f"다음 정보 신상품 정보 수집까지 {wait_time}분 대기합니다.")
            time.sleep(wait_time*60)
    
    except Exception as e:
        logger.log_error(f"다음과 같은 오류로 프로그램을 종료합니다. : {e}")
    
    logger.log_info(f"프로그램을 종료하시려면 아무 키나 입력해주세요.")
    end = input("")