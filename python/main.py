from fastapi import FastAPI, HTTPException
import mysql.connector
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Nickchu20020611',  
    'database': 'hololiveOfficialCardGame'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# 讓 React 知道每一張卡片會有哪些欄位
class CardSchema(BaseModel):
    id: int
    card_number: str
    name: str
    rarity: str
    card_type: str
    image_url: Optional[str] = None
    # 這裡可以之後慢慢補上 hp, colors, sp_tags 等欄位

# --- API 路線 (Routes) ---
@app.get("/")
def read_root():
    return {"message": "歡迎來到 Hololive TCG API 伺服器！"}

# 取得所有卡片 (支援簡單的分頁，避免一次撈幾千張炸掉)
@app.get("/api/cards", response_model=List[CardSchema])
def get_cards(limit: int = 20, offset: int = 0):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # dictionary=True 會讓結果變成字典格式
    
    try:
        # 簡單的查詢，之後可以加入 WHERE 條件來過濾
        query = "SELECT id, card_number, card_name as name, rarity, card_type, image_url FROM cards LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, offset))
        cards = cursor.fetchall()
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

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