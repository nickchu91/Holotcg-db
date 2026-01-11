const API_BASE_URL = 'http://127.0.0.1:8001';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    loadCards();
});

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
        const colorMap = { '黃': 'yellow', '紅': 'red', '藍': 'blue', '紫': 'purple', '綠': 'green', '白': 'white' };
        if (filters.colors.length > 0 && !filters.colors.includes('全部')) {
            filters.colors.forEach(c => {
                const mapped = colorMap[c.trim()];
                if (mapped) params.append('colors', mapped);
            });
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
        displayCards(data.data || data);
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
function displayCards(cards) {
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

    div.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.card_name}">` : '<div class="no-image">暫無圖片</div>'}
        </div>
        <div class="card-info">
            <div class="card-number">${card.card_number}</div>
            <div class="card-name">${card.card_name}</div>
            <div class="card-type">${card.card_type}</div>
            <div class="card-color">顏色: ${colorText}</div>
            <div class="card-rarity">稀有度: ${card.rarity}</div>
            ${card.bloom_level ? `<div class="bloom-level">綻放等級: ${card.bloom_level}</div>` : ''}
            ${card.hp ? `<div class="hp">HP: ${card.hp}</div>` : ''}
            ${card.life ? `<div class="life">生命值: ${card.life}</div>` : ''}
        </div>
    `;
    
    return div;
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

