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

# 카테고리 선택자 및 이름 목록 (콘서트, 뮤지컬/연극, 클래식, 전시/행사)
categories = [
    ("콘서트", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(2) > a"),
    ("뮤지컬/연극", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(3) > a"),
    ("클래식", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(4) > a"),
    ("전시/행사", "#sForm > div > div.wrap_form_input.box_ticket_search > div > div > div > ul > li:nth-child(5) > a")
]

# 각 카테고리에 대해 크롤링
for category_name, category_selector in categories:
    
    
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

        #카테고리
        print(f"카테고리: {category_name}")
        
        # 제목 추출
        title = driver.find_element(By.CSS_SELECTOR, '.tit').text if driver.find_elements(By.CSS_SELECTOR, '.tit') else ''
        print(f"제목: {title}")
    
        # 등록일
        register_date = driver.find_element(By.CSS_SELECTOR, '.txt_date').text if driver.find_elements(By.CSS_SELECTOR, '.txt_date') else ''
        print(f"등록일: {register_date}")
        
        # 선예매 및 티켓 오픈일 추출
        pre_sale_date = '정보 없음'
        open_sale_date = '정보 없음'

        #선예매로 되어있으면 선예매 정보 가져오고 티켓오픈 으로 되어있으면 티켓오픈의 날짜 정보를 가져옴
        try:
            dt_elements = driver.find_elements(By.XPATH, "//*[@id='conts']/div[1]/div[2]/div/ul/li/dl/dt[@class='tit_type']")
            for i, dt in enumerate(dt_elements):
                dt_text = dt.text.strip()
                dd_element = dt.find_element(By.XPATH, "following-sibling::dd[@class='txt_date']")
                dd_text = dd_element.text.split(':', 1)[-1].strip()
                
                if dt_text == "선예매":
                    pre_sale_date = dd_text
                elif dt_text == "티켓오픈":
                    open_sale_date = dd_text
        except Exception as e:
            print(f"Error occurred: {e}")
        
        print(f"선예매 오픈일: {pre_sale_date}")
        print(f"티켓 오픈일: {open_sale_date}")
        
        # 이미지 URL 추출
        image_url = driver.find_element(By.CSS_SELECTOR, '.box_consert_thumb img').get_attribute('src') if driver.find_elements(By.CSS_SELECTOR, '.box_consert_thumb img') else ''
        print(f"이미지 URL: {image_url}")
        
        # 기본 정보 추출
        basic_info = driver.find_element(By.CSS_SELECTOR, '.box_concert_time .data_txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_concert_time .data_txt') else ''
        print(f"기본 정보:\n{basic_info}")
        
        # 공연 소개 추출
        introduction = driver.find_element(By.CSS_SELECTOR, '.box_concert_info .concert_info_txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_concert_info .concert_info_txt') else ''
        print(f"공연 소개:\n{introduction}")
        
        # 기획사 정보 추출
        agency_info = driver.find_element(By.CSS_SELECTOR, '.box_agency .txt').text if driver.find_elements(By.CSS_SELECTOR, '.box_agency .txt') else ''
        print(f"기획사 정보:\n{agency_info}")
    
        print("--------------------------------------------------------------")
        
        # 현재 탭을 닫고 목록 페이지로 돌아감
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        # 잠시 대기
        time.sleep(2)

# 웹 드라이버 종료
driver.quit()
