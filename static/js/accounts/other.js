document.addEventListener('DOMContentLoaded', function() {
    //時間帯で変化する背景
    // static/js/bg_switch.js
    const hour = new Date().getHours();

    const backgrounds = {
    dawn:   "../../static/img/dayline_bg_dawn.svg",
    noon:   "../../static/img/dayline_bg_noon.svg",
    sunset: "../../static/img/dayline_bg_sunset.svg",
    night:  "../../static/img/dayline_bg_night.svg",
    };

    function getBg(h) {
    if (h >= 5  && h < 10) return backgrounds.dawn;
    if (h >= 10 && h < 17) return backgrounds.noon;
    if (h >= 17 && h < 20) return backgrounds.sunset;
    return backgrounds.night;
    }

    document.body.style.backgroundImage = `url("${getBg(hour)}")`;
    document.body.style.backgroundSize       = "cover";
    document.body.style.backgroundPosition   = "center";
    document.body.style.backgroundAttachment = "fixed";
    
    const signup_iputs = document.querySelectorAll(".signup-form-input");
    const signup_btn = document.getElementById("signup-btn")
    const password_1 = document.getElementById("password-1")
    const password_2 = document.getElementById("password-2")
    const regex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$/;
    const terms_of_use = document.getElementById("terms_of_use-check");

    let j_specified_length = false;
    let j_specified_character = false;
    let j_safety = false;
    let password_matched = false;
    let terms_of_use_btn = false; 

    function checkFrom(){
        if (j_specified_length && 
            j_specified_character &&
            j_safety &&
            password_matched &&
            terms_of_use_btn
        ){
            signup_btn.style.color = "white";
            signup_btn.disabled = false;
        }else{
            signup_btn.style.color = "rgba(255, 255, 255, 0.363)";
            signup_btn.disabled = true;
        }
    }
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
        terms_of_use.addEventListener("click", () => {
            if(terms_of_use.checked){
                terms_of_use_btn = true;
            }else{
                terms_of_use_btn = false;
            }
            checkFrom();
        });


});