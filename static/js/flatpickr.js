document.addEventListener("DOMContentLoaded", function(){
    flatpickr(".date-picker", {
        locale: "ja",
        // dateFormat: "Y年m月d日"
    });

    flatpickr(".time-picker", {
        enableTime: true,        // 時間選択を有効化
        noCalendar: true,       // カレンダーを非表示
        dateFormat: "H:i",      // 24時間表示 (例: 13:45)
        // dateFormatが"H:i"（24時間形式）なのにfalseだと、
        // 入力欄は24時間表示のままAM/PMセレクターが出て時刻がずれるのでtrueに合わせる
        time_24hr: true,
    });
});