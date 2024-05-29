from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 열고자 하는 웹페이지 URL
driver.get("https://ticket.interpark.com/webzine/paper/TPNoticeList.asp?tid1=in_scroll&tid2=ticketopen&tid3=board_main&tid4=board_main")  

# 오픈티켓목록 iframe
iframe_content = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iFrmNotice")))
driver.switch_to.frame(iframe_content)

# 오픈티켓목록
tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "body > div > div > div.list > div.table > table > tbody > tr")))

for ticket in tickets: 
    # 제목
    event_name = ticket.find_element(By.CSS_SELECTOR, 'td.subject').text
    print("제목 : " + event_name)
    
    # 카테고리
    genre = ticket.find_element(By.CSS_SELECTOR, 'td.type').text
    print("카테고리 : " + genre)
    
    # 티켓오픈일
    ticket_open_date = ticket.find_element(By.CSS_SELECTOR, 'td.date').text
    print("티켓오픈일 : " + ticket_open_date)
    
    # 티켓링크 상세페이지
    detail_link = ticket.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute('href')

    # 상세페이지 열기
    driver.execute_script(f"window.open('{detail_link}','_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    time.sleep(3)
    
    # 티켓선예매
    pre_sale_date = ''
    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .poster > img').get_attribute('src')
    except:
        image_url = ''
    print("이미지 URL : " + image_url)
    
    # 등록일
    registration_date = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .btn .date > span').text
    print("등록일 : " + registration_date)
    
    # 공연정보
    try:
        basic_info = driver.find_element(By.CSS_SELECTOR, 'div.introduce').text
    except:
        basic_info = ''
    print("공연정보 : " + basic_info)
    
    # 할인정보
    try:
        info_discount = driver.find_element(By.CSS_SELECTOR, 'div.info_discount').text
    except:
        info_discount = ''
    print("할인정보 : " + info_discount)
    
    # 공연소개
    try:
        event_description = driver.find_element(By.CSS_SELECTOR, 'div.info1').text 
    except:
        event_description = ''
        infos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.info2")))
        for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "공연소개":
                event_description = info.text
    print("공연소개 : " + event_description)
    
    # 캐스팅
    try:
        infos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.info2")))
        for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "캐스팅":
                casting = info.text
    except:
        casting = ''
    print("캐스팅 : " + casting)
    
    # 기획사정보
    agency_info = ''
    for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "기획사정보":
                agency_info = info.text
    print("기획사정보 : " + agency_info)
    
   
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    iframe_content = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iFrmNotice")))
    driver.switch_to.frame(iframe_content)
    
    time.sleep(2)
    
# 웹 드라이버 종료
driver.quit()