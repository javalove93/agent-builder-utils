# Flask Application

from flask import Flask, request, jsonify, Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from functools import wraps
import requests
import time
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

google_search_api_key = None
google_map_api_key = None
cx = None
userid = None
password = None

def read_webpage(url):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x5000')
    options.add_argument("disable-gpu")
    # 혹은 options.add_argument("--disable-gpu")

    try:
        driver = webdriver.Chrome(options=options)

        driver.get(url)
        driver.implicitly_wait(10)
        driver.get_screenshot_as_file('webpage_capture.png')

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # print(soup.title)
        body = soup.find('body')
        # extract text from body
        text = body.get_text()
        # print(text)

        return text
    finally:
        driver.quit()

def read_search_api_key():
    global google_search_api_key, cx, google_map_api_key, userid, password
    with open("search_api.key", "r") as f:
        while True:
            line = f.readline()
            # print(line)
            if not line:
                break
            key, value = line.split("=")
            if key == "GOOGLE_SEARCH_API_KEY":
                google_search_api_key = value.strip()
            elif key == "GOOGLE_MAP_API_KEY":
                google_map_api_key = value.strip()
            elif key == "USERID":
                userid = value.strip()
            elif key == "PASSWORD":
                password = value.strip()
            elif key == "CX":
                cx = value.strip()

    # print(google_search_api_key, google_map_api_key, cx, userid, password)

# Basic Authentication 설정
def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
	            'Could not verify your access level for that URL.\n'
	            'You have to login with proper credentials\n', 401,
	            {'WWW-Authenticate': 'Basic realm="Login Required"'})

        return func(*args, **kwargs)
    return wrapper

# 사용자 인증 확인
def check_auth(uid, pwd):
    global userid, password

    if userid is None or password is None:
        read_search_api_key()
    
    print(userid, password, uid, pwd)

    if uid == userid and pwd == password:
        return True
    return False

@app.route('/')
def hello():
    # Basic Authentication
    auth = request.authorization

    return 'Hello World!'

@app.route('/google_search', methods=['POST, GET'])
@authenticate
def google_search():
    q = request.args.get('q')
    url = f'https://www.google.com/search?q={q}'
    text = read_webpage(url)
    return jsonify(
        {
            'q': q,
            'content': text
        }
    )

@app.route('/google_search_api', methods=['POST, GET'])
@authenticate
def google_search_api():
    global google_search_api_key, cx, google_map_api_key

    if google_search_api_key is None or google_map_api_key is None or cx is None:
        read_search_api_key()
        
    q = request.args.get('q')
    url = "https://www.googleapis.com/customsearch/v1"
    content = ""
    for i in range(0, 0):
        response = requests.get(url, params={"key": google_search_api_key, "cx": cx, "q": q, "start": i * 10 + 1, "num": 10}).json()
        for link in response["items"]:
            print(link['link'])
            text = read_webpage(link['link'])
            content += text + "\n" + "-" * 100 + "\n"
    
    return jsonify(
        {
            'q': q,
            'content': content
        }
    )

@app.route('/google_map', methods=['POST', 'GET'])
@authenticate
def get_places():
    global google_search_api_key, cx, google_map_api_key

    if google_search_api_key is None or google_map_api_key is None or cx is None:
        read_search_api_key()
    
    activity = request.args.get('activity')
    city = request.args.get('city')
    print(activity, city)
    # print(google_map_api_key)
    text_query = f"{activity} in {city}"
    places_resp = requests.get(
        f"https://maps.googleapis.com/maps/api/place/textsearch/json",
        params={
            "query": text_query,
            "key": google_map_api_key,
            "language": "ko",
            # "region": "kr",
        },
    )
    
    # print(places_resp.json())

    # places_resp.json() 결과
        # {'html_attributions': [],
        # 'next_page_token': 'AdCG2DNV3W67AW1UPTbNhafP2RvI5CeZ1wWLua8LMUVNAeY52uJfzWr6lQ9V-vapwzQD9-FPJlBMw8IIW-n3BO8tonTKgy3G-FMKFMl7jpx2vID-yfE1LeUF4YI3kJzPofdAQW1MfWaYYwA3smzG7U_rMFtBkLyROZpruqTiEtRSzUByk38VtTszZLa2ApEMGpySnizJrYJwPlPwavsIx6uqwURhc0ZRGdieSCC9pzDmkR5w5T7CI-i8rs4OCMBfcj5masKFcs5rXrRc_kkFYh7cwQ78-jXXZR2WKsTtGtemy5fl9UTUb3YIlbph9neBHm5edV_ZbjG9IaJB0UzlYlnUBvzbzHpfbVQMPRG3ieFmBBk8m4e1WIGGgEQREflJ98KjCyNSlPMEMe9mCkU',
        # 'results': [{'business_status': 'OPERATIONAL',
        # 'formatted_address': '대한민국 부산광역시 부산진구 가야대로 772',
        # 'geometry': {'location': {'lat': 35.156766, 'lng': 129.05587},
        #     'viewport': {'northeast': {'lat': 35.15811582989272,
        #     'lng': 129.0572198298927},
        #     'southwest': {'lat': 35.15541617010728, 'lng': 129.0545201701073}}},
        # 'icon': 'https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/lodging-71.png',
        # 'icon_background_color': '#909CE1',
        # 'icon_mask_base_uri': 'https://maps.gstatic.com/mapfiles/place_api/icons/v2/hotel_pinlet',
        # 'name': '롯데호텔 부산',
        # 'photos': [{'height': 2252,
        #     'html_attributions': ['<a href="https://maps.google.com/maps/contrib/118295300702597776773">이정일</a>'],
        #     'photo_reference': 'AdCG2DMuchA0Il9cEwbc2YSIcM-K_pAllPEZZPy4PBXesAJ4zBWxrPJ0CNL9nEW012uFvP06XhQJo27gDewF3c4xKMIkgG5mOm3rQFhRHmbv4HDuD7_jw31LLRG2baal1pQIERBmLlfbwHi5zUOPcJ6nKq8ysVu2ZWfING6azViB1eHWxnmS',
        #     'width': 4000}],
        # 'place_id': 'ChIJzZl9PXLraDURpgeBSXYqYSQ',
        # 'plus_code': {'compound_code': '5344+P8 부산광역시 대한민국',
        #     'global_code': '8Q7F5344+P8'},
        # 'rating': 4.4,
        # 'reference': 'ChIJzZl9PXLraDURpgeBSXYqYSQ',
        # 'types': ['lodging', 'point_of_interest', 'establishment'],
        # 'user_ratings_total': 4640},
    
    result = []
    for place in places_resp.json()['results']:
        print(place['name'], place['formatted_address'], place.get('rating', 0))
        result.append({
            'name': place['name'],
            'address': place['formatted_address'],
            'rating': place.get('rating', 0),
        })

    # result를 json 형태로 반환. ensure_ascii=False는 한글이 깨지지 않게 하기 위함
    return json.dumps(result, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8990)
