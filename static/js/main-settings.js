document.addEventListener('DOMContentLoaded', function() {

    function test_console(moji){
        console.log('test:', moji);
    }

    // flatpickrの初期化
    
    const start_date_fp = flatpickr(".start-date", {
        locale: "ja",
        // dateFormat: "Y年m月d日"
    });
    const end_date_fp = flatpickr(".end-date", {
        locale: "ja",
        // dateFormat: "Y年m月d日"
    });

    flatpickr(".time-picker", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true,  // falseになってたのでついでに修正
    });
    // flatpickrインスタンスをセレクタから取得するヘルパー
    function getFp(selector) {
        return document.querySelector(selector)._flatpickr;
    }
    //  ↓ ------------- フルカレンダー --------------------------------↓
    var calendarEl = document.getElementById('calendar');
    // let user_events = {id:'user_event',url:'/index/json/userevent/', editable: true,}

    // ここの変数の中に設定を書く
    // クラス名が未定義状態になってるけどindex_globalで定義してる
    var calendar = new FullCalendar.Calendar(calendarEl, {
        // headerToolbar: {
        // left: 'prev,next today',
        // center: 'title',
        // right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth',
        // },
        locale: 'ja',
        headerToolbar: false,
        initialView: 'dayGridMonth',
        fixedWeekCount: false, // 次月の週を非表示にする
        navLinks: true, // can click day/week names to navigate views
        businessHours: true, // display business hours
        editable: true,
        handleWindowResize: true,
        selectable: true,
        initialDate: new Date(),
        firstDay: 1,  // ← 月曜日スタート
        eventSources: [
            {
                url: "/index/json/userevent/",
                editable: true,
            },
            {
                url: "/index/json/holidays/",
                editable: false,       // ドラッグ移動不可
                color: "#ff6b6b",
                textColor: "#ffffff",
            }
        ],
        contentHeight: 600,
        dayMaxEvents: true,
        handleWindowResize: true,
        longPressDelay: 100, // スマホ用

        eventDidMount: function(info) {
            // JSONのextendedPropsからroom_idを取得
            // FullCalendarは知らないプロパティを自動でextendedPropsに入れる
            const roomId = info.event.extendedProps.room_id;
            if (roomId) {
                // イベントのDOM要素にdata-room-idを付ける
                info.el.setAttribute('data-room-id', roomId);

                // 初期状態：チェックが外れてたら最初から非表示にする
                const checkbox = document.querySelector(`.calendar-visibility-check[data-room-id="${roomId}"]`);
                if (checkbox && !checkbox.checked) {
                    info.el.style.display = 'none';
                }
            }
        },

        dateClick: function(info){
        console.log(test_console("dateclick"))
        new Create.open();
        },

        // イベントをクリックしたとき
        // 
        eventClick: function(info) {
            // 祝日のイベントクリックを不可能にする
            if (info.event.source?.url === "/index/json/holidays/") return;

            // 以降は既存の処理
            info.jsEvent.stopPropagation()
            // イベントをクリックしたら閉じる処理が同時に起きるからクリックしたときに伝播を止める
            info.jsEvent.stopPropagation();
            // 詳細モーダルを展開する
            document.getElementById("detail-event-modal").classList.add("hidden");

            // actionに削除用のurlを設定する
            const deleteForm = document.getElementById("delete-event-form");
            deleteForm.action = `/index/event/${info.event.id}/delete/`;
            deleteForm.addEventListener("submit", function(e) {
                e.preventDefault(); // 一旦送信を止める
                if (confirm("このイベントを削除しますか？")) {
                    this.submit(); // OKなら送信
                }
            });
            // event/<int:pk>/delete/
            // 要素取得
            
            const title = document.getElementById("detail-title"); 
            const user = document.getElementById("detail-user"); 
            const start_date = document.getElementById("detail-start-date")
            const allday_start_date = document.getElementById("check-detail-start-date")
            const allday_start_year = document.getElementById("check-detail-start-year")
            const end_date = document.getElementById("detail-end-date") 
            const allday_end_date = document.getElementById("check-detail-end-date")
            const allday_end_year = document.getElementById("check-detail-end-year")            
            const start_time = document.getElementById("detail-start-time") 
            const end_time = document.getElementById("detail-end-time") 
            const repeat = document.querySelector("#detail-repeat p") 
            const event_url = document.querySelector("#detail-url p") 
            const locate = document.querySelector("#detail-locate p") 
            const memo = document.querySelector("#detail-memo p")

            // 基本情報
            title.textContent = info.event.title;
            // extendedProps から取得
            const props = info.event.extendedProps;

            function formatDate(dateStr){
                const [y, m, d] = dateStr.split('-');
                return `${Number(y)}年${Number(m)}月${Number(d)}日`;
            }
            function formatTime(TiemStr){
                const [h, n, s] = TiemStr.split(':');
                return `${Number(h)}時${Number(n)}分`;
            }
            user.textContent = props.user || "";
            start_date.textContent = formatDate(props.start_date);
            end_date.textContent = formatDate(props.end_date);
            start_time.textContent = formatTime(props.start_time);
            end_time.textContent = formatTime(props.end_time);
            allday_start_date.textContent = `${Number(props.start_date.slice(5, 7))}月${Number(props.start_date.slice(8, 10))}日`;
            allday_end_date.textContent = `${Number(props.end_date.slice(5, 7))}月${Number(props.end_date.slice(8, 10))}日`;
            allday_start_year.textContent = `${Number(props.start_date.slice(0, 4))}年`;
            allday_end_year.textContent = `${Number(props.end_date.slice(0, 4))}年`
            if(props.repeat=="繰り返しなし"){document.getElementById("detail-repeat").style.display="none"}else{document.getElementById("detail-repeat").style.display="flex"; repeat.textContent = props.repeat || "";}
            if(props.event_url==null){document.getElementById("detail-url").style.display="none"}else{document.getElementById("detail-url").style.display="flex"; event_url.textContent = props.event_url || "";}
            if(props.locate==null){document.getElementById("detail-locate").style.display="none"}else{document.getElementById("detail-locate").style.display="flex"; locate.textContent = props.locate || "";}
            if(props.memo==null){document.getElementById("detail-memo").style.display="none"}else{document.getElementById("detail-memo").style.display="flex"; memo.textContent = props.memo || "";}

            // タイトルの色を変える
            document.getElementById("detail-title").style.color = info.event.backgroundColor
            

            // まず全部表示に戻す
            document.querySelectorAll(".un-check-allday").forEach(e => {
                e.style.display = "";
            });
            document.querySelectorAll(".check-allday").forEach(e => {
                e.style.display = "";
            });

            // そのあと条件分岐
            if(info.event.allDay){
                document.querySelectorAll(".un-check-allday").forEach(e => {
                    e.style.display = "none";
                });
            }else{
                document.querySelectorAll(".check-allday").forEach(e => {
                    e.style.display = "none";
                });
            }
            // 現在クリックされているイベント情報を保持する変数に格納
            currentEvent = { id: info.event.id, props: props, event: info.event };

        },
        // 表示中のカレンダーの日付をセット
        datesSet: function() {
            document.getElementById('current-date').textContent =
            calendar.view.title;
        },
        // 日付セルをクリックしたときの挙動
        dateClick: function(info) {
            // 作成モーダルの呼び出し
            create_sidebar.open()
            // 日付をセット（start）
            getFp("#create-start-date input").setDate(info.dateStr, false);
            // end も同日にする（初期値）
            getFp("#create-end-date input").setDate(info.dateStr, false);
        },    
    });
    
    
    // ここ↓の中には何も書かない(反映させるだけの部品)
    calendar.render();

    // カレンダーをスワイプできるようにする
    let startX = 0;
    calendarEl.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
    }, { passive: true });

    calendarEl.addEventListener('touchend', (e) => {
        const diff = startX - e.changedTouches[0].clientX;
        if (Math.abs(diff) < 50) return; // 50px未満は誤操作扱い

        if (diff > 0) {
            calendar.next(); // 左スワイプ→次の月
        } else {
            calendar.prev(); // 右スワイプ→前の月
        }
    });

    // ===== カレンダーリスト 表示切替 =====
    document.querySelectorAll('.calendar-visibility-check').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const roomId = this.dataset.roomId;   // data-room-id の値を取得
            const isChecked = this.checked;

            // data-room-id が一致するイベント要素を全部切り替える
            document.querySelectorAll(`[data-room-id="${roomId}"]`).forEach(function(el) {
                // .calendar-list 要素自体は除外（あれもdata-room-id持ってるから）
                if (!el.classList.contains('calendar-list')) {
                    el.style.display = isChecked ? '' : 'none';
                }
            });

        });
    });
    // ===== カレンダーリスト 表示切替 ここまで =====

    // 詳細モーダルを閉じる
    document.addEventListener('click', function(e) {
        const modal = document.getElementById("detail-event-modal");
        // モーダル外をクリックor閉じるボタンを押したら閉じる
        if ((!e.target.closest('#detail-event-modal'))||(e.target.closest('#detail-close'))) {
            modal.classList.remove("hidden");
        }
    });
    
    // 今日へ
    document.getElementById('root-today').addEventListener('click', function () {
        calendar.today();
    });
    // 前へ
    document.getElementById('prev').addEventListener('click', function () {
        calendar.prev();
    })
    // 次へ
    document.getElementById('next').addEventListener('click', function () {
        calendar.next();
    })

    // 月表示
    document.getElementById("monthBtn").addEventListener("click", () => {
        calendar.changeView("dayGridMonth");
    });

    //週表示
    document.getElementById("weekBtn").addEventListener("click", () => {
        calendar.changeView("timeGridWeek");
    });



    // サイドバー(イベント作成)の開閉
    class Create_sidebar{
        constructor(){
            this.sidebar = document.getElementById("create-sidebar");
            this.open_btn = document.getElementById("create-sidebar-open");
            this.close_btn = document.querySelectorAll(".cancel-btn");
            this.allday_cehck = document.querySelectorAll(".event-allday");
            this.init();
        }
        
        open(actionUrl = "/index/event/create/") {
            this.sidebar.classList.add("active");
            calendar.updateSize();
            document.getElementById("create-event-field").style.display = ""
            document.querySelectorAll(".create-time").forEach(el => {
                el.style.display = "none";
            });
            const d = new Date();
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, "0");
            const date = String(d.getDate()).padStart(2, "0");
            const today = `${year}-${month}-${date}`;
            getFp("#create-start-date input").setDate(today, false);
            getFp("#create-end-date input").setDate(today, false);
            setTimeout(() => {
                calendar.updateSize();
            }, 300);
            document.getElementById("create-event-field").action = actionUrl;
        }
        close(){
            this.sidebar.classList.remove("active");
            calendar.updateSize();
            // formのactionをリセット（編集後に作成モードに戻す）
            document.getElementById("create-event-field").action = "";
            document.getElementById("create-event-field").reset();
            getFp("#create-start-date input").clear();
            getFp("#create-end-date input").clear();
            setTimeout(() => {
                calendar.updateSize();
            }, 300);
        }

    allday(){

        const alldays = document.querySelectorAll(".event-allday");

        alldays.forEach(cb => {

            const timeOptions = cb.closest(".time-options");

            const startTime = timeOptions.querySelector(".create-start .create-time");
            const endTime = timeOptions.querySelector(".create-end .create-time");

            if(cb.checked){
                startTime.style.display = "none";
                endTime.style.display = "none";
                console.log("チェック")
                console.log(startTime.style.display)
            }else{
                startTime.style.display = "";
                endTime.style.display = "";
                console.log("未チェック")
                console.log(startTime.style.display)
            }

        });

    }

        init(){
            /* 
            アロー関数(pythonのlamda)を使うことで
            thisがhtml要素のクラスを指すようにする
            メソッドを実行させるメソッド
            */
            this.open_btn.addEventListener("click", () => {
                this.open();
            });

            this.close_btn.forEach((e) => {
                e.addEventListener("click", () => this.close());
            });

            this.allday_cehck.forEach((e) => {
                e.addEventListener("change", () => this.allday());
            });
        }
    }
    // インスタンス化して使えるようにする
    const create_sidebar = new Create_sidebar();

    // aiチャットのサイドバー展開
    document.querySelector(".ai-function").addEventListener("click", function(e){
        document.querySelector(".ai-chat-wrapper").classList.add("active");
        document.querySelector(".ai-chat").classList.add("active");
        setTimeout(() => {
            calendar.updateSize();
        }, 300);
    })
    document.querySelector(".ai-chat-close-btn").addEventListener("click", function(e){
        document.querySelector(".ai-chat-wrapper").classList.remove("active");
        document.querySelector(".ai-chat").classList.remove("active");
        setTimeout(() => {
            calendar.updateSize();
        }, 300);
    })

    // -----------------作成時の時間オブジェクトの動き-----------------------

    const startInput = document.querySelector("#create-start-date input");
    const endInput   = document.querySelector("#create-end-date input");

    endInput.addEventListener("input", function() {
        const start = new Date(startInput.value);
        const end   = new Date(endInput.value);
        if (end < start) {
            getFp("#create-start-date input").setDate(endInput.value, false);
        }
    });
    
    startInput.addEventListener("input", function() {
        const start = new Date(startInput.value);
        const end   = new Date(endInput.value);
        if (end < start) {
            getFp("#create-end-date input").setDate(startInput.value, false);
        }
    });


    //---------------------------------------------------------------------

    // -------------- カスタムselelct -------------- 
    const selectedElements = document.querySelectorAll('.custom-select-selected');

    selectedElements.forEach(function(selectedEl) {
        selectedEl.addEventListener('click', function(event) {
        event.stopPropagation(); // 親のクリックイベントを止める

        // 操作対象を変数に入れる
        // カスタムセレクト全体
        const customSelect = selectedEl.closest('.custom-select');
        // カスタムセレクトの選択部
        const optionsEl = customSelect.querySelector('.custom-select-options');
        // カスタムセレクトの選択部を非表示にする変数を設定
        const isHidden = !optionsEl.classList.contains('is-open');

        // すべてのオプションを閉じる
        // カスタムセレクトの選択部(全部)を取得
        document.querySelectorAll('.custom-select-options').forEach(function(el) {
            // カスタムセレクトの選択部(全部を非表示にする)
            hideElement(el);
        });

        // カスタムセレクトの選択部が閉じてる→true 開いてる→false
        if (isHidden) {
            // カスタムセレクトの選択部を表示する
            showElement(optionsEl);
            // カスタムセレクトの選択部をはみ出さない位置に調整
            adjustListPosition(optionsEl);
        }
        });

    //選択処理と hidden input への反映
    const optionElements = document.querySelectorAll('.custom-select-option');

    optionElements.forEach(function(optionEl) {
        optionEl.addEventListener('click', function(event) {
        event.stopPropagation(); // クリック伝播を止める

        const customSelect = optionEl.closest('.custom-select');
        const selectedTextEl = customSelect.querySelector('.custom-select-selected');
        // 選択した値を取得
        const hiddenInput = customSelect.querySelector('input[name]');
        const optionsContainer = customSelect.querySelector('.custom-select-options');
        const value = optionEl.dataset.value;

        customSelect.querySelectorAll('.custom-select-option').forEach(function(el) {
            el.classList.remove('is-selected');
        });

        if (value) {
            optionEl.classList.add('is-selected');
        }

        selectedTextEl.textContent = optionEl.textContent;
        if (hiddenInput){
            hiddenInput.value = value;
            console.log("更新されたname:", hiddenInput.name, "value:", value);
        } 

        hideElement(optionsContainer);
        });
    });
    // 初期選択処理
    document.querySelectorAll('.custom-select').forEach(customSelect => {
        const defaultOption =
            customSelect.querySelector('.custom-select-option.is-selected');

        if (!defaultOption) return;

        const selectedTextEl =
            customSelect.querySelector('.custom-select-selected');
        const hiddenInput =
            customSelect.querySelector('.custom-select-value');

        selectedTextEl.textContent = defaultOption.textContent;
        if (hiddenInput) {
            hiddenInput.value = defaultOption.dataset.value;
        }
    });

    // 外側クリックで閉じる
    document.addEventListener('click', function() {
        document.querySelectorAll('.custom-select-options').forEach(function(el) {
        hideElement(el);
        });
    });

    // 表示位置の自動調整（スクロール・リサイズ対応）
    window.addEventListener('resize', handleAdjustAll);
    window.addEventListener('scroll', handleAdjustAll);

    function handleAdjustAll() {
        const optionLists = document.querySelectorAll('.custom-select-options');

        optionLists.forEach(function(optionEl) {
        if (optionEl.classList.contains('is-open')) {
            adjustListPosition(optionEl);
        }
        });
    }

    function adjustListPosition(element) {
        // 引数の親要素(カスタムセレクト)を取得
        const customSelect = element.closest('.custom-select');

        // 引数の親要素の高さを取得
        const customSelectHeight = customSelect.offsetHeight;

        // 開いたときの選択部の高さを取得
        const optionsHeight = element.offsetHeight;

        // 親要素の画面内の位置を取得(選択部の下端が画面のどこにあるか)
        const rect = customSelect.getBoundingClientRect();

        // ブラウザのウィンドウの高さを取得
        const windowHeight = window.innerHeight;

        // 余白を代入
        const margin = 5; // 余白（px）

        // 選択部の下に残ってるスペースを取得
        const spaceBelow = windowHeight - rect.bottom;

        // 画面下の余白を見て十分な幅があれば下に、なければ上に
        const top = spaceBelow >= optionsHeight + margin
        ? customSelectHeight + margin // 下に出せる
        : -(optionsHeight + margin); // 上に出す

        // cssに代入
        setStyles(element, {
        top: top + 'px'
        });
    }

    function setStyles(element, styles) {
        Object.keys(styles).forEach(function(key) {
        element.style[key] = styles[key];
        });
    }

    // 引数で指定した要素をdisplay:block(表示)する
    function showElement(element) {
        element.classList.add('is-open');
    }

    // 引数で指定した要素をdisplay:none(非表示にする)
    function hideElement(element) {
        element.classList.remove('is-open');
    }
    });
    // --------------------------------------------

    // -----------------モーダルの開閉--------------------------------
    // querySelectorAllは配列形式で渡される
    const modal = document.querySelectorAll(".modal");
    const openBtn = document.querySelectorAll(".open-modal");
    const closeBtn = document.querySelectorAll(".close-modal");

    /*forEachの使い方
    要素.forEach((配列要素, 配列番号) => {
        処理内容
        }})
    */
    // モーダルの開くボタンがクリックされたら
    openBtn.forEach((btn, index) => {
        btn.addEventListener("click", function(){
            modal[index].style.display = "block"
        })
    })

    closeBtn.forEach((btn, index) => {
        btn.addEventListener("click", function(){
            modal[index].style.display = "none"
        })
    })

    // 背景クリックで閉じる
    modal.forEach((modal) => {
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
        modal.style.display = "none";
        }
    });
    });
    // ---------------------------------------------------------------

    // -------------------------------メモの入力-----------------------------------
    // メモで入力された内容を移す
    // メモで入力された内容を移す
    const memo_form = document.querySelectorAll(".modal-texterea-form");
    const memo_output = document.getElementById("memo-output");

    memo_form.forEach((e) => {
        e.addEventListener("input", () => {

            if (e.value === "") {
                memo_output.textContent = "メモを入力";
                memo_output.style.color = "grey";
                console.log("未入力");
            } else {
                memo_output.textContent = e.value;
                memo_output.style.color = "";
                console.log("入力中");
            }

        });
    });
    
    
    // ---------------------------------------------------------------------------

    // ----------------------------イベント作成のキャンセル・保存ボタン---------------
    // キャンセルボタンの挙動
    const create_cancel = document.getElementById("create-cancel-btn")
    create_cancel.addEventListener("click", () => {
        document.getElementById("create-event-field").reset();
        document.getElementById("create-sidebar").classList.remove("active")
        document.querySelector(".create-other-option").style.display = "none";
        document.querySelector(".other-optuin-hidden").style.display="block";
    })

    // ---------------------------------------------------------------------------

    // ---------------------------- 左サイドバーの開閉 ----------------------------
    const hamburger = document.getElementById("hamburger");
    const left_sidebar = document.getElementById("right-sidebar");
    const left_sidebar_over = document.getElementById("right-sidebar-overlay");
    hamburger.addEventListener("click", () => {
        left_sidebar.classList.toggle("active");
        left_sidebar_over.classList.toggle("active");
        setTimeout(() => {
            calendar.updateSize();
        }, 300);
    })
    // ---------------------------------------------------------------------------------

    // ------------------------------プロフィールモーダルの展開---------------------
    const header_icon = document.querySelector(".header-icon-space");
    const index_profile = document.getElementById("index-profile");
    header_icon.addEventListener("click", function(e){
        console.log("テスト")
        e.stopPropagation();
        index_profile.style.display = "flex";
    });

    document.addEventListener('click', function(e) {
        // モーダル外をクリックor閉じるボタンを押したら閉じる
        if ((!e.target.closest('#index-profile'))) {
            index_profile.style.display = "none";
        }
    });

    // -------------------------------------------------------------------------




    // ----------------------- ユーザー情報の取得 ---------------------------------
    fetch("/index/json/userinfo/")
    .then(response => response.json())
    .then(data => {
            // リンクを貼り付ける
            // document.querySelector(".user-setting").href = `/accounts/account/${data[0].pk}/settings/`
        })
        .catch(error => {
            console.error(error);
        });
    // ---------------------------------------------------------------------------
    // 現在選択中のイベント情報（eventClickのたびに上書き）
    let currentEvent = null;

    // ここに移動
    document.querySelector("#detail-url p").addEventListener("click", function(){
        if (!currentEvent) return;
        if (confirm("次のページに移動しますか？")) {
            window.location.href = currentEvent.props.event_url;
        }
    })

    // 編集ボタン（detail-edit）のリスナーは1回だけ登録
    document.getElementById("detail-edit").addEventListener("click", function(e){
        if (!currentEvent) return;

        const { id, props, event } = currentEvent;

        // 詳細モーダルを閉じる
        document.getElementById("detail-event-modal").classList.remove("hidden");

        // 作成フォームのactionを編集用URLに差し替え
        document.getElementById("create-event-field").action = `/index/event/${id}/edit/`;

        // サイドバーを開く
        create_sidebar.open(`/index/event/${id}/edit/`);

        // フィールドに既存データを流し込む
        getFp("#create-start-date input").setDate(props.start_date, false);
        getFp("#create-end-date input").setDate(props.end_date, false);
        getFp("#create-start-time input").setDate(props.start_time, false);
        getFp("#create-end-time input").setDate(props.end_time, false);

        // タイトル
        document.querySelector("#id_title").value = event.title;

        // 終日
        const alldayCheck = document.querySelector(".event-allday");
        alldayCheck.checked = event.allDay;
        create_sidebar.allday();

        // 色のカスタムセレクト
        document.querySelectorAll(".custom-select-option").forEach((el) => {
            const hiddenInput = el.querySelector("input[type='hidden']");
            if (hiddenInput && hiddenInput.value == event.backgroundColor) {
                el.classList.add("is-selected");
                const customSelect = el.closest(".custom-select");
                customSelect.querySelector(".custom-select-selected").textContent = el.textContent.trim();
                customSelect.querySelector(".custom-select-value").value = el.dataset.value;
            }
        });

        // url
        if(props.event_url){
            document.querySelector("#id_url").value = props.event_url;
        }
        // 場所
        if(props.locate){
            document.querySelector("#id_location").value = props.locate;
        }
        // メモ
        if(props.memo){
            document.querySelector("#id_memo").value = props.memo;
        }
    });

    const sidebar = document.querySelector(".sidebar");

    function toggleSidebar(){
        sidebar.classList.toggle("closed");
    }

    // aiチャット機能のtextareの伸縮
    document.querySelectorAll('.chat-input-textarea').forEach(el => {
    const dummy = el.querySelector('.chat-input-textarea-dummy');
    const textarea = el.querySelector('.chat-input-textarea-textarea');

    textarea.addEventListener('input', () => {
        dummy.textContent = textarea.value + '\u200b';
    });
    });




// -----------------------------------------------
// チャット機能のJS
// -----------------------------------------------

// 会話履歴を配列で管理する（AIに文脈を理解させるために毎回サーバーに送る）
let chatHistory = [];

// -----------------------------------------------
// イベントリスナーの登録
// -----------------------------------------------

// 送信ボタンをクリックしたら sendMessage() を呼ぶ
document.querySelector('.chat-input-textarea button').addEventListener('click', sendMessage);

// テキストエリアで Enter を押したら送信（Shift+Enter は改行）
document.querySelector('.chat-input-textarea-textarea')
    .addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // デフォルトの改行動作をキャンセル
            sendMessage();
        }
    });
    // ☆クロード☆
    // -----------------------------------------------
    // メッセージ送信処理
    // -----------------------------------------------
    // ユーザーのメッセージを送信する関数
    // async:非同期の処理
    async function sendMessage() {

        // チャットのテキストエリアを変数に
        const textarea = document.querySelector('.chat-input-textarea-textarea');
        const userText = textarea.value.trim(); // 前後の空白を除去

        // 何も入力されていなければ何もしない
        if (!userText) return;

        // ユーザーのメッセージをチャット画面に表示
        appendMessage('user', userText);

        // テキストエリアを空にする
        textarea.value = '';

        // 会話履歴に追加（次回のリクエスト時にサーバーに送る）
        chatHistory.push({ role: 'user', content: userText });

        // 「入力中...」のローディングメッセージを表示しておく
        // 後で内容を書き換えるために変数に入れておく
        const loadingEl = appendMessage('ai', '入力中...');
        try {
            // -----------------------------------------------
            // サーバー（Django）にPOSTリクエストを送る
            // -----------------------------------------------
            const res = await fetch('/index/ai/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // CSRFトークン → Djangoのセキュリティ機能。POSTには必須
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: userText,
                    // 直近10件の履歴だけ送る（多すぎるとAPIのコストが増えるため）
                    history: chatHistory.slice(-10)
                })
            });
            console.log("抽出中")
    
            // レスポンスのJSONを取り出す
            const data = await res.json();
    
            // -----------------------------------------------
            // AIの返答をチャットに表示する
            // -----------------------------------------------
            // <action>...</action> タグはユーザーに見せる必要がないので除去する
            const displayText = data.reply
                .replace(/<action>[\s\S]*?<\/action>/g, '')
                .trim();
    
            // 「入力中...」を実際の返答テキストに書き換える
            loadingEl.querySelector('p').textContent = displayText;
    
            // AIの返答も会話履歴に追加する（roleは "assistant"）
            chatHistory.push({ role: 'assistant', content: data.reply });
    
            // -----------------------------------------------
            // DB操作があった場合の処理
            // -----------------------------------------------
            if (data.action_result) {
                // 「✅ 予定を作成しました」などの結果メッセージを表示
                appendMessage('ai', data.action_result);
    
                // FullCalendarのイベントを再取得してカレンダーを更新する
                // ※ calendar変数はFullCalendarを初期化した変数名に合わせること
                calendar.refetchEvents();
            }

        } catch (e) {
            // 通信エラーなどが起きた場合
            loadingEl.querySelector('p').textContent = 'エラーが発生しました';
        }
    }


    // -----------------------------------------------
    // チャットにメッセージを追加する関数
    // -----------------------------------------------
    function appendMessage(role, text) {

        // チャットエリアのDOM要素を取得
        const chatArea = document.querySelector('.ai-chat-chat');

        // メッセージのdiv要素を作成
        const div = document.createElement('div');

        // role に応じてCSSクラスを切り替える
        // 'ai'   → AIのメッセージ（左寄せなど）
        // 'user' → ユーザーのメッセージ（右寄せなど）
        div.className = role === 'ai'
            ? 'chat-for-ai ai-chat-chat'
            : 'chat-for-user ai-chat-chat';

        // テキストをpタグで表示
        div.innerHTML = `<p>${text}</p>`;

        // チャットエリアの末尾に追加
        chatArea.appendChild(div);

        // 自動スクロール（最新メッセージが見えるように下にスクロール）
        chatArea.scrollTop = chatArea.scrollHeight;

        // ローディング表示を後で書き換えられるように要素を返す
        return div;
    }


    // -----------------------------------------------
    // Cookieの値を取得する関数（CSRFトークン取得に使う）
    // -----------------------------------------------
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        // Cookieの文字列から指定した名前の値を探して返す
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    // オプションを表示
    document.querySelector(".other-optuin-hidden").addEventListener("click", function(){
        document.querySelector(".create-other-option").style.display = "block";
        document.querySelector(".other-optuin-hidden").style.display="none";
    });

    // セレクトの選択肢を生成
    const jumpYear  = document.getElementById("jump-year");
    const jumpMonth = document.getElementById("jump-month");
    const dropdown  = document.getElementById("date-jump-dropdown");

    const thisYear = new Date().getFullYear();
    for (let y = thisYear - 5; y <= thisYear + 5; y++) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y + "年";
        jumpYear.appendChild(opt);
    }
    for (let m = 1; m <= 12; m++) {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m + "月";
        jumpMonth.appendChild(opt);
    }

    // セレクトをカレンダーの現在日付に同期
    function syncJumpSelect() {
        const d = calendar.getDate();
        jumpYear.value  = d.getFullYear();
        jumpMonth.value = d.getMonth() + 1;
    }
    syncJumpSelect();

    // current-dateクリックでドロップダウン開閉
    document.getElementById("current-date").addEventListener("click", function(e) {
        e.stopPropagation();
        syncJumpSelect();
        dropdown.style.display = dropdown.style.display === "none" ? "flex" : "none";
    });

    dropdown.addEventListener("click", function(e) {
        e.stopPropagation();
    });
    // 外クリックで閉じる
        document.addEventListener("click", function() {
            dropdown.style.display = "none";
        });

    // セレクト変更でジャンプ
    jumpYear.addEventListener("change", () => {
        calendar.gotoDate(new Date(jumpYear.value, jumpMonth.value - 1, 1));
    });
    jumpMonth.addEventListener("change", () => {
        calendar.gotoDate(new Date(jumpYear.value, jumpMonth.value - 1, 1));
    });

    // prev/next/todayと同期
    document.getElementById("prev").addEventListener("click", syncJumpSelect);
    document.getElementById("next").addEventListener("click", syncJumpSelect);
    document.getElementById("root-today").addEventListener("click", syncJumpSelect);

    // ===== メモ詳細モーダル =====
    (function() {
        const detailMemo  = document.getElementById("detail-memo");
        const overlay     = document.getElementById("memo-detail-overlay");
        const closeBtn    = document.getElementById("memo-detail-close");
        const contentArea = document.getElementById("memo-detail-content");

        detailMemo.addEventListener("click", function(e) {
            e.stopPropagation();
            contentArea.textContent = detailMemo.querySelector("p").textContent;
            overlay.classList.add("active");
        });
        closeBtn.addEventListener("click", () => overlay.classList.remove("active"));
        document.addEventListener("click", () => overlay.classList.remove("active"));
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") overlay.classList.remove("active");
        });
    })();
});