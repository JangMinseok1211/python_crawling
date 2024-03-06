import MySQLdb
import requests
import time
import random
from bs4 import BeautifulSoup

# URL을 입력하세요.
url = "https://ticket.interpark.com/webzine/paper/TPNoticeList_iFrame.asp?bbsno=34&stext=&KindOfGoods=TICKET&genre=&sort=WriteDate&pageno={no}"

conn = MySQLdb.connect(
    user="root",
    passwd="1921",
    host="localhost",
    db="ticket",
    charset="utf8"
)
headers = {
"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",

"Accept-Language" : "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    
}
# 커서 생성
cursor = conn.cursor()

for no in range(1, 0, -1):  # 2부터 1까지 역순으로 페이지를 순회합니다.
    response = requests.get(url.format(no=no),headers =headers)
    response.encoding = 'euc-kr'  # 인코딩 방식을 'euc-kr'로 설정합니다.
    
    html = response.text

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    rows = table.find_all("tr")
    
    data = []
    i = 1
    for row in reversed(rows[1:]):
        
        random_sec = random.uniform(3,5)

        time.sleep(random_sec)
        
        print(i)
        i= i+1
        columns = row.find_all("td")
        
        type_ = columns[0].text.strip()
        title = columns[1].text.strip()
        link = columns[1].a['href']  # <a> 태그의 href 속성에서 링크를 가져옵니다.
        date = columns[2].text.strip()
    
        page_url = "https://ticket.interpark.com/webzine/paper/"+link
    
        # 웹페이지 요청 및 응답 받기
        response_page = requests.get(page_url)
        
        # BeautifulSoup 객체 생성
        soup_page = BeautifulSoup(response_page.text, 'html.parser')
        
        # 포스터 이미지
        poster_image_element = soup_page.find("span", class_="poster")
        poster_image = poster_image_element.img["src"] if poster_image_element else None
        
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
        
        if type_ != "HOT":
            data.append({
                "type": type_, 
                "title": title, 
                "date": date, 
                "poster_image": poster_image,
                "performance_info": performance_info,
                "discount_info": discount_info_div,
                "performance_intro": performance_intro,
                "casting_info": casting_info,
                "planner_info": planner_info,
            })
         
    
    
        
    for item in data:
        sql = '''INSERT INTO interpark(type, title, date, poster_image, performance_info, discount_info, performance_intro, casting_info, planner_info)
                  VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
        cursor.execute(sql, (item['type'], item['title'], item['date'], item['poster_image'], item['performance_info'], item['discount_info'], item['performance_intro'], item['casting_info'], item['planner_info']))
    
    # 변경사항 저장
    conn.commit()
    print("완료")
# 연결종료하기
conn.close()