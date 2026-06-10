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

    // 招待URLコピー
    const btnCopy = document.getElementById("btn-copy");
    if (btnCopy) {
        btnCopy.addEventListener("click", function() {
            const input = document.getElementById("invite-url-input");
            const btnText = document.getElementById("btn-copy-text");
            const url = input.value;

            function showCopied() {
                btnCopy.classList.add("copied");
                btnText.textContent = "コピーしました！";
                setTimeout(function() {
                    btnCopy.classList.remove("copied");
                    btnText.textContent = "コピー";
                }, 2000);
            }

            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(url).then(showCopied).catch(function() {
                    input.select();
                    document.execCommand("copy");
                    showCopied();
                });
            } else {
                input.select();
                input.setSelectionRange(0, 99999);
                document.execCommand("copy");
                showCopied();
            }
        });
    }

});
