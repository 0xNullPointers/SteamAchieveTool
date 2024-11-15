import os
import argparse
from curl_cffi import requests
from bs4 import BeautifulSoup
import json

def make_request(url: str) -> requests.Response:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br"
    }

    session = requests.Session(
        impersonate="safari15_5",
        headers=headers,
        timeout=30
    )
    
    session.cipher = (
        "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:"
        "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256:"
        "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256:"
        "TLS_RSA_WITH_AES_256_GCM_SHA384:TLS_RSA_WITH_AES_128_GCM_SHA256:"
        "TLS_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_AES_128_CBC_SHA:"
        "TLS_ECDHE_ECDSA_WITH_3DES_EDE_CBC_SHA:TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA:"
        "TLS_RSA_WITH_3DES_EDE_CBC_SHA"
    )
    
    session.curve = "X25519:P-256:P-384:P-521"
    
    session.sign_algo = (
        "ecdsa_secp256r1_sha256,rsa_pss_rsae_sha256,rsa_pkcs1_sha256,"
        "ecdsa_secp384r1_sha384,ecdsa_sha1,rsa_pss_rsae_sha384,"
        "rsa_pss_rsae_sha384,rsa_pkcs1_sha384,rsa_pss_rsae_sha512,"
        "rsa_pkcs1_sha512,rsa_pkcs1_sha1"
    )
    
    try:
        response = session.get(url, timeout=30)
        return response

    finally:
        session.close()

def download_images(appid: str, achievements: list):
    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)
    
    downloaded_images = set()
    
    for achievement in achievements:
        for key in ['icon', 'icongray']:
            icon_name = achievement.get(key)
            if not icon_name:
                continue

            image_file_name = icon_name.split('/')[-1]
            if image_file_name in downloaded_images:
                continue

            image_url = f"https://cdn.fastly.steamstatic.com/steamcommunity/public/images/apps/{appid}/{image_file_name}"
            response = make_request(image_url)
            
            if response.status_code == 200:
                image_path = os.path.join(image_folder, image_file_name)
                with open(image_path, 'wb') as img_file:
                    img_file.write(response.content)
                downloaded_images.add(image_file_name)

def fetch_from_steamdb(appid: str):
    url = f"https://steamdb.info/app/{appid}/stats/"
    response = make_request(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    achievements = []
    achievements_section = soup.find("h2", string="Achievements")
    table = achievements_section.find_next("table", {"class": "table"})
    achievement_rows = table.select("tbody tr")

    for row in achievement_rows:
        name = row.select_one("td").get_text(strip=True)
        display_name = row.select_one("td:nth-of-type(2)").contents[0].strip() if row.select_one("td:nth-of-type(2)") else ""
        description = row.select_one("td:nth-of-type(2) p.i").get_text(strip=True) if row.select_one("td:nth-of-type(2) p.i") else ""
        hidden, description = (1, "") if "Hidden" in description else (0, description)
        
        icons = row.select("td:nth-of-type(3) img")
        icon = icons[0].get("data-name", "") if len(icons) >= 1 else ""
        icongray = icons[1].get("data-name", "") if len(icons) >= 2 else ""

        achievement = {
            "description": description,
            "displayName": display_name,
            "hidden": hidden,
            "icon": f"images/{icon}",
            "icongray": f"images/{icongray}",
            "name": name
        }
        achievements.append(achievement)

    with open("achievementsDB.json", "w") as json_file:
        json.dump(achievements, json_file, indent=2)
    download_images(appid, achievements)

def fetch_from_steamcommunity(appid: str):
    url = f"https://steamcommunity.com/stats/{appid}/achievements/"
    response = make_request(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    achievements = []
    for idx, achievement in enumerate(soup.select('.achieveRow')):
        icon_src = achievement.select_one('.achieveImgHolder img')['src']
        icon = icon_src.split('/')[-1]
        
        displayName = achievement.select_one('.achieveTxt h3').text.strip()
        description = achievement.select_one('.achieveTxt h5').text.strip()
        hidden = 1 if description == "" else 0

        achievement = {
            "description": description,
            "displayName": displayName,
            "hidden": hidden,
            "icon": f"images/{icon}",
            "icongray": f"images/{icon}",
            "name": f"ach{idx + 1}"
        }
        achievements.append(achievement)

    with open('achievements.json', 'w') as f:
        json.dump(achievements, f, indent=2)
    download_images(appid, achievements)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("appid", type=str, help="Steam application ID")
    parser.add_argument("--steamdb", action="store_true", help="Use SteamDB to fetch achievements")
    
    args = parser.parse_args()
    
    if args.steamdb:
        fetch_from_steamdb(args.appid)
    else:
        fetch_from_steamcommunity(args.appid)
