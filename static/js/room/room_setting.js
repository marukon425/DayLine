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

    // メンバー権限フォーム: 非表示セクションの入力を無効化してからサブミット
    // PCテーブルとモバイルカードに同名selectが重複するため、
    // 非表示側をdisabledにして送信値の重複を防ぐ
    const memberCards = document.querySelector('.member-cards');
    const membersTable = document.querySelector('.members-table');
    if (memberCards && membersTable) {
        const memberForm = membersTable.closest('form');
        if (memberForm) {
            memberForm.addEventListener('submit', function() {
                const isMobile = window.innerWidth <= 640;
                if (isMobile) {
                    membersTable.querySelectorAll('select, input[name="member_id"]')
                        .forEach(function(el) { el.disabled = true; });
                } else {
                    memberCards.querySelectorAll('select, input[name="member_id"]')
                        .forEach(function(el) { el.disabled = true; });
                }
            });
        }
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
