// top_scroll.js
// スクロールアニメーション + ヘッダーshadow
// toppage.js（.road-outputアニメーション）は別ファイルのまま維持

document.addEventListener('DOMContentLoaded', function() {

    // ヘッダーのスクロール影
    window.addEventListener('scroll', function() {
        var header = document.querySelector('header');
        if (header) {
            if (window.scrollY > 20) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
    });

    // .fade-up のIntersectionObserver
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-up').forEach(function(el) {
        observer.observe(el);
    });

});
