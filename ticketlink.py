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

    return date_db_format

# 공연 기간을 추출하는 함수
def extract_event_dates(basic_info):
    # 공연 기간 패턴: "공연 기간 : 2024년 11월 14일(목) ~ 2024년 11월 16일(토)"
    period_pattern = r"공연 기간\s*:\s*(\d{4}년\s\d{1,2}월\s\d{1,2}일)\([^)]+\)\s*~\s*(\d{4}년\s\d{1,2}월\s\d{1,2}일)\([^)]+\)"
    single_date_pattern = r"공연 기간\s*:\s*(\d{4}년\s\d{1,2}월\s\d{1,2}일)\([^)]+\)"

    # 공연 기간이 범위인 경우
    period_match = re.search(period_pattern, basic_info)
    
    if period_match:
        start_date_str = period_match.group(1)  # 공연 시작일
        end_date_str = period_match.group(2)  # 공연 종료일

        # 날짜를 datetime 형식으로 변환
        start_date = datetime.strptime(start_date_str, '%Y년 %m월 %d일').date()
        end_date = datetime.strptime(end_date_str, '%Y년 %m월 %d일').date()
        
        return start_date, end_date
    
    # 공연 기간이 한 날짜인 경우
    single_date_match = re.search(single_date_pattern, basic_info)
    
    if single_date_match:
        start_date_str = single_date_match.group(1)  # 공연 시작일
        # 종료일이 없으므로 시작일과 동일하게 설정
        start_date = datetime.strptime(start_date_str, '%Y년 %m월 %d일').date()
        return start_date, start_date

    return None, None
        
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

# 공연정보를 합쳐서 출력하는 부분 추가
def get_info_part(info, section_name, list):
    if section_name in info:
        _, section_info = info.split(section_name)
        for title in list:
            if title in section_info:
                section_info, _ = section_info.split(title)
                break
        return section_info.strip()
    return ''
    
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
    address = None
    venue = None    
    # 이미지 URL
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dt > dl > dd.thumb > img').get_attribute('src')
    except:
        image_url = ''
    print("이미지 URL : " + image_url)
    
    # 티켓오픈일
    ticket_open_date = convert_datetime(driver.find_element(By.CSS_SELECTOR, '#ticketOpenDatetime').text)
    print("티켓 오픈일" + ticket_open_date)
    pre_ticket_open_date = None
    # 등록일
    registration_date = convert_datetime(driver.find_element(By.CSS_SELECTOR, '#registerDatetime').text)
    print("티켓 등록일" + registration_date)
    # 상세페이지(예매)
    try:
        detail_link = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dt > dl > dd:nth-child(9) > a').get_attribute('href')
        
        # 상세페이지 들어가기
        driver.execute_script(f"window.open('{detail_link}','_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        
        time.sleep(2)
        
        close_popup(driver)
        
        
        
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
        region = address[:2]
        print("장소 : " + venue)
        #print("지역 : " + region)
        print("상세 주소 : " + address)
        
        driver.close()
        driver.switch_to.window(driver.window_handles[1])
        
    except:
        detail_link = link
    
    # 전체정보
    info = driver.find_element(By.CSS_SELECTOR, '#content > div > div.help_cont > div > dl > dd.list_cont').text
    
    list = ['공연정보', '공지사항', '할인정보', '공연내용', '기획사정보']
    
    # 공연정보, 공지사항, 할인정보 추출 및 합치기
    basic_info = get_info_part(info, '공연정보', list)
    notice_info = get_info_part(info, '공지사항', list)
    discount_info = get_info_part(info, '할인정보', list)

    # 세 가지 정보를 합쳐서 공연정보로 출력
    full_performance_info = f" {basic_info}\n {notice_info}\n {discount_info}"
    print("공연정보 : " + full_performance_info)
    
    # 공연내용(랜덤)
    content_info = get_info_part(info, '공연내용', list)

    print('공연내용 : ' + content_info)
            
    # 기획사정보
    agency_info = get_info_part(info, '기획사정보', list)

    print('기획사정보 : ' + agency_info)

    genre =''

    event_start_date, event_end_date = extract_event_dates(full_performance_info)
    
    # 공연 기간이 추출되지 않으면 기본값 설정
    if event_start_date is None:
        event_start_date = None
        event_end_date = None
    else:
        print(f"공연 시작일: {event_start_date}, 공연 종료일: {event_end_date}")
        
    
     # 데이터베이스에 삽임

    try:
        event_exists = is_event_exists(cursor, event_name)

        if event_exists:
            event_id = event_exists[0] #첫번재 열의 값인 id를 가져옴
            # 이미 존재하는 이벤트에 대해 판매 사이트 정보만 추가
            sales_site_data = (event_id, 'Ticket Link', detail_link)
            insert_sales_site(cursor, sales_site_data)
        else:
            # 이벤트 정보 삽입
            event_data = (
                event_name, registration_date, ticket_open_date, pre_ticket_open_date, image_url, full_performance_info,
                content_info, agency_info, genre, event_start_date, event_end_date, venue, address
            )
            event_id = insert_event(cursor, event_data)

            # 판매 사이트 정보 삽입
            sales_site_data = (event_id, 'Ticket Link', detail_link)
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
