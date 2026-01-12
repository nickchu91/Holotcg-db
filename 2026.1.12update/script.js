const API_BASE_URL = 'http://127.0.0.1:8001';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    loadCards();
    initializeFilterToggle();
});

// 初始化篩選面板的切換按鈕（收合/展開）
function initializeFilterToggle() {
    const filterPanel = document.querySelector('.filter-panel');
    const cardsArea = document.querySelector('.cards-display-area');
    let toggleBtn = document.getElementById('filter-toggle');
    if (!filterPanel || !cardsArea) return;

    // 若按鈕不存在則建立（保險）
    if (!toggleBtn) {
        toggleBtn = document.createElement('button');
        toggleBtn.id = 'filter-toggle';
        toggleBtn.setAttribute('aria-label', '切換篩選面板');
        document.body.appendChild(toggleBtn);
    }

    // 預設收合（使用者要求為按鈕顯示）
    filterPanel.classList.add('collapsed');
    cardsArea.classList.add('full');
    toggleBtn.textContent = '▶';

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const collapsed = filterPanel.classList.toggle('collapsed');
        if (collapsed) {
            // 面板收合：讓 cards 擴展
            cardsArea.classList.add('full');
            toggleBtn.textContent = '▶';
            toggleBtn.classList.remove('hidden');
        } else {
            // 面板展開：hide 按鈕以免擋住篩選欄
            cardsArea.classList.remove('full');
            toggleBtn.textContent = '◀';
            toggleBtn.classList.add('hidden');
        }
    });

    // 若點擊畫面其他處時，不做處理（避免誤關閉）
}

// 初始化篩選按鈕
function initializeFilters() {
    document.querySelectorAll('.filter-buttons').forEach(group => {
        const buttons = group.querySelectorAll('button');
        const selectAllButton = group.querySelector('.select-all');
        const otherButtons = Array.from(buttons).filter(btn => !btn.classList.contains('select-all'));

        // 點擊「全部」
        selectAllButton.addEventListener('click', () => {
            buttons.forEach(btn => btn.classList.remove('active'));
            selectAllButton.classList.add('active');
            loadCards();
        });

        // 點擊其他選項
        otherButtons.forEach(button => {
            button.addEventListener('click', () => {
                button.classList.toggle('active');
                selectAllButton.classList.remove('active');

                // 如果所有其他選項都亮，則只亮「全部」
                const allActive = otherButtons.every(btn => btn.classList.contains('active'));
                if (allActive) {
                    otherButtons.forEach(btn => btn.classList.remove('active'));
                    selectAllButton.classList.add('active');
                    loadCards();
                    return;
                }

                // 如果所有按鈕都沒亮，則只亮「全部」
                const noneActive = otherButtons.every(btn => !btn.classList.contains('active'));
                if (noneActive) {
                    selectAllButton.classList.add('active');
                    loadCards();
                } else {
                    loadCards();
                }
            });
        });
    });

    // 搜尋欄事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            loadCards();
        });
    }
}

// 從 API 獲取卡片數據
async function loadCards() {
    const searchInput = document.getElementById('search-input');
    const searchKeyword = searchInput ? searchInput.value : '';
    
    try {
        // 使用 URLSearchParams 以支援重複的查詢參數（FastAPI List 欄位）
        const params = new URLSearchParams();
        params.append('limit', '100');
        params.append('offset', '0');

        // 搜尋關鍵字對應到 card_name
        if (searchKeyword) {
            params.append('card_name', searchKeyword);
        }

        // 獲取選中的篩選條件
        const filters = getSelectedFilters();

        // 卡片類型 (重複參數 card_types=...)
        if (filters.cardTypes.length > 0 && !filters.cardTypes.includes('全部')) {
            filters.cardTypes.forEach(v => params.append('card_types', v));
        }

        // 顏色：把中文轉為 API 預期的英文欄位名稱
        // 注意：若選中"無"，不傳其他顏色給後端，在前端篩選
        const colorMap = { '黃': 'yellow', '紅': 'red', '藍': 'blue', '紫': 'purple', '綠': 'green', '白': 'white' };
        if (filters.colors.length > 0 && !filters.colors.includes('全部')) {
            // 若選中了"無"，則所有顏色篩選在前端進行
            if (!filters.colors.includes('無')) {
                filters.colors.forEach(c => {
                    const mapped = colorMap[c.trim()];
                    if (mapped) params.append('colors', mapped);
                });
            }
        }

        // 綻放等級
        if (filters.bloomLevels.length > 0 && !filters.bloomLevels.includes('全部')) {
            filters.bloomLevels.forEach(v => params.append('bloom_levels', v));
        }

        const url = `${API_BASE_URL}/api/cards?` + params.toString();
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API 錯誤: ${response.status}`);
        }

        const data = await response.json();
        displayCards(data.data || data, filters.colors);
    } catch (error) {
        console.error('載入卡片失敗:', error);
        showError('無法載入卡片，請檢查 API 連線');
    }
}

// 獲取選中的篩選條件
function getSelectedFilters() {
    const filters = {
        cardTypes: [],
        colors: [],
        bloomLevels: [],
        effects: [],
        tokkou: []
    };

    const sections = document.querySelectorAll('.filter-section');
    sections.forEach(section => {
        const h3 = section.querySelector('h3')?.textContent;
        const activeButtons = section.querySelectorAll('.filter-buttons button.active');
        
        const values = Array.from(activeButtons).map(btn => btn.textContent);

        if (h3 === '卡片類型') {
            filters.cardTypes = values;
        } else if (h3 === '顏色') {
            filters.colors = values;
        } else if (h3 === '綻放等級') {
            filters.bloomLevels = values;
        } else if (h3 === '效果') {
            filters.effects = values;
        } else if (h3 === '特攻') {
            filters.tokkou = values;
        }
    });

    return filters;
}

// 顯示卡片
function displayCards(cards, selectedColors) {
    let cardsContainer = document.getElementById('cards-container');
    
    // 如果容器不存在，則創建
    if (!cardsContainer) {
        cardsContainer = document.createElement('div');
        cardsContainer.id = 'cards-container';
        cardsContainer.className = 'cards-grid';
        document.body.appendChild(cardsContainer);
    }

    // 清空容器
    cardsContainer.innerHTML = '';

    // 如果沒有卡片
    if (!cards || cards.length === 0) {
        cardsContainer.innerHTML = '<p class="no-results">沒有找到符合條件的卡片</p>';
        return;
    }

    // 前端篩選顏色：若選中了"無"或其他顏色，進行前端過濾
    if (selectedColors && selectedColors.length > 0 && !selectedColors.includes('全部')) {
        const colorMap = { '黃': 'is_yellow', '紅': 'is_red', '藍': 'is_blue', '紫': 'is_purple', '綠': 'is_green', '白': 'is_white' };
        const hasNone = selectedColors.includes('無');
        const otherColors = selectedColors.filter(c => c !== '無');
        
        cards = cards.filter(card => {
            const hasNoColor = !card.is_red && !card.is_blue && !card.is_green && 
                              !card.is_yellow && !card.is_purple && !card.is_white;
            
            // 若選中"無"，無色卡片符合
            if (hasNone && hasNoColor) return true;
            
            // 若選中其他顏色，檢查是否符合
            if (otherColors.length > 0) {
                return otherColors.some(c => {
                    const field = colorMap[c.trim()];
                    return field && card[field];
                });
            }
            
            return false;
        });
    }

    // 顯示卡片
    cards.forEach(card => {
        const cardElement = createCardElement(card);
        cardsContainer.appendChild(cardElement);
    });
}

// 創建單張卡片元素
function createCardElement(card) {
    const div = document.createElement('div');
    div.className = 'card-item';
    
    // 構建顏色標籤
    const colors = [];
    if (card.is_red) colors.push('紅');
    if (card.is_blue) colors.push('藍');
    if (card.is_green) colors.push('綠');
    if (card.is_yellow) colors.push('黃');
    if (card.is_purple) colors.push('紫');
    if (card.is_white) colors.push('白');

    const colorText = colors.length > 0 ? colors.join(', ') : '無';

    // 嘗試取得可能的日文欄位（若無則為空字串）
    const jpText = card.japanese_name || card.jp_name || card.card_name_jp || card.original_name || card.card_original_name || '';

    // 卡片資訊預設隱藏，點擊圖片或 placeholder 時會切換顯示
    div.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.card_name}">` : '<div class="no-image">暫無圖片</div>'}
        </div>
        <div class="card-info" style="display:none">
            <div class="card-number">${card.card_number}</div>
            <div class="card-name">${card.card_name}</div>
            <div class="card-type">${card.card_type}</div>
            <div class="card-color">顏色: ${colorText}</div>
            <div class="card-rarity">稀有度: ${card.rarity}</div>
            ${card.bloom_level ? `<div class="bloom-level">綻放等級: ${card.bloom_level}</div>` : ''}
            ${card.hp ? `<div class="hp">HP: ${card.hp}</div>` : ''}
            ${card.life ? `<div class="life">生命值: ${card.life}</div>` : ''}
            ${jpText ? `<button class="show-jp-btn">顯示日文</button><div class="jpn-caption" style="display:none">${jpText}</div>` : ''}
        </div>
    `;

    // 點擊圖片會在頂層打開浮層（overlay），避免 Grid 產生空白格
    const imageContainer = div.querySelector('.card-image');
    const infoContainer = div.querySelector('.card-info');
    if (imageContainer) {
        imageContainer.style.cursor = 'pointer';
        imageContainer.addEventListener('click', (e) => {
            e.stopPropagation();
            // 關閉其他 overlay
            closeCardOverlay();
            openCardOverlay(card, div);
        });
    }

    // 綁定切換事件（若有日文欄位）
    if (jpText) {
        const btn = div.querySelector('.show-jp-btn');
        const caption = div.querySelector('.jpn-caption');
        if (btn && caption) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isHidden = caption.style.display === 'none' || caption.style.display === '';
                caption.style.display = isHidden ? 'block' : 'none';
                btn.textContent = isHidden ? '隱藏日文' : '顯示日文';
            });
        }
    }

    return div;
}

// Overlay handling: create a floating card overlay to avoid changing grid layout
function openCardOverlay(card, sourceDiv) {
    // 如果已存在，先關閉
    closeCardOverlay();

    // 建立遮罩
    const overlay = document.createElement('div');
    overlay.className = 'card-overlay';

    // 構建 overlay 內容（放大顯示）
    const jpText = card.japanese_name || card.jp_name || card.card_name_jp || card.original_name || card.card_original_name || '';
    const colors = [];
    if (card.is_red) colors.push('紅');
    if (card.is_blue) colors.push('藍');
    if (card.is_green) colors.push('綠');
    if (card.is_yellow) colors.push('黃');
    if (card.is_purple) colors.push('紫');
    if (card.is_white) colors.push('白');
    const colorText = colors.length > 0 ? colors.join(', ') : '無';

    overlay.innerHTML = `
        <div class="overlay-backdrop"></div>
        <div class="overlay-card">
            <button class="overlay-close">✕</button>
            <div class="overlay-image">${card.image_url ? `<img src="${card.image_url}" alt="${card.card_name}">` : '<div class="no-image">暫無圖片</div>'}</div>
            <div class="overlay-info">
                <div class="card-number">${card.card_number}</div>
                <div class="card-name">${card.card_name}</div>
                <div class="card-type">${card.card_type}</div>
                <div class="card-color">顏色: ${colorText}</div>
                <div class="card-rarity">稀有度: ${card.rarity}</div>
                ${card.bloom_level ? `<div class="bloom-level">綻放等級: ${card.bloom_level}</div>` : ''}
                ${card.hp ? `<div class="hp">HP: ${card.hp}</div>` : ''}
                ${card.life ? `<div class="life">生命值: ${card.life}</div>` : ''}
                ${jpText ? `<div class="jpn-caption">${jpText}</div>` : ''}
            </div>
        </div>
    `;

    // 點擊 backdrop 或 close 關閉 overlay
    overlay.querySelector('.overlay-backdrop').addEventListener('click', closeCardOverlay);
    overlay.querySelector('.overlay-close').addEventListener('click', closeCardOverlay);

    document.body.appendChild(overlay);
    // 禁用背景滾動
    document.body.style.overflow = 'hidden';

    // Esc 鍵關閉
    overlay._escHandler = (e) => { if (e.key === 'Escape') closeCardOverlay(); };
    document.addEventListener('keydown', overlay._escHandler);

    // 小動畫：先縮放再放大
    requestAnimationFrame(() => {
        overlay.classList.add('visible');
    });
}

function closeCardOverlay() {
    const existing = document.querySelector('.card-overlay');
    if (!existing) return;
    // 移除 esc handler
    if (existing._escHandler) document.removeEventListener('keydown', existing._escHandler);
    existing.classList.remove('visible');
    // 還原滾動
    document.body.style.overflow = '';
    // 等待動畫再移除
    setTimeout(() => {
        if (existing.parentNode) existing.parentNode.removeChild(existing);
    }, 200);
}

// 顯示錯誤信息
function showError(message) {
    let errorContainer = document.getElementById('error-container');
    if (!errorContainer) {
        errorContainer = document.createElement('div');
        errorContainer.id = 'error-container';
        document.body.insertBefore(errorContainer, document.body.firstChild);
    }
    
    errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
    setTimeout(() => {
        errorContainer.innerHTML = '';
    }, 5000);
}

