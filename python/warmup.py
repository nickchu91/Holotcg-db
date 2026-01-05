import requests
from bs4 import BeautifulSoup
import mysql.connector
import time
import re
from urllib.parse import urlparse, parse_qs

# ==========================================
# 1. 設定與工具函式
# ==========================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Nickchu20020611',  # 記得改密碼
    'database': 'hololiveOfficialCardGame'
}



HEADERS = {     # 告訴伺服器「我是 Chrome 瀏覽器」，而不是「我是 Python 程式」
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

COLOR_MAP = {
    'type_red': 'RED', 'type_blue': 'BLUE', 'type_green': 'GREEN',
    'type_yellow': 'YELLOW', 'type_purple': 'PURPLE', 'type_white': 'WHITE',
    'type_null': 'NULL'
    # 根據你的 oshi_cards 設定
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def parse_colors_flattened(img_list):
    
    # 1. 初始化：全部設為 False
    colors = {
        'is_red': False, 'is_blue': False, 'is_green': False,
        'is_yellow': False, 'is_purple': False, 'is_white': False
    }
    
    # 2. 檢查圖片 (hSD01-013 只有一張圖，但我們還是跑迴圈比較保險)
    for img in img_list:
        src = img.get('src', '')
        
        # --- 關鍵修改：全部改用 if，不要用 elif ---
        # 這樣如果檔名是 "type_white_green.png"
        # 程式會同時執行 'white' 和 'green' 的判斷區塊
        
        if 'red' in src: 
            colors['is_red'] = True
            
        if 'blue' in src: 
            colors['is_blue'] = True
            
        if 'green' in src: 
            colors['is_green'] = True
            
        if 'yellow' in src: 
            colors['is_yellow'] = True
            
        if 'purple' in src: 
            colors['is_purple'] = True
            
        if 'white' in src: 
            colors['is_white'] = True
            
    return colors

def calculate_flattened_cost(cost_img_list):
    """
    計算扁平化的藝能花費
    輸入: 包含 img 標籤的 list
    輸出: 字典 {'cost_red': 1, 'cost_white': 2, ...}
    """
    # 初始化你的資料表欄位 (全部設為 0)
    costs = {
        'cost_red': 0, 'cost_blue': 0, 'cost_green': 0, 'cost_yellow': 0,
        'cost_purple': 0, 'cost_white': 0, 'cost_any': 0
    }
    
    for img in cost_img_list:
        src = img.get('src', '')
        if 'red' in src: costs['cost_red'] += 1
        elif 'blue' in src: costs['cost_blue'] += 1
        elif 'green' in src: costs['cost_green'] += 1
        elif 'yellow' in src: costs['cost_yellow'] += 1
        elif 'purple' in src: costs['cost_purple'] += 1
        elif 'white' in src: costs['cost_white'] += 1
        elif 'null' in src: costs['cost_any'] += 1
        
    return costs

'''def get_card_links_from_list(list_url):
    """
    輸入: 列表頁面的網址 
    輸出: 該頁面上所有卡片的詳細頁網址 (List)
    """
    print(f"正在分析列表頁面: {list_url}")
    try:
        response = requests.get(list_url, headers=HEADERS)
        response.raise_for_status()
    except Exception as e:
        print(f"列表頁面連線失敗: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    #  鎖定卡片列表區塊 (根據你的截圖)
    # 找 class 為 "cardlist-Result_List" 裡面的所有 <a> 標籤
    links = []
    card_links = soup.select('.cardlist-Result_List a')
    
    for a in card_links:
        href = a.get('href')
        if href and 'id=' in href: # 確保連結裡有 id 參數
            # href 抓下來是相對路徑 "/cardlist/?id=..."
            # 我們要把它補全成絕對路徑
            full_url = f"https://hololive-official-cardgame.com{href}"
            links.append(full_url)
    
    # 使用 set 去除重複的連結 (有時候網頁排版會有重複連結)，再轉回 list
    unique_links = list(set(links))
    print(f"找到 {len(unique_links)} 張卡片！")
    return unique_links'''

def get_card_links_from_list(list_url):
    """
    改良版 v2: 支援 cardsearch_ex 無限捲動 API
    """
    all_links = []

    # 從原本的網址 (cardsearch) 抓出 expansion 代號 (如 hBP02)
    parsed_url = urlparse(list_url)
    query_params = parse_qs(parsed_url.query)

    expansion_id = query_params.get('expansion', [None])[0]
    if not expansion_id:
        print("錯誤: 無法從網址中解析出 expansion 參數，請確認網址格式。")
        return []
    
    print(f"目標卡包: {expansion_id}")

    # ---  抓取第 1 頁 (正門) ---
    print("正在抓取第 1 頁 (主頁面)...")
    try:
        response = requests.get(list_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.select('.cardlist-Result_List a')
        for a in links:
            href = a.get('href')
            if href and 'id=' in href:
                full_url = f"https://hololive-official-cardgame.com{href}"
                all_links.append(full_url)
                
        print(f"第 1 頁找到 {len(links)} 張卡片。")
        
    except Exception as e:
        print(f"主頁面連線失敗: {e}")
        return []
    
    # ---  抓取第 2 頁以後 (後門 API) ---
    # API 網址: https://hololive-official-cardgame.com/cardlist/cardsearch_ex
    api_base_url = "https://hololive-official-cardgame.com/cardlist/cardsearch_ex"
    
    page = 2
    while True:
        # 建構 API 請求參數
        # 根據你的截圖，參數包含 expansion, view=image, page, t(時間戳記)
        params = {
            "expansion": expansion_id,
            "view": "image",
            "page": page,
            "t": int(time.time() * 1000) # 模擬瀏覽器的時間戳記 (毫秒)
        }
        
        print(f"正在請求第 {page} 頁 API...", end=" ")
        
        try:
            # 發送請求給 API
            api_response = requests.get(api_base_url, headers=HEADERS, params=params)
            
            # 如果 API 回傳空的，或者狀態碼不對，就停止
            if api_response.status_code != 200 or not api_response.text.strip():
                print("回應為空，判斷已無更多頁面。")
                break
                
            # API 回傳的內容通常直接就是 HTML 片段 (<li>...</li>)
            # 所以我們一樣用 BeautifulSoup 去解析它
            api_soup = BeautifulSoup(api_response.text, 'html.parser')
            
            # 這裡的 selector 可能不需要 .cardlist-Result_List，因為回傳的本身就是列表項目
            # 我們直接抓所有的 <a> 試試看
            new_links = api_soup.find_all('a')
            
            current_page_count = 0
            for a in new_links:
                href = a.get('href')
                if href and 'id=' in href:
                    full_url = f"https://hololive-official-cardgame.com{href}"
                    # 防止重複加入
                    if full_url not in all_links:
                        all_links.append(full_url)
                        current_page_count += 1
            
            print(f"找到 {current_page_count} 張新卡片。")
            
            if current_page_count == 0:
                print("本頁無新卡片，結束爬取。")
                break
                
            page += 1
            time.sleep(1) # 禮貌性休息
            
        except Exception as e:
            print(f"\nAPI 連線發生錯誤: {e}")
            break

    # 去重
    unique_links = list(set(all_links))
    print(f"=== 列表收集完成！總共 {len(unique_links)} 張卡片 ===")
    return unique_links


# 自動分析sp_tags
def analyze_sp_tags(card_data):
    detected_tags = set()
    # 收集這張卡所有的敘述文字
    full_text_list = []

    # 成員卡效果
    full_text_list.append(str(card_data.get('bloom_effect', '')))
    full_text_list.append(str(card_data.get('collab_effect', '')))
    full_text_list.append(str(card_data.get('gift_effect', '')))
    # 主推卡效果
    full_text_list.append(str(card_data.get('oshi_skill', '')))
    full_text_list.append(str(card_data.get('sp_oshi_skill', '')))
    # 支援卡效果
    full_text_list.append(str(card_data.get('effect_text', '')))
    # 藝能效果 (可能有好多個)
    if 'arts_data_list' in card_data:
        for art in card_data['arts_data_list']:
            full_text_list.append(str(art.get('description', '')))
    # 合併成一個大字串
    full_text = " ".join(full_text_list)

    # 看效果型 (關鍵字搜尋)
    if '自分のデッキを' in full_text and '引く' in full_text:
        detected_tags.add('DRAW')
    # Search (牌組檢索): [自分のデッキ] AND [公開し] AND [手札に加える]
    if '自分のデッキ' in full_text and '公開し' in full_text and '手札に加える' in full_text:
        detected_tags.add('SEARCH')
        
    # Heal (回血): [HP] AND [回復]
    if 'HP' in full_text and '回復' in full_text:
        detected_tags.add('HEAL')
        
    # Archive_Search (存檔區檢索): [自分のアーカイブ] AND [手札に戻す]
    if '自分のアーカイブ' in full_text and '手札に戻す' in full_text:
        detected_tags.add('ARCHIVE_SEARCH')
        
    # Damage_Increase: [アーツ+]
    if 'アーツ+' in full_text:
        detected_tags.add('DMG_INCREASE')
        
    # HP_Increase: [HP+]
    if 'HP+' in full_text:
        detected_tags.add('HP_INCREASE')
        
    # Special_Damage: [特殊ダメージ]
    if '特殊ダメージ' in full_text:
        detected_tags.add('SPECIAL_DAMAGE')
        
    # Archive (送牌進存檔區): [をアーカイブ]
    if 'をアーカイブ' in full_text:
        detected_tags.add('ARCHIVE_SEND')
        
    # Damage_Decrease: [受けるダメージ-]
    if '受けるダメージ-' in full_text:
        detected_tags.add('DMG_DECREASE')
        
    # Cheer_Deck (應援牌組填應援): [自分のエールデッキ] AND [送る]
    if '自分のエールデッキ' in full_text and '送る' in full_text:
        detected_tags.add('CHEER_DECK_SEND')
        
    # Archive_Cheer (存檔區填應援): [アーカイブ] AND [エール] (需小心誤判，但根據規則)
    if 'アーカイブ' in full_text and 'エール' in full_text:
        detected_tags.add('ARCHIVE_CHEER')
        
    # Guard (守護): [自分のコラボホロメンしか対象]
    if '自分のコラボホロメンしか対象' in full_text:
        detected_tags.add('GUARD')
        
    # Limited
    if 'LIMITED' in full_text or card_data.get('is_limited') == True:
        detected_tags.add('LIMITED')

    # 指定欄位有沒有值
    if card_data.get('collab_effect_name'):
        detected_tags.add('HAS_COLLAB')
        
    if card_data.get('gift_effect_name'):
        detected_tags.add('HAS_GIFT')
        
    if card_data.get('bloom_effect_name'):
        detected_tags.add('HAS_BLOOM')
    
    # 看特殊規則 (extra_rule)
    extra_rule = str(card_data.get('extra_rule', ''))
    
    if '何枚でも入' in extra_rule:
        detected_tags.add('UNLIMITED')
        
    if '自分のライフ-2' in extra_rule:
        detected_tags.add('BUZZ')
    
    # 特攻顏色 (Arts)
    if 'arts_data_list' in card_data:
        for art in card_data['arts_data_list']:
            tokkou = art.get('tokkou_color') # 這裡假設你爬蟲存的是 'RED', 'BLUE' 等字串
            if tokkou:
                # 轉成對應的 tag slug，例如 RED -> TOK_RED
                slug = f"TOK_{tokkou}"
                detected_tags.add(slug)

    # 看卡片名字
    card_name = str(card_data.get('name', ''))
    if 'パソコン' in card_name:
        detected_tags.add('PC')

    return list(detected_tags)

# ==========================================
#  爬蟲區 (Parser)
# ==========================================

def parse_card_page(url):
    print(f"正在爬取: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status() # 檢查是否有 404 等錯誤
    except Exception as e:
        print(f"連線失敗: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    data = {}
    # --- A. 通用資料 (cards 表) ---
    # TODO: 以下 selector 需要你用 F12 確認
    try:
        data['number'] = soup.select_one('.number span').text.strip() # 卡號擷取
        data['name'] = soup.select_one('.txt .name').text.strip() # 卡名擷取

        rarity_label = soup.find('dt', string='レアリティ')     # 卡片稀有度擷取
        if rarity_label:    
            data['rarity'] = rarity_label.find_next_sibling('dd').text.strip() 
        else:
            data['rarity'] = 'N/A' 
        
        '''product_label = soup.find('dt', string='収録商品')   # 收錄名稱擷取
        if product_label:
            product_dd = product_label.find_next_sibling('dd')
            lines = list(product_dd.stripped_strings)   # 使用 stripped_strings 取得分段的文字列表
            if lines:
                data['product'] = lines[-1] # 取最後一行作為收錄名稱
            else:
                data['product'] = 'N/A'
        else:
            data['product'] = 'N/A' '''
        
        img_tag = soup.select_one('.img.w100 img')  # 卡片圖片擷取
        if img_tag:
            rel_path = img_tag['src']
            data['image_url'] = f"https://hololive-official-cardgame.com{rel_path}"
        else:
            data['image_url'] = None
                
        # 判斷卡片種類 
        type_label = soup.find('dt', string='カードタイプ')
        if type_label:
            raw_type = type_label.find_next_sibling('dd').text.strip()
        else:
            raw_type = ""

        if '推しホロメン' in raw_type or 'Oshi Holomen' in raw_type:
            data['type'] = 'OSHI'
        elif 'ホロメン' in raw_type or 'Holomem' in raw_type:
            data['type'] = 'HOLOMEM'
        elif 'エール' in raw_type or 'Cheer' in raw_type:
            data['type'] = 'CHEER'
        else:
            data['type'] = 'SUPPORT' # 包含 Event, Item 等
    except AttributeError as e:
        print(f"解析基本資料失敗 (可能 selector 錯誤): {e}")
        return None
    
    # --- B. 根據種類解析詳細資料 ---
    
    # 1. 解析主推卡 (OSHI)
    if data['type'] == 'OSHI':  
        color_label = soup.find('dt', string='色')  # 顏色擷取
        if color_label:
            color_imgs = color_label.find_next_sibling('dd').find_all('img')
            data['colors'] = parse_colors_flattened(color_imgs)
        else:
            data['colors'] = parse_colors_flattened([]) # 預設值

        life_label = soup.find('dt', string='LIFE')
        if life_label:
            data['life'] = int(life_label.find_next_sibling('dd').text.strip())

        oshi_block = soup.select_one('.oshi.skill') # 推しスキル區塊
        if oshi_block:
            content_p = oshi_block.find_all('p')[1]
            name_span = content_p.find('span')
            if name_span:
                data['oshi_skill_name'] = name_span.text.strip()
                raw_cost = name_span.previous_sibling
                if raw_cost:
                    # 清洗資料：去掉前後空白，並去掉可能存在的雙引號
                    data['oshi_skill_power_cost'] = raw_cost.strip().replace('"', '')
                raw_desc = name_span.next_sibling
                if raw_desc:
                    data['oshi_skill'] = raw_desc.strip().replace('"', '')
                    
            else:
                # 如果沒有 span，可能是格式跑掉了，做個錯誤處理
                print("找不到技能名稱的 span")

        oshi_block = soup.select_one('.sp.skill') # SP推しスキル區塊
        if oshi_block:
            content_p = oshi_block.find_all('p')[1]
            name_span = content_p.find('span')
            if name_span:
                data['sp_oshi_skill_name'] = name_span.text.strip()
                raw_cost = name_span.previous_sibling
                if raw_cost:
                    # 清洗資料：去掉前後空白，並去掉可能存在的雙引號
                    data['sp_oshi_skill_power_cost'] = raw_cost.strip().replace('"', '')
                raw_desc = name_span.next_sibling
                if raw_desc:
                    data['sp_oshi_skill'] = raw_desc.strip().replace('"', '')
                    
            else:
                # 如果沒有 span，可能是格式跑掉了，做個錯誤處理
                print("找不到技能名稱的 span")
        
    # 2. 解析一般卡 (HOLOMEM)
    elif data['type'] == 'HOLOMEM':
        color_label = soup.find('dt', string='色')  # 顏色擷取
        if color_label:
            color_imgs = color_label.find_next_sibling('dd').find_all('img')
            data['colors'] = parse_colors_flattened(color_imgs)
        else:
            data['colors'] = parse_colors_flattened([]) # 預設值

        hp_label = soup.find('dt', string='HP')     # 生命值擷取
        if hp_label:
            data['hp'] = int(hp_label.find_next_sibling('dd').text.strip())
        else:
            data['hp'] = 0  # 預設值
        
        #

        # Bloom Level 
        if(bloom_label := soup.find('dt', string='Bloomレベル')):
            raw_level = bloom_label.find_next_sibling('dd').text.strip()
        else:
            raw_level = ""
        
        if 'Debut' in raw_level: data['bloom_level'] = 'DEBUT'
        elif '1st' in raw_level: data['bloom_level'] = '1ST'
        elif '2nd' in raw_level: data['bloom_level'] = '2ND'
        elif 'Spot' in raw_level: data['bloom_level'] = 'SPOT'
        
        baton_label = soup.find('dt', string='バトンタッチ')    # Baton  擷取
        if baton_label:
            baton_dd = baton_label.find_next_sibling('dd')
            # 計算裡面有幾張圖片 (img)
            data['baton_cost'] = len(baton_dd.find_all('img'))
        else:
            data['baton_cost'] = 0
        
        # 關鍵字 Keywords
        data['bloom_effect_name'] = None; data['bloom_effect'] = None
        data['gift_effect_name'] = None; data['gift_effect'] = None
        data['collab_effect_name'] = None; data['collab_effect'] = None
        keyword_block = soup.select_one('.keyword')
        if keyword_block:
            all_icons = keyword_block.find_all('img')
            for icon in all_icons:
                src = icon.get('src', '')
                alt = icon.get('alt', '')
                
                # 抓取「效果名稱」 (圖片後面的文字，在 span 裡面)
                raw_name = icon.next_sibling 
                effect_name = raw_name.strip().replace('"', '') if raw_name else ""
                
                # 抓取「效果敘述」 (span 結束後的文字，在 p 裡面)
                effect_desc_node = icon.parent.next_sibling
                effect_desc = effect_desc_node.strip().replace('"', '') if effect_desc_node else ""

                # 根據圖片特徵填入對應欄位
                # 判斷 Bloom Effect
                if 'bloomEF' in src or 'ブルームエフェクト' in alt:
                    data['bloom_effect_name'] = effect_name
                    data['bloom_effect'] = effect_desc
                    
                # 判斷 Collab Effect
                elif 'collabEF' in src or 'コラボエフェクト' in alt:
                    data['collab_effect_name'] = effect_name
                    data['collab_effect'] = effect_desc
                    
                # 判斷 Gift Effect
                elif 'gift' in src or 'ギフト' in alt:
                    data['gift_effect_name'] = effect_name
                    data['gift_effect'] = effect_desc

        #extra 效果擷取
        data['extra_rule'] = None
        extra_block = soup.select_one('.extra')
        if extra_block:
            extra_label = extra_block.find('p', string='エクストラ')
            if extra_label:
                extra_content_node = extra_label.find_next_sibling('p')
                if extra_content_node:
                    data['extra_rule'] = extra_content_node.text.strip()
            
    
        # 標籤 Tags
        data['tags'] = []
        tag_label = soup.find('dt', string='タグ')
        if tag_label:
    
            tag_dd = tag_label.find_next_sibling('dd')
            
            if tag_dd:
                tag_links = tag_dd.find_all('a')    #抓取裡面所有的 <a> 標籤
                for link in tag_links:
                    raw_tag = link.text.strip().replace('#', '')  # 去掉前後空白和 #號
                    if raw_tag:
                        data['tags'].append(raw_tag)
        

        # 藝能 Arts (多個)
        arts_data_list = []

        art_blocks = soup.select('.sp.arts') 
        for block in art_blocks:
            art_info = {
                'name': 'Unknown',
                'damage': '',         # 資料庫是 VARCHAR，預設空字串
                'description': '',
                'tokkou_color': None, 
                'tokkou_damage': None,
                'costs': {}           
            }
            p_tags = block.find_all('p')
            content_p = p_tags[1]   # 第二個 <p> 標籤，包含藝能名稱和敘述
            main_span = content_p.find('span')
            # 藝能費用&特攻顏色&特工傷害擷取
            if main_span:
                all_imgs = main_span.find_all('img')    # 取得所有圖片
                cost_imgs = [img for img in all_imgs if 'tokkou' not in img.get('src', '')]
                art_info['arts_cost'] = calculate_flattened_cost(cost_imgs)
            
                # 特攻顏色與傷害
                tokkou_span = main_span.select_one('.tokkou')
                if tokkou_span:
                    tokkou_img = tokkou_span.find('img')
                    if tokkou_img:
                        src = tokkou_img.get('src', '')
                        match = re.search(r'tokkou_(\d+)_([a-z]+)', src)
                        if match:
                            art_info['tokkou_damage'] = int(match.group(1)) # 50
                            raw_color = match.group(2).upper()              # YELLOW
                            
                            if raw_color in ['RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE', 'WHITE']:
                                art_info['tokkou_color'] = raw_color
                # 藝能名稱與傷害
                full_text = main_span.get_text(strip=True)
                if tokkou_span:
                    tokkou_text = tokkou_span.get_text(strip=True)
                    # 把特攻的文字(如果有)從總文字中扣掉，只剩下 "名稱 傷害"
                    name_damage_str = full_text.replace(tokkou_text, '').strip()
                else:
                    name_damage_str = full_text

                nd_match = re.search(r'^(.*?)\s*(\d+\+?)$', name_damage_str)
                if nd_match:
                    art_info['name'] = nd_match.group(1).strip()
                    art_info['damage'] = nd_match.group(2)
                else:
                    # 如果沒有傷害數字 (例如 Support 技能)，整個字串就是名字
                    art_info['name'] = name_damage_str
                    art_info['damage'] = '' # 無傷害

                # --- 處理描述 ---
                # 描述文字在 main_span 的後面
                raw_desc = main_span.next_sibling
                if raw_desc:
                    art_info['description'] = raw_desc.strip().replace('"', '')
                
            else:
                continue

            arts_data_list.append(art_info)
        data['arts_data_list'] = arts_data_list

    elif data['type'] == 'CHEER':
        color_label = soup.find('dt', string='色')  # 顏色擷取
        if color_label:
            color_imgs = color_label.find_next_sibling('dd').find_all('img')
            data['colors'] = parse_colors_flattened(color_imgs)
        else:
            data['colors'] = parse_colors_flattened([]) # 預設值
    elif data['type'] == 'SUPPORT':
        data['sub_type'] = 'EVENT'
        data['is_limited'] = False
        type_label = soup.find('dt', string='カードタイプ')
        if type_label:
            raw_type_text = type_label.find_next_sibling('dd').text.strip()
        else:
            raw_type_text = ""
        if 'LIMITED' in raw_type_text:
            data['is_limited'] = True
        #------------------------------------------------------
        # 判斷 SUPPORT 卡的子類型 (EVENT / ITEM / TOOL /
        if 'イベント' in raw_type_text:
            data['sub_type'] = 'EVENT'
        elif 'アイテム' in raw_type_text:
            data['sub_type'] = 'ITEM'
        elif 'ツール' in raw_type_text:
            data['sub_type'] = 'TOOL'
        elif 'マスコット' in raw_type_text: 
            data['sub_type'] = 'MASCOT' 
        elif 'スタッフ' in raw_type_text: 
            data['sub_type'] = 'STAFF'
        elif 'ファン' in raw_type_text: 
            data['sub_type'] = 'FAN'
        #------------------------------------------------------
        effect_label = soup.find('dt', string='能力テキスト')
        if effect_label:
            effect_text = effect_label.find_next_sibling('dd')
            raw_text = effect_text.get_text(separator='\n')
            data['effect_text'] = raw_text.strip()
        else:
            data['effect_text'] = ''

        data['tags'] = []
        tag_label = soup.find('dt', string='タグ')
        if tag_label:
    
            tag_dd = tag_label.find_next_sibling('dd')
            
            if tag_dd:
                tag_links = tag_dd.find_all('a')    #抓取裡面所有的 <a> 標籤
                for link in tag_links:
                    raw_tag = link.text.strip().replace('#', '')  # 去掉前後空白和 #號
                    if raw_tag:
                        data['tags'].append(raw_tag)
#--------------------------------------------------
    return data 

# 資料庫存檔工具函式
def save_to_database(data):
    if not data:
        return
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn.start_transaction() # 開始交易，這樣如果存藝能或標籤時出錯，可以全部撤回，不會留下斷頭資料
        
        # 這是一個幫你檢查 SQL 和參數數量是否對應的小工具
        def debug_execute(sql, params, table_name):
            param_count = len(params)
            placeholder_count = sql.count('%s')
            if param_count != placeholder_count:
                print(f"!!! [錯誤偵測] 表格: {table_name} !!!")
                print(f"    - 參數數量 (Python): {param_count}")
                print(f"    - 佔位符數量 (%s): {placeholder_count}")
                print(f"    - 你的 SQL: {sql.strip()[:100]}...") # 只印前100字避免太長
                # 這裡會故意讓它報錯，這樣你才能看到上面的訊息
            cursor.execute(sql, params)
        #---------------------------------------------------------------------------
        # 寫入主表 (cards)
        #---------------------------------------------------------------------------
        sql_card = """
            INSERT INTO cards (card_number, card_name, rarity, card_type, image_url)
            VALUES (%s, %s, %s, %s, %s)
        """

        card_params= (
            data.get('number'),
            data.get('name'),
            data.get('rarity'),
            data.get('type'),
            data.get('image_url')
        )
        debug_execute(sql_card, card_params, "cards")
        new_card_id = cursor.lastrowid
        print(f"成功寫入 cards 表，Card ID: {new_card_id}")
        #---------------------------------------------------------------------------
        # 根據卡片類型，寫入相關子表

        # 1. 主推卡 (OSHI)
        if data['type'] == 'OSHI':
            c = data.get('colors', {}) # 顏色字典
            sql_oshi = """
                INSERT INTO oshi_cards 
                (card_id, life,
                oshi_skill_name, oshi_skill_power_cost, oshi_skill,
                sp_oshi_skill_name, sp_oshi_skill_power_cost, sp_oshi_skill ,
                is_red, is_blue, is_green, is_yellow, is_purple, is_white)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_oshi, (
                new_card_id,
                data.get('life'),
                data.get('oshi_skill_name'),
                data.get('oshi_skill_power_cost'),
                data.get('oshi_skill'),
                data.get('sp_oshi_skill_name'),
                data.get('sp_oshi_skill_power_cost'),
                data.get('sp_oshi_skill'),
                c.get('is_red', False),
                c.get('is_blue', False),
                c.get('is_green', False),
                c.get('is_yellow', False),
                c.get('is_purple', False),
                c.get('is_white', False)
            ))
            print(f"成功寫入 oshi_cards 表，Card ID: {new_card_id}")

        # 2. 一般卡 (HOLOMEM)
        elif data['type'] == 'HOLOMEM':
            c = data.get('colors', {}) # 顏色字典
            sql_holomem = """
                INSERT INTO holomem_cards 
                (card_id, hp, bloom_level, baton_cost,
                bloom_effect_name, bloom_effect,
                gift_effect_name, gift_effect,
                collab_effect_name, collab_effect,
                extra_rule,
                is_red, is_blue, is_green, is_yellow, is_purple, is_white)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            mem_params= (
                new_card_id,
                data.get('hp'),
                data.get('bloom_level'),
                data.get('baton_cost'),
                data.get('bloom_effect_name'),data.get('bloom_effect'),
                data.get('gift_effect_name'),data.get('gift_effect'),
                data.get('collab_effect_name'),data.get('collab_effect'),
                data.get('extra_rule'),
                c.get('is_red', False),
                c.get('is_blue', False),
                c.get('is_green', False),
                c.get('is_yellow', False),
                c.get('is_purple', False),
                c.get('is_white', False)
            )

            debug_execute(sql_holomem, mem_params, "holomem_cards")
            print(f"成功寫入 holomem_cards 表，Card ID: {new_card_id}")
            # --- 處理標籤 (Tags) ---
            for tag_name in data.get('tags', []):
                # 確保標籤存在 (如果不存在就插入，存在就忽略)
                cursor.execute("INSERT IGNORE INTO tags (tag_name) VALUES (%s)", (tag_name,))
                # 查出該標籤 ID
                cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag_name,))
                tag_row = cursor.fetchone()
                if tag_row:
                    tag_id = tag_row[0]
                    #  建立關聯
                    cursor.execute("INSERT INTO card_tags (card_id, tag_id) VALUES (%s, %s)", (new_card_id, tag_id))
                    print(f"成功寫入 card_tags 表，Card ID: {tag_name}")
            # --- 處理藝能 (Arts) ---
            if 'arts_data_list' in data:
                sql_art = """
                    INSERT INTO card_arts 
                    (card_id, art_name, art_damage, art_description, 
                    cost_red, cost_blue, cost_green, cost_yellow, cost_purple, cost_white, cost_any,
                    tokkou, tokkou_damage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                for art in data['arts_data_list']:
                    costs = art.get('arts_cost', {}) 
                    art_params=(
                        new_card_id,
                        art.get('name'),
                        art.get('damage'),
                        art.get('description'),
                        # 展開 Cost 字典
                        costs.get('cost_red', 0), costs.get('cost_blue', 0), costs.get('cost_green', 0),
                        costs.get('cost_yellow', 0), costs.get('cost_purple', 0), costs.get('cost_white', 0),
                        costs.get('cost_any', 0),
                        # 特攻資料
                        art.get('tokkou_color'),
                        art.get('tokkou_damage')
                    )
                    debug_execute(sql_art, art_params, "card_arts")
                    print(f"成功寫入 card_arts 表，Card ID: {new_card_id}")

        # ===  應援卡 (CHEER) ===
        elif data['type'] == 'CHEER':
            c = data.get('colors', {})
            sql_cheer = """
                INSERT INTO cheer_cards (card_id, is_red, is_blue, is_green, is_yellow, is_purple, is_white)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cheer_params =(
                new_card_id,
                c.get('is_red', False), c.get('is_blue', False), c.get('is_green', False),
                c.get('is_yellow', False), c.get('is_purple', False), c.get('is_white', False)
            )
            debug_execute(sql_cheer, cheer_params, "cheer_cards")

        # ===  支援卡 (SUPPORT) ===
        elif data['type'] == 'SUPPORT':
            sql_support = """
                INSERT INTO support_cards (card_id, support_card_type, limited, effect)
                VALUES (%s, %s, %s, %s)
            """
            support_params = (
                new_card_id,
                data.get('sub_type'),
                data.get('is_limited'),
                data.get('effect_text')
            )
            for tag_name in data.get('tags', []):
                # 確保標籤存在 (如果不存在就插入，存在就忽略)
                cursor.execute("INSERT IGNORE INTO tags (tag_name) VALUES (%s)", (tag_name,))
                # 查出該標籤 ID
                cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag_name,))
                tag_row = cursor.fetchone()
                if tag_row:
                    tag_id = tag_row[0]
                    #  建立關聯
                    cursor.execute("INSERT INTO card_tags (card_id, tag_id) VALUES (%s, %s)", (new_card_id, tag_id))
                    print(f"成功寫入 card_tags 表，Card ID: {tag_name}")
            debug_execute(sql_support, support_params, "support_cards")

        #  計算 sp_tags

        sp_tags_found = analyze_sp_tags(data)
        
        if sp_tags_found:
            print(f"  -> 自動偵測到 SP Tags: {sp_tags_found}")
            
            for slug in sp_tags_found:
                # 2. 查出 tag_id (假設 sp_tags 表已經有資料了)
                cursor.execute("SELECT id FROM sp_tags WHERE sp_tag_name = %s", (slug,))
                tag_row = cursor.fetchone()
                
                if tag_row:
                    tag_id = tag_row[0]
                    # 3. 建立關聯
                    cursor.execute("""
                        INSERT IGNORE INTO card_sp_tags (card_id, sp_tag_id) 
                        VALUES (%s, %s)
                    """, (new_card_id, tag_id))
                else:
                    print(f"  [警告] 資料庫中找不到 Tag 定義: {slug}，請先在 MySQL 中新增。")
        # -------------------------------------------------------
        # 提交變更 (Commit)
        # -------------------------------------------------------
        conn.commit()
        print(f"卡片 {data.get('number')} - {data.get('name')} 資料庫寫入完成！")

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
        conn.rollback() # 發生錯誤時，復原所有動作
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":  
    # 測試用：請換成一張實際的卡片詳細頁 URL
    '''test_url = "https://hololive-official-cardgame.com/cardlist/?id=358&%2Fcardlist%2Fcardsearch_ex=&expansion=hBP02&view=image"
    card_data = parse_card_page(test_url)
    if card_data:
        save_to_database(card_data)'''
    
    # 爬取整個 hBP02 列表頁面的所有卡片
    target_list_url = "https://hololive-official-cardgame.com/cardlist/cardsearch/?expansion=hBP02"
    # 取得該列表頁面的所有卡片詳細頁網址
    all_card_urls = get_card_links_from_list(target_list_url)
    for index, card_url in enumerate(all_card_urls):
        print(f"[{index+1}/{len(all_card_urls)}] ", end="") # 顯示進度 
        
        card_data = parse_card_page(card_url)
        
        if card_data:
            save_to_database(card_data)
        
        # 休息，怕被鎖 IP
        time.sleep(1.5) 
        
    print("=== 全數完成！收工！ ===")