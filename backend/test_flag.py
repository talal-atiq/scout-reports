import requests
from bs4 import BeautifulSoup
import json

def get_correct_flag(player_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    p_resp = requests.get(player_link, headers=headers, timeout=10)
    p_soup = BeautifulSoup(p_resp.content, 'html.parser')
    
    # Let's find all flaggenrahmen and print their context
    flags = []
    for img in p_soup.find_all('img', class_='flaggenrahmen'):
        parent = img.parent
        flags.append({
            'src': img.get('src'),
            'alt': img.get('alt'),
            'title': img.get('title'),
            'parent_text': parent.get_text(strip=True)[:50] if parent else ""
        })
        
    return flags

print(json.dumps(get_correct_flag("https://www.transfermarkt.com/erling-haaland/profil/spieler/418560"), indent=2))
