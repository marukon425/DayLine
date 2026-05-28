document.addEventListener("DOMContentLoaded", function() {

    // ルームアイコンをクリックしたら画像選択を開く
    const roomIcon = document.querySelector(".room-icon");
    const editRoomIcon = document.querySelector(".edit-room-icon");

    if (roomIcon && editRoomIcon) {
        roomIcon.addEventListener("click", function() {
            editRoomIcon.click();
        });

        // 選択した画像をプレビュー
        editRoomIcon.addEventListener("change", function(e) {
            const file = e.target.files[0];
            if (!file) return;
            if (!file.type.startsWith("image/")) {
                alert("画像ファイルを選択してください");
                editRoomIcon.value = "";
                return;
            }
            roomIcon.src = URL.createObjectURL(file);
        });
    }

});
