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
driver.get("https://ticket.melon.com/csoon/index.htm")

WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#sForm')))

# JavaScript를 사용하여 콘서트 카테고리 클릭
concert_category_selector = "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(5) > a"
driver.execute_script(f"document.querySelector('{concert_category_selector}').click();")

# 변경된 결과가 로드될 때까지 대기
time.sleep(2)  # 페이지가 새로 고침될 시간을 주기 위해 대기

# 콘서트 목록을 추출
tickets = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.list_ticket_cont > li')))

# 각 콘서트 상세 페이지로 이동하여 정보를 추출
for ticket in tickets:  # 예시를 위해 첫 번째 항목만 처리
    # 콘서트 상세 페이지 링크
    detail_link = ticket.find_element(By.CSS_SELECTOR, 'div.link_consert > a').get_attribute('href')

    # 새 탭에서 상세 페이지 열기
    driver.execute_script(f"window.open('{detail_link}','_blank');")
    driver.switch_to.window(driver.window_handles[1])
    


    # 대기
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.section_ticketopen_view')))
    
    #제목 추출
    title = driver.find_element(By.CSS_SELECTOR, '.tit').text
    print(f"제목: {title}")

    #등록일
    register_date = driver.find_element(By.CSS_SELECTOR, '.txt_date').text
    print(f"등록일: {register_date}")
    
    #티켓 오픈일 추출
    open_date = driver.find_element(By.CSS_SELECTOR, '.box_ticketopen_schedule .txt_date').text
    print(f"티켓오픈일: {open_date}")
    
    # 이미지 URL 추출
    image_url = driver.find_element(By.CSS_SELECTOR, '.box_consert_thumb img').get_attribute('src')
    print(f"이미지 URL: {image_url}")
    
    # 기본 정보 추출
    basic_info = driver.find_element(By.CSS_SELECTOR, '.box_concert_time .data_txt').text
    print(f"기본 정보:\n{basic_info}")
    
    # 공연 소개 추출
    introduction = driver.find_element(By.CSS_SELECTOR, '.box_concert_info .concert_info_txt').text
    print(f"공연 소개:\n{introduction}")
    
    # 기획사 정보 추출
    agency_info = driver.find_element(By.CSS_SELECTOR, '.box_agency .txt').text
    print(f"기획사 정보:\n{agency_info}")


    
 
    # 현재 탭을 닫고 목록 페이지로 돌아감
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    # 잠시 대기
    time.sleep(2)

# 웹 드라이버 종료
driver.quit()
