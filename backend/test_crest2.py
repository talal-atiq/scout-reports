import requests
from bs4 import BeautifulSoup

def get_crest_html(player_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    p_resp = requests.get(player_link, headers=headers, timeout=10)
    p_soup = BeautifulSoup(p_resp.content, 'html.parser')
    
    # Try to find the box containing the club
    box = p_soup.find('div', class_='data-header__box--profile')
    if not box:
        box = p_soup.find('header', class_='data-header')
        
    if box:
        imgs = box.find_all('img')
        for img in imgs:
            if 'Manchester City' in img.get('alt', ''):
                print("Club Image Attributes:", img.attrs)
            
get_crest_html("https://www.transfermarkt.com/erling-haaland/profil/spieler/418560")
