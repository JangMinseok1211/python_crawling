import MySQLdb
import requests
import time
import random
from bs4 import BeautifulSoup
from detail_crawler import get_detail

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
    
        detail = get_detail(link)
        
        if type_ != "HOT":
            data.append({
                "type": type_, 
                "title": title, 
                "date": date, 
                "poster_image": detail["poster_image"],
                "performance_info": detail["performance_info"],
                "discount_info": detail["discount_info"],
                "performance_intro": detail["performance_intro"],
                "casting_info": detail["casting_info"],
                "planner_info": detail["planner_info"],
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
