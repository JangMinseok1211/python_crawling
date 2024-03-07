# detail_crawler.py
import requests
from bs4 import BeautifulSoup

def get_detail(link):
    page_url = "https://ticket.interpark.com/webzine/paper/"+link

    # 웹페이지 요청 및 응답 받기
    response_page = requests.get(page_url)

    # BeautifulSoup 객체 생성
    soup_page = BeautifulSoup(response_page.text, 'html.parser')
    
    # 포스터 이미지
    poster_image_element = soup_page.find("span", class_="poster")
    poster_image = poster_image_element.img["src"] if poster_image_element else None
    
    #게시물 등록일
    create_date_element = soup_page.find("span", class_="date")
    create_date = create_date_element.span.get_text(strip=True) if create_date_element else None
    
    # 공연 정보
    performance_info_element = soup_page.find("div", class_="introduce")
    performance_info = performance_info_element.div.get_text(strip=True) if performance_info_element else None

    # 할인 정보
    discount_info_element = soup_page.find("div", class_="info_discount")
    discount_info_div = discount_info_element.div.get_text(strip=True) if discount_info_element else None

    # 공연 소개
    performance_intro_element = soup_page.find("div", class_="info1")
    performance_intro = performance_intro_element.div.get_text(strip=True) if performance_intro_element else None

    # 캐스팅 정보
    info2_elements = soup_page.find_all("div", class_="info2")
    casting_info = None
    planner_info = None
    if info2_elements:
        casting_info_element = info2_elements[0]
        casting_info = casting_info_element.div.get_text(strip=True) if casting_info_element else None
        if len(info2_elements) > 1:
            # 기획사 정보
            planner_info_element = info2_elements[1]
            planner_info = planner_info_element.div.get_text(strip=True) if planner_info_element else None
            
    return {
        "poster_image": poster_image,
        "create_date" : create_date,
        "performance_info": performance_info,
        "discount_info": discount_info_div,
        "performance_intro": performance_intro,
        "casting_info": casting_info,
        "planner_info": planner_info,
    }
