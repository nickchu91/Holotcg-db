document.querySelectorAll('.filter-buttons').forEach(group => {
    const buttons = group.querySelectorAll('button');
    const selectAllButton = group.querySelector('.select-all');
    const otherButtons = Array.from(buttons).filter(btn => !btn.classList.contains('select-all'));

    // 點擊「全部」
    selectAllButton.addEventListener('click', () => {
        buttons.forEach(btn => btn.classList.remove('active'));
        selectAllButton.classList.add('active');
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
                return;
            }

            // 如果所有按鈕都沒亮，則只亮「全部」
            const noneActive = otherButtons.every(btn => !btn.classList.contains('active'));
            if (noneActive) {
                selectAllButton.classList.add('active');
            }
        });
    });
});

