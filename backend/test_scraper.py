import requests
from bs4 import BeautifulSoup
import json
import traceback

def search_transfermarkt(player_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Cache-Control': 'max-age=0',
    }
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name.replace(' ', '+')}"
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(search_url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find first player link
        player_link = None
        for a in soup.find_all('a', href=True):
            if '/profil/spieler/' in a['href']:
                player_link = "https://www.transfermarkt.com" + a['href']
                break
                
        if not player_link:
            print(f"Status: {response.status_code}")
            # print(f"Content snippet: {response.text[:500]}")
            return "No player found"
            
        p_resp = session.get(player_link, timeout=30)
        p_soup = BeautifulSoup(p_resp.content, 'html.parser')
        
        # Extract Image
        img_tag = p_soup.find('img', class_='data-header__profile-image')
        player_pic = img_tag.get('src') if img_tag else None
        
        # Extract Club Crest
        crest_tag = p_soup.find('a', class_='data-header__box__club-link')
        club_crest = None
        if crest_tag:
            img = crest_tag.find('img')
            if img:
                club_crest = img.get('src') or img.get('data-src')
            
        # Extract Nation Flag
        flag_tag = p_soup.find('img', class_='flaggenrahmen')
        nation_flag = None
        if flag_tag:
            nation_flag = flag_tag.get('src') or flag_tag.get('data-src')
        
        # Extract Info Table
        age = None
        preferred_foot = None
        
        for li in p_soup.find_all('li', class_='data-header__label'):
            text = li.get_text(strip=True).lower()
            if 'age:' in text:
                age = li.find('span').get_text(strip=True) if li.find('span') else text.split(':')[-1].strip()

        # Try another way for age/foot if not found
        info_table = p_soup.find('div', class_='info-table')
        if info_table:
            for row in info_table.find_all('span', class_='info-table__content'):
                text = row.get_text(strip=True)
                prev = row.find_previous_sibling('span')
                if prev:
                    label = prev.get_text(strip=True).lower()
                    if 'age:' in label and not age:
                        age = text
                    elif 'foot:' in label:
                        preferred_foot = text
                        
        if not preferred_foot:
            # TM often has foot in the info table under "Foot:"
            for span in p_soup.find_all('span'):
                if span.get_text(strip=True) == 'Foot:':
                    next_span = span.find_next_sibling('span')
                    if next_span:
                        preferred_foot = next_span.get_text(strip=True)

        return {
            "player_picture": player_pic,
            "club_crest": club_crest,
            "nation_flag": nation_flag,
            "age": age,
            "preferred_foot": preferred_foot
        }
        
    except Exception as e:
        return traceback.format_exc()

print(json.dumps(search_transfermarkt("Elliot Anderson"), indent=2))
