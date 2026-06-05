document.addEventListener('DOMContentLoaded', function() {
    const password_1 = document.getElementById("password-1") || document.getElementById("id_new_password1");
    const password_2 = document.getElementById("password-2") || document.getElementById("id_new_password2");
    const signup_btn = document.getElementById("signup-btn") || document.getElementById("login-btn");
    const terms_of_use = document.getElementById("terms_of_use-check");
    const regex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$/;

    let j_specified_length = false;
    let j_specified_character = false;
    let j_safety = false;
    let password_matched = false;
    let terms_of_use_btn = !terms_of_use;

    function checkFrom(){
        if (j_specified_length &&
            j_specified_character &&
            j_safety &&
            password_matched &&
            terms_of_use_btn
        ){
            if (signup_btn) {
                signup_btn.style.color = "white";
                signup_btn.disabled = false;
            }
        }else{
            if (signup_btn) {
                signup_btn.style.color = "rgba(255, 255, 255, 0.363)";
                signup_btn.disabled = true;
            }
        }
    }

    if (!password_1 || !password_2) return;

        // パスワードの安全性の条件
        password_1.addEventListener("input", () => {
            // パスワードの長さ
            if (password_1.value.length >= 8 && password_1.value.length <= 20){
                j_specified_length = true;
                document.querySelector("#specified_length img").src = CHECK_IMG ;
                document.querySelector("#specified_length span").style.color = "black";
            }else{
                document.querySelector("#specified_length img").src = UNCHECK_IMG;
                document.querySelector("#specified_length span").style.color = "#D9D9D9";
                j_specified_length = false;
            }
            // 半角英数字
            if (regex.test(password_1.value)) {
                document.querySelector("#specified_character img").src = CHECK_IMG;
                document.querySelector("#specified_character span").style.color = "black";
                j_specified_character = true;
            }else{
                document.querySelector("#specified_character img").src = UNCHECK_IMG;
                document.querySelector("#specified_character span").style.color = "#D9D9D9";
                j_specified_character = false;
            }
            if (j_specified_length && j_specified_character){
                document.querySelector("#safety img").src = CHECK_IMG;
                document.querySelector("#safety span").style.color = "black";
                j_safety = true;
            }else{
                document.querySelector("#safety img").src = UNCHECK_IMG;
                document.querySelector("#safety span").style.color = "#D9D9D9";
                j_safety = false;
            }
            // パスワードが一致してるか
            if (password_1.value == password_2.value && !password_1.value == ""){
                document.querySelector("#password_matched img").src = CHECK_IMG;
                document.querySelector("#password_matched span").style.color = "black";
                password_matched = true;
            }else{
                document.querySelector("#password_matched img").src = UNCHECK_IMG;
                document.querySelector("#password_matched span").style.color = "#D9D9D9";
                password_matched = false;
            }
            console.log(password_2.value)
            checkFrom();
        });
        password_2.addEventListener("input", () => {
            // パスワードが一致してるか
            if (password_1.value == password_2.value){
                document.querySelector("#password_matched img").src = CHECK_IMG;
                document.querySelector("#password_matched span").style.color = "black";
                password_matched = true;
            }else{
                document.querySelector("#password_matched img").src = UNCHECK_IMG;
                document.querySelector("#password_matched span").style.color = "#D9D9D9";
                password_matched = false;
            }
            checkFrom();
        });
        // 同意ボタン
        if (terms_of_use) {
            terms_of_use.addEventListener("click", () => {
                terms_of_use_btn = terms_of_use.checked;
                checkFrom();
            });
        }


});