import requests
from bs4 import BeautifulSoup
import json

def get_market_value(player_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    p_resp = requests.get(player_link, headers=headers, timeout=10)
    p_soup = BeautifulSoup(p_resp.content, 'html.parser')
    
    mv_tag = p_soup.find('a', class_='data-header__market-value-wrapper')
    if mv_tag:
        return mv_tag.get_text(separator=' ', strip=True)
    
    return "Not found"
            
print(get_market_value("https://www.transfermarkt.com/erling-haaland/profil/spieler/418560"))
