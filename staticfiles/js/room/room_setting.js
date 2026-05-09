document.addEventListener("DOMContentLoaded", function(){
        //アイコンをクリックしたら編集できるようにする 
    document.querySelector(".room-icon").addEventListener("click", function () {
        document.querySelector(".edit-room-icon").click();
    });

    // 選択したアイコンをプレビューできるようにする
    const input = document.querySelector(".edit-room-icon");
    const preview = document.querySelector(".room-icon");


    try {
        input.addEventListener("change", (e) => {
        const file = e.target.files[0];

        if (!file) return;

        // MIMEタイプで判定
        if (!file.type.startsWith("image/")) {
                alert("画像ファイルを選択してください");
                input.value = ""; // リセット
                return;
            }

        // OKなら表示
        preview.src = URL.createObjectURL(file);
        });
    } catch (e) {
        // エラーを無視
    }

    // ハンバーガーメニューの開閉
    document.querySelector(".hamburger").addEventListener("click", () => {
    document.querySelector(".settings-sidebar").classList.toggle("active");
    });
})