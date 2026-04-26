import requests
from bs4 import BeautifulSoup

def get_market_value(player_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    p_resp = requests.get(player_link, headers=headers, timeout=10)
    p_soup = BeautifulSoup(p_resp.content, 'html.parser')
    
    mv_tag = p_soup.find('a', class_='data-header__market-value-wrapper')
    if mv_tag:
        mv_text = mv_tag.get_text(separator=' ', strip=True)
        if 'Last update' in mv_text:
            return mv_text.split('Last update')[0].strip()
        else:
            return mv_text.strip()
    
    return "Not found"
            
val = get_market_value("https://www.transfermarkt.com/richarlison/profil/spieler/378710")
print("Raw value:", repr(val))
print("Without spaces:", repr(val.replace(' ', '')))
