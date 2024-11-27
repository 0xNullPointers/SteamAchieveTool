import os
import json
import concurrent.futures
from bs4 import BeautifulSoup
from curl_cffi import requests
from typing import List, Dict, Set

def create_session():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", "Accept-Encoding": "gzip, deflate, br"}
    session = requests.Session(impersonate="safari15_5", headers=headers, timeout=30)

    session.cipher = ("TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256:TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256:TLS_RSA_WITH_AES_256_GCM_SHA384:TLS_RSA_WITH_AES_128_GCM_SHA256:TLS_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_AES_128_CBC_SHA:TLS_ECDHE_ECDSA_WITH_3DES_EDE_CBC_SHA:TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA:TLS_RSA_WITH_3DES_EDE_CBC_SHA")
    session.curve = "X25519:P-256:P-384:P-521"
    session.sign_algo = ("ecdsa_secp256r1_sha256,rsa_pss_rsae_sha256,rsa_pkcs1_sha256,ecdsa_secp384r1_sha384,ecdsa_sha1,rsa_pss_rsae_sha384,rsa_pss_rsae_sha384,rsa_pkcs1_sha384,rsa_pss_rsae_sha512,rsa_pkcs1_sha512,rsa_pkcs1_sha1")
    
    return session

def mk_request(url: str, session: requests.Session) -> requests.Response:
    try:
        return session.get(url, timeout=30)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL {url}: {str(e)}")

def download_one_image(args) -> bool:
    image_url, image_path, headers = args
    try:
        session = create_session()
        response = mk_request(image_url, session)
        if response.status_code == 200:
            with open(image_path, 'wb') as img_file:
                img_file.write(response.content)
            session.close()
            return True
        session.close()
    except Exception:
        return False
    return False

def download_images(appid: str, achievements: List[Dict], session: requests.Session, silent: bool = False):
    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)
    
    download_tasks = []
    downloaded_images: Set[str] = set()
    headers = session.headers
    
    total_images = 0
    for achievement in achievements:
        for key in ['icon', 'icongray']:
            icon_name = achievement.get(key)
            if icon_name and icon_name.split('/')[-1] not in downloaded_images:
                total_images += 1
                downloaded_images.add(icon_name.split('/')[-1])
    
    downloaded_images.clear()
    
    for achievement in achievements:
        for key in ['icon', 'icongray']:
            icon_name = achievement.get(key)
            if not icon_name:
                continue

            image_file_name = icon_name.split('/')[-1]
            if image_file_name in downloaded_images:
                continue

            image_url = f"https://cdn.fastly.steamstatic.com/steamcommunity/public/images/apps/{appid}/{image_file_name}"
            image_path = os.path.join(image_folder, image_file_name)
            
            download_tasks.append((image_url, image_path, headers))
            downloaded_images.add(image_file_name)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(download_one_image, download_tasks))

def fetch_from_steamdb(appid: str, silent: bool = False):
    session = create_session()
    url = f"https://steamdb.info/app/{appid}/stats/"
    if not silent:
        print("Fetching achievements from SteamDB...")
    response = mk_request(url, session)
    soup = BeautifulSoup(response.content, 'html.parser')

    achievements = []
    achievements_section = soup.find("h2", string="Achievements")
    if not achievements_section:
        session.close()
        return achievements

    table = achievements_section.find_next("table", {"class": "table"})
    if not table:
        session.close()
        return achievements
        
    rows = table.select("tbody tr")
    if not silent:
        print(f"Found {len(rows)} achievements...")

    for row in rows:
        name = row.select_one("td").get_text(strip=True)
        second_column = row.select_one("td:nth-of-type(2)")
        display_name = second_column.contents[0].strip() if second_column else ""
        description_tag = second_column.select_one("p.i") if second_column else None
        description = description_tag.get_text(strip=True) if description_tag else ""
        hidden, description = (1, "") if "Hidden" in description else (0, description)
        
        icons = row.select("td:nth-of-type(3) img")
        icon = icons[0].get("data-name", "") if len(icons) >= 1 else ""
        icongray = icons[1].get("data-name", "") if len(icons) >= 2 else ""

        achievements.append({
            "description": description,
            "displayName": display_name,
            "hidden": hidden,
            "icon": f"images/{icon}",
            "icongray": f"images/{icongray}",
            "name": name
        })

    with open("achievements.json", "w", encoding='utf-8') as json_file:
        json.dump(achievements, json_file, indent=2, ensure_ascii=False)
    
    download_images(appid, achievements, session, silent)
    session.close()
    return achievements

def fetch_from_steamcommunity(appid: str, silent: bool = False):
    session = create_session()
    url = f"https://steamcommunity.com/stats/{appid}/achievements/"
    if not silent:
        print("Fetching achievements from Steam Community...")
    response = mk_request(url, session)
    soup = BeautifulSoup(response.content, 'html.parser')

    achievements = []
    achievement_rows = soup.select('.achieveRow')
    if not silent:
        print(f"Found {len(achievement_rows)} achievements...")

    for idx, achievement in enumerate(achievement_rows):
        icon_src = achievement.select_one('.achieveImgHolder img')['src']
        icon = icon_src.split('/')[-1]
        
        displayName = achievement.select_one('.achieveTxt h3').text.strip()
        description_tag = achievement.select_one('.achieveTxt h5')
        description = description_tag.text.strip() if description_tag else ""
        hidden = 1 if description == "" else 0

        achievements.append({
            "description": description,
            "displayName": displayName,
            "hidden": hidden,
            "icon": f"images/{icon}",
            "icongray": f"images/{icon}",
            "name": f"ach{idx + 1}"
        })

    with open('achievements.json', 'w', encoding='utf-8') as json_file:
        json.dump(achievements, json_file, indent=2, ensure_ascii=False)
    
    download_images(appid, achievements, session, silent)
    session.close()
    return achievements


# def main():
#     # Commented out argparse functionality
#     parser = argparse.ArgumentParser()
#     parser.add_argument("appid", type=str, help="Steam application ID")
#     parser.add_argument("--steam", action="store_true", help="Use SteamCommunity to fetch achievements")
#     parser.add_argument("--silent", "-s", action="store_true", help="Suppress all output")
    
#     args = parser.parse_args()
    
#     try:
#         # Replace with your specific implementation
#         appid = "your_appid_here"  # Replace with the actual Steam app ID
#         fetch_from_steamdb(appid)  # Or use fetch_from_steamcommunity(appid)
#     except Exception as e:
#         print(f"\nAn error occurred: {str(e)}")
#         return 1
#     return 0

# if __name__ == "__main__":
#     sys.exit(main())