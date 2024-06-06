import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
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


# MySQL 연결 함수
def get_mysql_connection():
    return mysql.connector.connect(**db_config)

# 이벤트 존재 확인 함수 (LIKE를 사용하여 부분 일치 검색)
def is_event_exists(cursor, event_name):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    query = "SELECT id FROM tickets WHERE event_name LIKE %s"
    cursor.execute(query, ('%' + event_name + '%',))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


# 이벤트 삽입 함수
def insert_event(cursor, event_data):
    insert_event_query = """
    INSERT INTO tickets (event_name, registration_date, ticket_open_date, pre_sale_date, image_url, basic_info, event_description, agency_info, genre, event_start_date, event_end_date, venue, address)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_event_query, event_data)
    return cursor.lastrowid

# 판매 사이트 삽입 함수
def insert_sales_site(cursor, sales_site_data):
    insert_site_query = """
    INSERT INTO event_sites (event_id, sales_site, detail_link)
    VALUES (%s, %s, %s)
    """
    cursor.execute(insert_site_query, sales_site_data)

try:
    conn = get_mysql_connection()
    cursor = conn.cursor()
    print("데이터베이스 연결 성공")
except mysql.connector.Error as err:
    print(f"Error: {err}")
    
    
# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

 # 예매 안내 팝업 닫기 함수
def close_popup(driver):
    try:
        close_button = driver.find_element(By.CSS_SELECTOR, '#popup-prdGuide > div > div.popupFooter > button')
        close_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass
    except Exception as e:
        print(f"Unexpected error when trying to close popup: {e}")

# 장르 매핑
genre_mapping = {
    '콘서트': '콘서트',
    '뮤지컬': '뮤지컬연극',
    '연극': '뮤지컬연극',
    '아동/가족': '뮤지컬연극',
    '클래식/무용': '클래식',
    '전시/행사': '전시행사'
}
    
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

    
    # 카테고리
    try:
        original_genre = ticket.find_element(By.CSS_SELECTOR, 'td.type').text
    except NoSuchElementException:
        original_genre = ""
    
    # 카테고리가 사이트공지일 경우 크롤링 하지 않음
    if original_genre == '사이트공지':
        continue
    
    # 장르 매핑
    genre = genre_mapping.get(original_genre, None)
    if not genre:
        continue  # 매핑되지 않은 장르의 경우 크롤링하지 않음


    
    # 티켓링크 상세페이지
    detail_link = ticket.find_element(By.CSS_SELECTOR, 'td.subject > a').get_attribute('href')

    # 상세페이지 열기
    driver.execute_script(f"window.open('{detail_link}','_blank');")
    driver.switch_to.window(driver.window_handles[1])
    
    time.sleep(1)
    

  
    
    # 티켓오픈일 추출
    try:
        ticket_open_element = driver.find_element(By.CSS_SELECTOR, 'li.open')
        ticket_open_text = ticket_open_element.text.strip()
        ticket_open_date = ticket_open_text.replace('티켓오픈일', '').strip()  # '티켓오픈일' 제거
        ticket_open_date = convert_datetime(ticket_open_date)

    except:
        ticket_open_date = None
        
    # 티켓선예매 추출
    presale_info = ''
    try:
        toping_presale_element = driver.find_element(By.CSS_SELECTOR, '#wrapBody > div > div > div.board > div.detail_top > div.info > ul > li.tiki')
        presale_info = toping_presale_element.text.replace('Toping 선예매', '').strip()
        pre_ticket_open_date = convert_datetime(presale_info)
    except:
        try:
            fanclub_presale_element = driver.find_element(By.CSS_SELECTOR, '#wrapBody > div > div > div.board > div.detail_top > div.info > ul > li:nth-child(2)')
            presale_info = fanclub_presale_element.text.replace('팬클럽 선예매', '').strip()
            pre_ticket_open_date = convert_datetime(presale_info)
        except:
            pre_ticket_open_date = None
            

    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .poster > img').get_attribute('src')
    except:
        image_url = ''

    
    # 등록일
    registration_date_str = driver.find_element(By.CSS_SELECTOR, '.section_notice .detail_top .btn .date > span').text
    registration_date = convert_date(registration_date_str)

    
    # 공연정보
    try:
        basic_info = driver.find_element(By.CSS_SELECTOR, 'div.introduce').text
    except:
        basic_info = ''
        

    
    # 할인정보
    try:
        info_discount = driver.find_element(By.CSS_SELECTOR, 'div.info_discount').text
    except:
        info_discount = ''

    basic_info = basic_info + info_discount

    # 공연소개
    try:
        event_description = driver.find_element(By.CSS_SELECTOR, 'div.info1').text 
    except:
        event_description = ''
        infos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.info2")))
        for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "공연소개":
                event_description = info.text

    
    # 캐스팅
    try:
        infos = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.info2")))
        for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "캐스팅":
                casting = info.text
    except:
        casting = ''

    
    # 기획사정보
    agency_info = ''
    for info in infos:
            if info.find_element(By.TAG_NAME, 'h4').text == "기획사정보":
                agency_info = info.text

    agency_info= agency_info + casting
    
    # 상세보기 링크 추출
    detail = detail_link
    try:
        detail_url = driver.find_element(By.CSS_SELECTOR, 'a.btn_book').get_attribute('href')
    except NoSuchElementException:
        detail_url = detail_link

    if detail_url == '':
        detail_url = detail
    #상세보기 링크 페이지로 접속
    driver.execute_script(f"window.open('{detail_url}','_blank');")
    driver.switch_to.window(driver.window_handles[2])
    
    time.sleep(1)
    # 예매 안내 팝업 닫기 
    close_popup(driver)
    
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

    try:
        venue = driver.find_element(By.CSS_SELECTOR, '#container > div.contents > div.productWrapper > div.productMain > div.productMainTop > div > div.summaryBody > ul > li:nth-child(1) > div > a').text
        venue = venue[:-5] #불필요한 문장 삭제 

        
    except: 
         venue = ''
    # 공연장 정보 팝업 클릭 및 주소 추출
    try:
        info_btn = driver.find_element(By.CSS_SELECTOR, '.infoBtn[data-popup="info-place"]')
        info_btn.click()
        time.sleep(1)  
        address_elements = driver.find_elements(By.CSS_SELECTOR, '#popup-info-place > div > div.popupBody > div > div.popPlaceInfo > p')
        address = ''
        
        for element in address_elements:
            if '주소' in element.text:
                span_element = element.find_element(By.TAG_NAME, 'span')
                address = span_element.text
                break
                
               
    except:
        address = ''

        
    # 현재 탭을 닫음
    driver.close()
    driver.switch_to.window(driver.window_handles[1])

    # 데이터베이스에 삽임

    try:
        event_exists = is_event_exists(cursor, event_name)

        if event_exists:
            event_id = event_exists[0] #첫번재 열의 값인 id를 가져옴
            # 이미 존재하는 이벤트에 대해 판매 사이트 정보만 추가
            sales_site_data = (event_id, 'Interpark Ticket', detail_url)
            insert_sales_site(cursor, sales_site_data)
        else:
            # 이벤트 정보 삽입
            event_data = (
                event_name, registration_date, ticket_open_date, pre_ticket_open_date, image_url, basic_info,
                event_description, agency_info, genre, event_start_date, event_end_date, venue, address
            )
            event_id = insert_event(cursor, event_data)

            # 판매 사이트 정보 삽입
            sales_site_data = (event_id, 'Interpark Ticket', detail_url)
            insert_sales_site(cursor, sales_site_data)

        conn.commit()
        print(f"카테고리: {genre} 게시물 삽입 또는 업데이트 완료")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()  # 오류가 발생하면 롤백합니다.
    
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    iframe_content = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "iFrmNotice")))
    driver.switch_to.frame(iframe_content)
    
    time.sleep(2)



    
    
# 웹 드라이버 종료
driver.quit()
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
