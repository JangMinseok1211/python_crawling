import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time

# 데이터 전처리 함수
def convert_date(date_str):
    return datetime.strptime(date_str.strip(), "%Y.%m.%d").date()
    
def convert_datetime(datetime_str):
    # 요일 정보를 제거 > 정규 표현식 사용
    date_str = re.sub(r'\([^)]*\)', '', datetime_str)
    
    date_format = '%Y.%m.%d %H:%M'
    date_obj = datetime.strptime(date_str.strip(), date_format)
    date_db_format = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    print(date_db_format)
    return date_db_format

# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
service = Service()
driver = webdriver.Chrome(service=service)

# 열고자 하는 웹페이지 URL
driver.get("http://ticket.yes24.com/New/Notice/NoticeMain.aspx")

# 오픈일순 정렬
open_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#SelectOrder > a:nth-child(2)")))

driver.execute_script("arguments[0].click();", open_link)

time.sleep(3)

# 오픈티켓목록
tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#BoardList > div > table > tbody > tr")))

time.sleep(3)

for ticket in tickets[1:]: 
    # 제목
    event_name = ticket.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
    
    # 카테고리
    genre = ""
    
    # 상세페이지 열기
    link = ticket.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
    driver.execute_script(f"window.open('{link}','_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    time.sleep(3)
    
    # 티켓오픈일
    ticket_open_date = driver.find_element(By.CSS_SELECTOR, '#title1').text
    
    # 티켓선예매
    try:
        pre_sale_date = driver.find_element(By.CSS_SELECTOR, '#noti2 > div > span:nth-child(1)').text
    except:
        pre_sale_date = ''
    
    # 등록일
    registration_date = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-date > span:nth-child(1)').text
    
    # 불필요한 문자 삭제
    registration_date = registration_date[6:]
    print(registration_date)
    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-ticket > div > div.noti-vt-left > img').get_attribute('src')
    except:
        image_url = ''
    
    # 공연개요, 공연소개, 기획사
    infos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#NoticeRead > div.noti-view-con > div")))
    
    for info in infos:
        # 공연 개요
        if info.find_element(By.CSS_SELECTOR, 'p').text == "공연 개요":
            basic_info = info.find_element(By.CSS_SELECTOR, 'div').text
            
        # 공연 소개
        if info.find_element(By.CSS_SELECTOR, 'p').text == "공연 소개":
            event_description = info.find_element(By.CSS_SELECTOR, 'div').text
            
        # 기획사 정보
        if info.find_element(By.CSS_SELECTOR, 'p').text == "기획사 정보":
            agency_info = info.find_element(By.CSS_SELECTOR, 'div').text 
    
    try:
        detail_link = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-ticket > div > div.noti-vt-right > div.noti-vt-btns > a').get_attribute('href')
        
        # 상세페이지 들어가기
        driver.execute_script(detail_link)
        
        detail_link = driver.current_url
        
        # 공연날짜
        try:
            event_date = driver.find_element(By.CSS_SELECTOR, '#mainForm > div:nth-child(43) > div > div.rn-02 > div > p > span').text
            
            if '~' in event_date:
                event_start_date, event_end_date = event_date.split('~')
                event_start_date = convert_date(event_start_date)
                event_end_date = convert_date(event_end_date)
        except:
            event_start_date = None
            event_end_date = None
        
        
        # 장소와 주소
        venue = driver.find_element(By.CSS_SELECTOR, '#ps-location > span').text
        address = driver.find_element(By.CSS_SELECTOR, '#TheaterAddress').text
        
    except:
        detail_link = ''
    
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    time.sleep(2)
   
# 웹 드라이버 종료
driver.quit()
