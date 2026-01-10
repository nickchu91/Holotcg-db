from fastapi import FastAPI, HTTPException , Query
import mysql.connector
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",  # 前端常用的 Port
    "http://127.0.0.1:3000",
    "*"                       # 開發階段可以先設星號，允許所有來源 (上線要改掉)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],      # 允許 GET, POST, OPTIONS 等所有方法
    allow_headers=["*"],      # 允許所有 Header
)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Nickchu20020611',  
    'database': 'hololiveOfficialCardGame'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

class PaginatedCardResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[CardSchema]

class ArtSchema(BaseModel):
    art_name: str
    art_description: str
    art_damage: str
    cost_red: int = 0
    cost_blue: int = 0
    cost_green: int = 0
    cost_yellow: int = 0
    cost_purple: int = 0
    cost_white: int = 0
    cost_any: int = 0
    tokkou: Optional[str] = None
    tokkou_damage: Optional[int] = None
    tokkou: Optional[str] = None
    tokkou_damage: Optional[int] = None

class TagSchema(BaseModel):
    sp_tag_name: str      

# 讓 React 知道每一張卡片會有哪些欄位
class CardSchema(BaseModel):
    # 所有卡片一定都有的欄位
    id: int
    card_number: str
    card_name: str
    rarity: str
    card_type: str
    image_url: Optional[str] = None
    
    #顏色
    is_red: Optional[bool] = None
    is_blue: Optional[bool] = None
    is_green: Optional[bool] = None
    is_yellow: Optional[bool] = None
    is_purple: Optional[bool] = None
    is_white: Optional[bool] = None


    # 只有主推卡片才有的欄位 (預設為 None)
    life:Optional[int] = None
    oshi_skill_name: Optional[str] = None
    oshi_skill: Optional[str] = None
    oshi_skill_power_cost: Optional[str] = None
    sp_oshi_skill_name: Optional[str] = None
    sp_oshi_skill: Optional[str] = None
    sp_oshi_skill_power_cost: Optional[str] = None

    # 只有成員卡片才有的欄位 (預設為 None) 
    hp: Optional[int] = None
    bloom_level: Optional[str] = None
    baton_cost: Optional[int] = None
    extra_rule: Optional[str] = None
    bloom_effect_name: Optional[str] = None
    bloom_effect: Optional[str] = None
    gift_effect_name: Optional[str] = None
    gift_effect: Optional[str] = None
    collab_effect_name: Optional[str] = None
    collab_effect: Optional[str] = None

    #  藝能
    arts: List[ArtSchema] = []


    # 只有支援卡片才有的欄位 (預設為 None)
    support_card_type: Optional[str] = None
    effect: Optional[str] = None
    limited: Optional[bool] = None

    #  Tags 
    sp_tags: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# --- API 路線 (Routes) ---

# 取得所有 SP Tag 
@app.get("/api/options/sp_tags")
def get_sp_tag_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT sp_tag_name FROM sp_tags ORDER BY sp_tags.id ASC"
    cursor.execute(sql)
    return cursor.fetchall()

@app.get("/api/options/tags")
def get_tag_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT tag_name FROM tags ORDER BY tags.tag_name ASC"
    cursor.execute(sql)
    return [row['tag_name'] for row in cursor.fetchall()]

@app.get("/api/options/names")
def get_name_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT card_name FROM cards ORDER BY card_name") 
    return [row['card_name'] for row in cursor.fetchall()]



# 取得所有卡片 (支援簡單的分頁，避免一次撈幾千張炸掉)
@app.get("/api/cards", response_model=List[CardSchema])
def get_cards(
    
    card_name: List[str] = Query(None), 
    colors: List[str] = Query(None), 
    card_types: List[str] = Query(None), 
    bloom_levels: List[str] = Query(None), 
    sp_tags: List[str] = Query(None), 
    tags: List[str] = Query(None), 
    rarities: List[str] = Query(None),
    support_card_types: List[str] = Query(None), 

    limit: int = 20, 
    offset: int = 0
    
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    try:
        base_sql = """
        SELECT DISTINCT
            c.id, c.card_number, c.card_name, c.card_type, c.rarity, c.image_url,
            
            -- 顏色處理 (COALESCE: 誰有值就用誰的)
            COALESCE(o.is_red, h.is_red, ch.is_red) as is_red,
            COALESCE(o.is_blue, h.is_blue, ch.is_blue) as is_blue,
            COALESCE(o.is_green, h.is_green, ch.is_green) as is_green,
            COALESCE(o.is_yellow, h.is_yellow, ch.is_yellow) as is_yellow,
            COALESCE(o.is_purple, h.is_purple, ch.is_purple) as is_purple,
            COALESCE(o.is_white, h.is_white, ch.is_white) as is_white,
            
            -- Oshi 專用欄位
            o.life, o.oshi_skill_name, o.oshi_skill, o.oshi_skill_power_cost,
            o.sp_oshi_skill_name, o.sp_oshi_skill, o.sp_oshi_skill_power_cost,
            
            -- Holomem 專用欄位
            h.hp, h.bloom_level, h.baton_cost, h.extra_rule,
            h.bloom_effect_name, h.bloom_effect, h.gift_effect_name, h.gift_effect,
            h.collab_effect_name, h.collab_effect,
            
            -- Support 專用欄位
            s.support_card_type, s.effect, s.limited

        FROM cards c
        LEFT JOIN oshi_cards o ON c.id = o.card_id
        LEFT JOIN holomem_cards h ON c.id = h.card_id
        LEFT JOIN support_cards s ON c.id = s.card_id
        LEFT JOIN cheer_cards ch ON c.id = ch.card_id
        
        """

        joins = ""
        conditions = ["1=1"] # 預設條件，方便後面用 AND 串接
        params = []

        if card_name:
            # 產生 "c.card_name IN (%s, %s)"
            placeholders = ",".join(["%s"] * len(card_name))
            conditions.append(f"c.card_name IN ({placeholders})")
            params.extend(card_name)

        # 種類 (Card Type)
        if card_types:
            placeholders = ",".join(["%s"] * len(card_types))
            conditions.append(f"c.card_type IN ({placeholders})")
            params.extend(card_types)

        # 稀有度 (Rarity)
        if rarities:
            placeholders = ",".join(["%s"] * len(rarities))
            conditions.append(f"c.rarity IN ({placeholders})")
            params.extend(rarities)
            
        # 支援卡類型 (Support Type)
        if support_card_types:
            placeholders = ",".join(["%s"] * len(support_card_types))
            conditions.append(f"s.support_card_type IN ({placeholders})")
            params.extend(support_card_types)

        # 綻放等級 (Bloom Level)
        if bloom_levels:
            placeholders = ",".join(["%s"] * len(bloom_levels))
            conditions.append(f"h.bloom_level IN ({placeholders})")
            params.extend(bloom_levels)

        # --- B. 處理複雜欄位 (顏色) ---
        # 前端傳來: ['red', 'blue']
        # 目標 SQL: AND ( (COALESCE(...) = 1) OR (COALESCE(...) = 1) )
        if colors:
            color_clauses = []
            for color in colors:
                safe_color = color.lower()
                if safe_color in ['red', 'blue', 'green', 'yellow', 'purple', 'white']:
                    # 這裡的邏輯是: 檢查該顏色的 COALESCE 結果是否為 True (1)
                    # 注意: 這裡不能用 %s，因為我們要拼的是欄位名稱
                    col_check = f"COALESCE(o.is_{safe_color}, h.is_{safe_color}, ch.is_{safe_color}) = 1"
                    color_clauses.append(col_check)
            
            if color_clauses:
                # 用 OR 把不同顏色串起來 (例如: 紅色 OR 藍色 的卡我都接受)
                conditions.append(f"({' OR '.join(color_clauses)})")

        # --- C. 處理關聯表過濾 (Tags & SP Tags) ---
        # 策略: 只有當使用者要查 tag 時，我們才 JOIN 該表，避免無謂效能消耗
        
        # SP Tags
        if sp_tags:
            joins += " JOIN card_sp_tags cst ON c.id = cst.card_id JOIN sp_tags st ON cst.sp_tag_id = st.id"
            placeholders = ",".join(["%s"] * len(sp_tags))
            conditions.append(f"st.sp_tag_name IN ({placeholders})")
            params.extend(sp_tags)

        # Normal Tags
        if tags:
            joins += " JOIN card_tags ct ON c.id = ct.card_id JOIN tags t ON ct.tag_id = t.id"
            placeholders = ",".join(["%s"] * len(tags))
            conditions.append(f"t.tag_name IN ({placeholders})")
            params.extend(tags)

        # 3. 組合最終 SQL
        where_clause = " WHERE " + " AND ".join(conditions)
        final_sql = base_sql + joins + where_clause + " ORDER BY c.id ASC LIMIT %s OFFSET %s"
        
        # 加上分頁參數
        final_params = params + [limit, offset]
        
        # 執行查詢
        cursor.execute(final_sql, tuple(final_params))
        cards = cursor.fetchall()

        # 如果沒抓到卡片，直接回傳空陣列
        if not cards:
            return []

        # ==========================================
        #  第二階段：補完資料 (Python Stitching)
        #  這裡跟上一題完全一樣，負責把藝能跟Tag裝回去
        # ==========================================
        
        card_ids = [card['id'] for card in cards]
        ids_placeholder = ','.join(['%s'] * len(card_ids))

        # A. 抓藝能
        cursor.execute(f"SELECT * FROM card_arts WHERE card_id IN ({ids_placeholder})", card_ids)
        all_arts = cursor.fetchall()

        # B. 抓一般 Tags
        cursor.execute(f"""
            SELECT ct.card_id, t.tag_name 
            FROM card_tags ct JOIN tags t ON ct.tag_id = t.id 
            WHERE ct.card_id IN ({ids_placeholder})
        """, card_ids)
        all_tags = cursor.fetchall()

        # C. 抓 SP Tags
        cursor.execute(f"""
            SELECT cst.card_id, st.sp_tag_name 
            FROM card_sp_tags cst JOIN sp_tags st ON cst.sp_tag_id = st.id 
            WHERE cst.card_id IN ({ids_placeholder})
        """, card_ids)
        all_sp_tags = cursor.fetchall()

        # D. 組裝
        card_map = {card['id']: card for card in cards}
        for card in cards:
            card['arts'] = []
            card['tags'] = []
            card['sp_tags'] = []

        for art in all_arts:
            if art['card_id'] in card_map:
                card_map[art['card_id']]['arts'].append(art)

        for tag in all_tags:
            if tag['card_id'] in card_map:
                card_map[tag['card_id']]['tags'].append(tag['tag_name'])

        for sp_tag in all_sp_tags:
            if sp_tag['card_id'] in card_map:
                card_map[sp_tag['card_id']]['sp_tags'].append(sp_tag['sp_tag_name'])

        return cards

    except Exception as e:
        # 建議在開發階段把錯誤印出來，方便除錯
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
        



        '''
        # 簡單的查詢，之後可以加入 WHERE 條件來過濾
        query_sql = "SELECT DISTINCT c.* FROM cards c"
        #count_sql = "SELECT COUNT(DISTINCT c.id) as total FROM cards c" # 算總共有幾張卡
        joins = ""
        wheres = " WHERE 1=1"
        params = []

        # 處理過濾條件

        # card_name
        if card_name:
            name_conditions = ["c.card_name = %s" for _ in card_name] 
            wheres += " AND (" + " OR ".join(name_conditions) + ")"
            for n in card_name: params.append(n)

        # card_types
        if card_types:
            type_conditions = ["c.card_type = %s" for _ in card_types]
            wheres += " AND (" + " OR ".join(type_conditions) + ")"
            for t in card_types: params.append(t)

        # rarities
        if rarities:
            rarity_conditions = ["c.rarity = %s" for _ in rarities]
            wheres += " AND (" + " OR ".join(rarity_conditions) + ")"
            for r in rarities: params.append(r)

        

        

        # B. 再抓資料 (加上排序與分頁)
        final_sql = query_sql + joins + wheres + " ORDER BY c.card_number ASC LIMIT %s OFFSET %s"
        # params 加上 limit 和 offset
        cursor.execute(final_sql, tuple(params + [limit, offset]))
        return cursor.fetchall()

        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()'''

# 根據 ID 取得單張卡片詳情
@app.get("/api/cards/{card_id}")
def get_card_detail(card_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 這裡示範如何順便把 SP Tags 抓出來
        cursor.execute("SELECT * FROM cards WHERE id = %s", (card_id,))
        card = cursor.fetchone()
        
        if not card:
            raise HTTPException(status_code=404, detail="卡片找不到")
            
        # 額外查詢這張卡的 SP Tags
        sql_tags = """
            SELECT sp_tag_name 
            FROM sp_tags t
            JOIN card_sp_tags cst ON t.id = cst.sp_tag_id
            WHERE cst.card_id = %s
        """
        cursor.execute(sql_tags, (card_id,))
        sp_tags = cursor.fetchall()
        
        # 把 tags 塞進卡片資料裡
        card['sp_tags'] = sp_tags
        
        return card
    finally:
        cursor.close()
        conn.close()


#終端執行 http://127.0.0.1:8000/docs#/