document.addEventListener("DOMContentLoaded", function(){
    // 検索ボックスのクリア
    const crear_btn = document.getElementById("event-search-box-crear");
    const search_box = document.getElementById("event-search-box");

    crear_btn.addEventListener("click", function(){
        search_box.value = null
    })
})