document.addEventListener("DOMContentLoaded", function(){
    flatpickr(".date-picker", {
        locale: "ja",
        // dateFormat: "Y年m月d日"
    });

    flatpickr(".time-picker", {
        enableTime: true,        // 時間選択を有効化
        noCalendar: true,       // カレンダーを非表示
        dateFormat: "H:i",      // 24時間表示 (例: 13:45)
        time_24hr: false,        // 24時間表示にする
    });
});