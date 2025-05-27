document.querySelectorAll('.filter-buttons').forEach(group => {
    const buttons = group.querySelectorAll('button');
    const selectAllButton = group.querySelector('.select-all');

        // 處理「全部」按鈕
        selectAllButton.addEventListener('click', () => {
            const isSelectAllActive = selectAllButton.classList.contains('active');
            if (isSelectAllActive) {
                // 取消所有選中
                buttons.forEach(btn => btn.classList.remove('active'));
            } else {
                // 全部選中
                buttons.forEach(btn => btn.classList.add('active'));
            }
        });

        // 處理其他按鈕的多選
        buttons.forEach(button => {
            if (!button.classList.contains('select-all')) {
                button.addEventListener('click', () => {
                    button.classList.toggle('active'); // 切換選中狀態

                    // 檢查是否所有按鈕（除了「全部」）都被選中
                    const allSelected = Array.from(buttons)
                        .filter(btn => !btn.classList.contains('select-all'))
                        .every(btn => btn.classList.contains('active'));

                    // 如果所有按鈕都被選中，「全部」也高亮；否則取消高亮
                    if (allSelected) {
                        selectAllButton.classList.add('active');
                    } else {
                        selectAllButton.classList.remove('active');
                    }
                });
            }
        });
    })

