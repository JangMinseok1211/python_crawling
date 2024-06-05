import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
import time

# 데이터 전처리 함수
def convert_date(date_str):
    return datetime.strptime(date_str.strip(), "%Y.%m.%d").date()
    
def convert_datetime(datetime_str):
    # 요일 정보를 제거 > 정규 표현식 사용
    date_str = re.sub(r'\([^)]*\)', '', datetime_str)
    # 오전/오후를 AM/PM으로 변환
    date_str = date_str.replace('오전', 'AM').replace('오후', 'PM')
    
    date_format = '%Y년 %m월 %d일 %p %I시'
    date_obj = datetime.strptime(date_str.strip(), date_format)
    date_db_format = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return date_db_format
  
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
    #카테고리가 사이트공지 일경우 크롤링 하지 않음
    if genre == '사이트공지' :
        continue
    print("카테고리 : " + genre)
    

    
    # 티켓링크 상세페이지
    detail_link = ticket.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute('href')

    # 상세페이지 열기
    driver.execute_script(f"window.open('{detail_link}','_blank');")
    driver.switch_to.window(driver.window_handles[1])
    
    time.sleep(2)
    
    # 티켓선예매
    pre_sale_date = ''
    
    # 티켓오픈일 추출
    try:
        open_date_text = driver.find_element(By.CSS_SELECTOR, '#wrapBody > div > div > div.board > div.detail_top > div.info > ul > li.open').text
        open_date_text = open_date_text.replace('티켓오픈일', '').strip()  # '티켓오픈일' 제거
        ticket_open_date = convert_datetime(open_date_text)
        print(f"티켓오픈일: {ticket_open_date}")
    except Exception as e:
        print(f"티켓오픈일 추출 중 오류 발생: {e}")
        ticket_open_date = None
    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .poster > img').get_attribute('src')
    except:
        image_url = ''
    print("이미지 URL : " + image_url)
    
    # 등록일
    registration_date_str = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .btn .date > span').text
    registration_date = convert_date(registration_date_str)
    print("등록일 : " + registration_date.strftime("%Y-%m-%d"))
    
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
    
    # 상세보기 링크 추출
    try:
        detail_url = driver.find_element(By.CSS_SELECTOR, 'a.btn_book').get_attribute('href')
    except:
        detail_url = detail_link
    print("상세보기 링크 : " + detail_url)

    #상세보기 링크 페이지로 접속
    driver.execute_script(f"window.open('{detail_url}','_blank');")
    driver.switch_to.window(driver.window_handles[2])
    
    time.sleep(2)
    
    # 공연 기간 추출
    try:
        period_text = driver.find_element(By.CSS_SELECTOR, '#container > div.contents > div.productWrapper > div.productMain > div.productMainTop > div > div.summaryBody > ul > li:nth-child(2) > div > p').text

        if '~' in period_text:
            event_start_date, event_end_date = period_text.split('~')
            event_start_date = convert_date(event_start_date)
            event_end_date = convert_date(event_end_date)

    except: 
        event_start_date = None
        event_end_date = None
    print(f"공연기간: {event_start_date} ~ {event_end_date}")
    
    venue = driver.find_element(By.CSS_SELECTOR, '#container > div.contents > div.productWrapper > div.productMain > div.productMainTop > div > div.summaryBody > ul > li:nth-child(1) > div > a').text
    venue = venue[:-5] #불필요한 문장 삭제 
    print(f'장소: {venue}')

    # 공연장 정보 팝업 클릭 및 주소 추출
    try:
        info_btn = driver.find_element(By.CSS_SELECTOR, '.infoBtn[data-popup="info-place"]')
        info_btn.click()
        time.sleep(2)  # 팝업이 로드될 시간을 주기 위해 대기
        address = driver.find_element(By.CSS_SELECTOR, '#popup-info-place > div > div.popupBody > div > div.popPlaceInfo > p > span').text
        print(f'주소: {address}')
    except Exception as e:
        address = ''
        print(f"Error retrieving address: {e}")
        
    # 현재 탭을 닫음
    driver.close()
    driver.switch_to.window(driver.window_handles[1])

    # 데이터베이스에 삽임


    
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    iframe_content = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iFrmNotice")))
    driver.switch_to.frame(iframe_content)
    
    time.sleep(2)
    
# 웹 드라이버 종료
driver.quit()
