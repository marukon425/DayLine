document.addEventListener("DOMContentLoaded", function(){
    //アイコンをクリックしたら編集できるようにする 
    document.querySelector(".profiele-icon-img").addEventListener("click", function () {
        console.log("クリック")
        document.querySelector(".edit-icon").click();
    });

    // 選択したアイコンをプレビューできるようにする
    const input = document.querySelector(".edit-icon");
    const preview = document.querySelector(".profiele-icon-img");

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
})


