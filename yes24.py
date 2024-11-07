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
import joblib

# 데이터 전처리 함수
def convert_date(date_str):
    return datetime.strptime(date_str.strip(), "%Y.%m.%d").date()
    
def extract_real_url(javascript_code):
    """JavaScript 호출에서 실제 URL 추출"""
    # 정규표현식으로 ID 추출
    pattern = r"jsf_base_GetSiteDetailURL\((\d+)\)"
    match = re.search(pattern, javascript_code)
    if match:
        # 실제 링크 구성
        perf_id = match.group(1)
        real_url = f"http://ticket.yes24.com/Pages/Perf/Detail/Detail.aspx?IdPerf={perf_id}"
        return real_url
    return None    
    
def convert_datetime(datetime_str):
    # 요일 정보를 제거 > 정규 표현식 사용
    date_str = re.sub(r'\([^)]*\)', '', datetime_str)
    
    date_format = '%Y.%m.%d %H:%M'
    date_obj = datetime.strptime(date_str.strip(), date_format)
    date_db_format = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    print(date_db_format)
    return date_db_format
    
# 팝업 닫기 함수
def close_popup(driver):
    try:
        # 팝업 닫기 버튼 찾기 및 클릭
        close_button = driver.find_element(By.CSS_SELECTOR, '#noticeAlert_layerpopup_close')
        close_button.click()
        time.sleep(1)
        print("닫기완료")
    except NoSuchElementException:
        pass
    except Exception as e:
        print(f"Unexpected error when trying to close popup: {e}")

# MySQL 연결 함수
def get_mysql_connection():
    return mysql.connector.connect(**db_config)

# MySQL 연결 설정
db_config = {
    
}


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
    INSERT INTO tickets (event_name, registration_date, ticket_open_date, pre_sale_date, image_url, basic_info, 
                         event_description, agency_info, genre, event_start_date, event_end_date, venue, address)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    # None 값을 NULL로 처리
    cursor.execute(insert_event_query, [
        value if value is not None else None for value in event_data
    ])
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
    
# 저장된 모델과 벡터라이저 불러오기
model, vectorizer = joblib.load('genre_classifier.pkl')

# ChromeDriverManager를 사용하여 크롬 드라이버 자동 설치 및 경로 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 열고자 하는 웹페이지 URL
driver.get("http://ticket.yes24.com/New/Notice/NoticeMain.aspx")

# 오픈일순 정렬
#open_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#SelectOrder > a:nth-child(2)")))

#open_link.click()


#time.sleep(1)

# 오픈티켓목록
tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#BoardList > div > table > tbody > tr")))

time.sleep(1)

for ticket in tickets[1:]: 
    
    event_name = genre = basic_info = event_description = agency_info = None
    ticket_open_date = pre_sale_date = registration_date = None
    image_url = venue = address = None
    event_start_date = event_end_date = None
    
    # 제목
    event_name = ticket.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
    print("제목" + event_name)

    # 장르 예측
    genre_vector = vectorizer.transform([event_name])
    genre = model.predict(genre_vector)[0]
    print("예측된 장르: " + genre)
    
    # 상세페이지 열기
    link = ticket.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
    driver.execute_script(f"window.open('{link}','_blank');")
    driver.switch_to.window(driver.window_handles[1])
    
    time.sleep(1)
    
    # 티켓오픈일
    ticket_open_date = driver.find_element(By.CSS_SELECTOR, '#title1').text
    print("오픈일" + ticket_open_date)
    # 티켓선예매
    try:
        pre_sale_date = driver.find_element(By.CSS_SELECTOR, '#title2').text
    except:
        pre_sale_date = None
    print("선예매" + pre_sale_date)
    # 등록일
    registration_date = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-date > span:nth-child(1)').text
    
    # 불필요한 문자 삭제
    registration_date = registration_date[6:]
    print("등록일" + registration_date)
    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-ticket > div > div.noti-vt-left > img').get_attribute('src')
    except:
        image_url = ''
    print("이미지" + image_url)
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


        time.sleep(2)  # 페이지가 다 로드될 시간을 충분히 부여
        detail_link = driver.find_element(By.CSS_SELECTOR, '#NoticeRead > div.noti-view-ticket > div > div.noti-vt-right > div.noti-vt-btns > a').get_attribute('href')
        detail_link = extract_real_url(detail_link)
        
        
        if detail_link:
            driver.execute_script(f"window.open('{detail_link}','_blank');")
            driver.switch_to.window(driver.window_handles[2])
        else:
            print("Detail link not found.")
            continue  # 다음 티켓으로 넘어감
        
        time.sleep(1)

        close_popup(driver)

        print(detail_link)

        
        try:
            # 공연 날짜 찾기
            try:
                event_date_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="mainForm"]/div[7]/div/div[2]/div/p/span | //*[@id="mainForm"]/div[8]/div/div[2]/div/p/span'
                        )
                    )
                )
                event_date = event_date_element.text
            except (NoSuchElementException, TimeoutException):
                event_date = None  # 요소를 찾지 못한 경우 처리
            except Exception as e:
                print(f"Error occurred: {e}")
        
            print(f"Event Date: {event_date}")
            
       
            # 날짜가 "~" 구분자로 되어 있는 경우
            if '~' in event_date:
                event_start_date, event_end_date = event_date.split('~')
                event_start_date = convert_date(event_start_date)
                event_end_date = convert_date(event_end_date)
            else:
                event_start_date = convert_date(event_date.strip())
                event_end_date = event_start_date  # 단일 날짜일 경우 같은 날짜로 설정
            
            print(f"이벤트 시작: {event_start_date}, 끝: {event_end_date}")
            
            # 장소와 주소 추출
            try:
                venue = driver.find_element(By.CSS_SELECTOR, '#ps-location > span').text
            except:
                venue = None
            try:
                address = driver.find_element(By.CSS_SELECTOR, '#TheaterAddress').text
            except:
                address = None
            print(f"장소: {venue}, 주소: {address}")
        
        except Exception as e:
            print(f"Error occurred during event data extraction: {e}")
        finally:
            # 현재 탭을 닫고, 원래 탭으로 돌아감
            driver.close()
            driver.switch_to.window(driver.window_handles[1])

        
    
    except:
        detail_link = link
         # 데이터베이스에 삽임

    try:
        event_exists = is_event_exists(cursor, event_name)

        if event_exists:
            event_id = event_exists[0] #첫번재 열의 값인 id를 가져옴
            # 이미 존재하는 이벤트에 대해 판매 사이트 정보만 추가
            sales_site_data = (event_id, 'Yes24', detail_link)
            insert_sales_site(cursor, sales_site_data)
        else:
            # 이벤트 정보 삽입
            event_data = (
                event_name, registration_date, ticket_open_date, pre_sale_date, image_url, basic_info,
                event_description, agency_info, genre, event_start_date, event_end_date, venue, address
            )
            event_id = insert_event(cursor, event_data)

            # 판매 사이트 정보 삽입
            sales_site_data = (event_id, 'Yes24', detail_link)
            insert_sales_site(cursor, sales_site_data)

        conn.commit()
        print(f"카테고리: {genre} 게시물 삽입 또는 업데이트 완료")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()  # 오류가 발생하면 롤백합니다.
    
    # 현재 탭을 닫고 목록 페이지로 돌아감

    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    
    time.sleep(2)
   
# 웹 드라이버 종료
driver.quit()
