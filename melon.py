import re
from datetime import datetime, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
import time
import schedule
import threading

# 데이터 전처리 함수
def convert_date(date_str):
    return datetime.strptime(date_str, "%Y.%m.%d").date()

def convert_datetime(datetime_str):
    match = re.search(r'(\d{4})년 (\d{1,2})월 (\d{1,2})일 \(\S+\) (\d{2}:\d{2})', datetime_str)
    if match:
        date_part = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        time_part = match.group(4)
        return f"{date_part} {time_part}:00"
    return None

# 상세보기 링크 추출 함수
def extract_detail_link(detail_element):
    onclick_text = detail_element.get_attribute('onclick')
    match = re.search(r"bannerLanding\('TD', '(\d+)'\);", onclick_text)
    if match:
        prod_id = match.group(1)
        return f"https://ticket.melon.com/performance/index.htm?prodId={prod_id}"
    return None

# MySQL 연결 설정
db_config = {
    'user': 'root',
    'password': '1921',
    'host': 'localhost',
    'database': 'tow',
    'port': 3306
}

def get_latest_registration_date(category_name):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT MAX(registration_date) FROM tickets WHERE genre = %s"
        cursor.execute(query, (category_name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result[0]:
            return result[0]
        else:
            return date.min
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return date.min

def crawl_and_insert():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        print("데이터베이스 연결 성공")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return

    # ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    # 열고자 하는 웹페이지 URL
    driver.get("https://ticket.melon.com/csoon/index.htm")

    # 카테고리 선택자 및 이름 목록 (콘서트, 뮤지컬/연극, 클래식, 전시/행사)
    categories = [
        ("콘서트", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(2) > a"),
        ("뮤지컬/연극", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(3) > a"),
        ("클래식", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(4) > a"),
        ("전시/행사", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(5) > a")
    ]

    for category_name, category_selector in categories:
        latest_registration_date = get_latest_registration_date(category_name)
        print(f"{category_name}의 최신 등록일: {latest_registration_date}")

        # 카테고리 클릭
        driver.execute_script(f"document.querySelector('{category_selector}').click();")
        
        # 변경된 결과가 로드될 때까지 대기
        time.sleep(2)  # 페이지가 새로 고침될 시간을 주기 위해 대기
        
        # 티켓 목록을 추출
        tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list_ticket_cont > li')))
        
        # 각 티켓 상세 페이지로 이동하여 정보를 추출
        for ticket in tickets:
            # 티켓 상세 페이지 링크
            detail_link = ticket.find_element(By.CSS_SELECTOR, 'div.link_consert > a').get_attribute('href')
        
            # 새 탭에서 상세 페이지 열기
            driver.execute_script(f"window.open('{detail_link}','_blank');")
            driver.switch_to.window(driver.window_handles[1])
            
            # 대기
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.section_ticketopen_view')))

            # 장르
            genre = category_name
            
            # 제목 추출
            event_name = driver.find_element(By.CSS_SELECTOR, '.tit').text if driver.find_elements(By.CSS_SELECTOR, '.tit') else ''
            
            # 등록일
            registration_date_raw = driver.find_element(By.CSS_SELECTOR, '.txt_date').text if driver.find_elements(By.CSS_SELECTOR, '.txt_date') else ''
            registration_date = convert_date(registration_date_raw)
            
            # 최신 등록일 이후의 게시물만 크롤링
            if registration_date <= latest_registration_date:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                continue

            # 선예매 및 티켓 오픈일 추출
            pre_sale_date_raw = '정보 없음'
            ticket_open_date_raw = '정보 없음'
            pre_sale_date = None
            ticket_open_date = None

            # 선예매로 되어있으면 선예매 정보 가져오고 티켓오픈으로 되어있으면 티켓오픈의 날짜 정보를 가져옴
            try:
                dt_elements = driver.find_elements(By.XPATH, "//*[@id='conts']/div[1]/div[2]/div/ul/li/dl/dt[@class='tit_type']")
                for i, dt in enumerate(dt_elements):
                    dt_text = dt.text.strip()
                    dd_element = dt.find_element(By.XPATH, "following-sibling::dd[@class='txt_date']")
                    dd_text = dd_element.text.split(':', 1)[-1].strip()
                    
                    if dt_text == "선예매":
                        pre_sale_date_raw = dd_text
                        pre_sale_date = convert_datetime(pre_sale_date_raw)
                    elif dt_text == "티켓오픈":
                        ticket_open_date_raw = dd_text
                        ticket_open_date = convert_datetime(ticket_open_date_raw)
            except Exception as e:
                print(f"Error occurred: {e}")
            
            # 이미지 URL 추출
            image_url = driver.find_element(By.CSS_SELECTOR, '.box_consert_thumb img').get_attribute('src') if driver.find_elements(By.CSS_SELECTOR, '.box_consert_thumb img') else ''
            
            # 기본 정보 추출
            basic_info = driver.find_element(By.CSS_SELECTOR, '.box_concert_time .data_txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_concert_time .data_txt') else ''
            
            # 공연 소개 추출
            event_description = driver.find_element(By.CSS_SELECTOR, '.box_concert_info .concert_info_txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_concert_info .concert_info_txt') else ''
            
            # 기획사 정보 추출
            agency_info = driver.find_element(By.CSS_SELECTOR, '.box_agency .txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_agency .txt') else ''
            
            # 상세보기 링크 추출
            detail_element = driver.find_elements(By.CSS_SELECTOR, '.box_link > a')
            detail_url = extract_detail_link(detail_element[0]) if detail_element else detail_link
            
            # 데이터베이스에 삽입
            try:
                insert_query = """
                INSERT INTO tickets (event_name, registration_date, ticket_open_date, pre_sale_date, image_url, basic_info, event_description, agency_info, detail_link, genre, sales_site)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    event_name, registration_date, ticket_open_date, pre_sale_date, image_url, basic_info, event_description, agency_info, detail_url, genre, 'Melon Ticket'
                ))
                print(f"Inserted: {event_name}, {registration_date}, {ticket_open_date}, {pre_sale_date}, {image_url}, {basic_info}, {event_description}, {agency_info}, {detail_url}, {genre}, Melon Ticket")
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                conn.rollback()  # 오류가 발생하면 롤백합니다.
            
            print("--------------------------------------------------------------")
            
            # 현재 탭을 닫고 목록 페이지로 돌아감
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            # 잠시 대기
            time.sleep(2)

    # 변경사항 커밋 및 MySQL 커넥션 종료
    try:
        conn.commit()
        print("커밋 완료")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()
        print("데이터베이스 연결 종료")

    # 웹 드라이버 종료
    driver.quit()

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

# 매일 00:00에 작업 실행
schedule.every().day.at("00:00").do(run_threaded, crawl_and_insert)

# 스케줄러 유지
while True:
    schedule.run_pending()
    time.sleep(1)
