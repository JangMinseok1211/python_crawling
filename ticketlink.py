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

# 예매 안내 팝업 닫기 함수
def close_popup(driver):
    try:
        close_button = driver.find_element(By.CSS_SELECTOR, '#app > div.common_modal_wrap > div.common_modal > div.common_modal_footer > button')
        close_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass
    except Exception as e:
        print(f"Unexpected error when trying to close popup: {e}")
        
# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 열고자 하는 웹페이지 URL
driver.get("https://www.ticketlink.co.kr/help/notice#TICKET_OPEN")

# 오픈티켓목록
tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.basic_tbl > table > tbody > tr")))

for ticket in tickets:
    
    #제목
    event_name = ticket.find_element(By.CSS_SELECTOR, 'td.tl.p_reative').text
    print("제목 : " + event_name)
    
    # 상세페이지 열기
    link = ticket.find_element(By.CSS_SELECTOR, 'td.tl.p_reative > a').get_attribute('href')
    driver.execute_script(f"window.open('{link}','_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    
    time.sleep(3)
    
    # 티켓선예매
    pre_sale_date = ''
    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dt > dl > dd.thumb > img').get_attribute('src')
    except:
        image_url = ''
    print("이미지 URL : " + image_url)
    
    # 티켓오픈일
    ticket_open_date = convert_datetime(driver.find_element(By.CSS_SELECTOR, '#ticketOpenDatetime').text)
    
    # 등록일
    registration_date = convert_datetime(driver.find_element(By.CSS_SELECTOR, '#registerDatetime').text)
    
    # 상세페이지(예매)
    try:
        detail_link = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dt > dl > dd:nth-child(9) > a').get_attribute('href')
        
        # 상세페이지 들어가기
        driver.execute_script(f"window.open('{detail_link}','_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        time.sleep(2)
        
        close_popup(driver)
        
        # 공연날짜
        try:
            event_date = driver.find_element(By.CSS_SELECTOR, '#content > section.common_section.section_product_info > div.product_detail_info > div.product_info > ul:nth-child(2) > li:nth-child(3) > div').text
            print('날짜 : ' + event_date)
            
            if '~' in event_date:
                event_start_date, event_end_date = event_date.split('-')
                event_start_date = convert_date(event_start_date)
                event_end_date = convert_date(event_end_date)
                print(event_start_date)
                print(event_end_date)
        except:
            event_start_date = None
            event_end_date = None
        
        # 장소정보 들어가기
        info_btns = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#content > section.common_section.section_product_tab > div > div > div > ul > li")))
        
        for btn in info_btns:
            if btn.find_element(By.CSS_SELECTOR, 'button > span').text == '장소정보' :
                info_btn = btn.find_element(By.CSS_SELECTOR, 'button')
                break
        info_btn.click()
        
        time.sleep(2)
        
        # 장소와 주소
        address_elements = driver.find_element(By.CSS_SELECTOR, '#content > section.common_section.section_product_content > div > section > p').text
        
        venue, address, tel = address_elements.split('\n')
        
        # 불필요한 문자 삭제
        venue = venue[5:] 
        address = address[5:] 
        
        print(venue)
        print(address)
        print(address_elements)
        
        driver.close()
        driver.switch_to.window(driver.window_handles[1])
        
    except:
        detail_link = ''
    
    # 전체정보
    info = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dd.list_cont').text
    
    list = ['공연정보', '공지사항', '할인정보', '공연내용', '기획사정보']
    
    # 공연정보
    if '공연정보' in info :
        _, basic_info = info.split('공연정보')
        for title in list : 
            if title in basic_info :
                basic_info, _ = basic_info.split(title)
                break
        print('공연정보 : ' + basic_info)
    
    # 공지사항(랜덤)
    if '공지사항' in info: 
        _, notice_info = info.split('공지사항')
        for title in list : 
            if title in notice_info :
                notice_info, _ = notice_info.split(title)
                break
        print('공지사항 : ' + notice_info)
            
    # 할인정보(랜덤)
    if '할인정보' in info: 
        _, discount_info = info.split('할인정보')
        for title in list : 
            if title in discount_info :
                discount_info, _ = discount_info.split(title)
                break
        print('할인정보 : ' + discount_info)
            
    
    # 공연내용(랜덤)
    if '공연내용' in info: 
        _, content_info = info.split('공연내용')
        for title in list : 
            if title in content_info :
                content_info, _ = content_info.split(title)
                break
        print('공연내용 : ' + content_info)
            
    # 기획사정보
    if '기획사정보' in info: 
        _, agency_info = info.split('기획사정보')
        print('기획사정보 : ' + agency_info)
     
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    time.sleep(2)
   
# 웹 드라이버 종료
driver.quit()