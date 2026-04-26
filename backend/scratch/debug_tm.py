import httpx
from bs4 import BeautifulSoup
import asyncio

async def test_search(player_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name.replace(' ', '+')}"
    
    async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
        response = await client.get(search_url)
        print(f"URL after potential redirect: {response.url}")
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if we are on a search result page or a profile page
        if "/profil/spieler/" in str(response.url):
            print("Redirected directly to profile page.")
        else:
            print("On search results page.")
            # Find first player link
            player_link = None
            for a in soup.find_all('a', href=True):
                if '/profil/spieler/' in a['href']:
                    print(f"Found link: {a['href']}")
                    player_link = "https://www.transfermarkt.com" + a['href']
                    # break # Check more links
            
            if not player_link:
                print("No player link found.")

if __name__ == "__main__":
    asyncio.run(test_search("Bukayo Saka"))
