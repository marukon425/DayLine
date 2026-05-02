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
        // navLinksを無効にする（デフォルトの日クリック遷移を防ぐ）
        navLinks: false,

        

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
        
        // 日付セルをクリックしたときの挙動
        dateClick: function(info) {
            // クリックした日付をローカルタイムで "YYYY-MM-DD" 形式に変換
            const [y, m, d] = info.dateStr.split("-");
            const clickedDate = info.dateStr;

            // カレンダーの全イベントから「クリックした日に該当するもの」だけ抽出
            const events = calendar.getEvents().filter(event => {
                // 祝日は除外
                if (event.source?.url === "/index/json/holidays/") return false;

                const start = new Date(event.startStr.slice(0, 10));
                const endStr = event.endStr ? event.endStr.slice(0, 10) : event.startStr.slice(0, 10);
                const end = new Date(endStr);
                const clicked = new Date(clickedDate);

                // start以上 end未満 → 複数日またがるイベントも正しく判定できる
                return clicked >= start && clicked < end;
            });

            // モーダルのタイトルを "YYYY年MM月DD日（曜日）" 形式で表示
            const weekdays = ["日", "月", "火", "水", "木", "金", "土"];
            const dateObj = new Date(clickedDate);
            const week = weekdays[dateObj.getDay()];
            document.getElementById("day-modal-title").textContent = `${Number(y)}年${Number(m)}月${Number(d)}日（${week}）`;

            // イベントリストの描画エリアをリセット
            const listEl = document.getElementById("day-modal-list");
            listEl.innerHTML = "";

            if (events.length === 0) {
                // 予定がない場合
                listEl.innerHTML = '<p class="day-modal-empty">予定なし</p>';
            } else {
                // 開始時刻の早い順にソート
                events.sort((a, b) => new Date(a.startStr) - new Date(b.startStr));

                events.forEach(event => {
                    const item = document.createElement("div");
                    item.className = "day-modal-item";

                    // 終日イベントは "終日"、時間指定イベントは "HH:MM" を表示
                    const timeStr = event.allDay ? "終日" : event.startStr.slice(11, 16);

                    // イベントの色を取得（未設定ならデフォルトのブルー）
                    const color = event.backgroundColor || "#4285f4";

                    item.innerHTML = `
                        <span class="day-modal-dot" style="background:${color}"></span>
                        <span class="day-modal-time">${timeStr}</span>
                        <span class="day-modal-name">${event.title}</span>
                    `;

                    // リストのアイテムをクリック → モーダルを閉じて詳細モーダルを開く
                    item.addEventListener("click", () => {
                        closeDayEventsModal();
                        openDetailModal(event);
                    });

                    listEl.appendChild(item);
                });
            }

            // オーバーレイに active クラスを付けてモーダルを表示
            document.getElementById("day-events-overlay").classList.add("active");
        },

        // イベントをクリックしたとき
        eventClick: function(info) {
            // 祝日は無効化
            if (info.event.source?.url === "/index/json/holidays/") return;
            info.jsEvent.stopPropagation();
            openDetailModal(info.event);  // ← 関数呼ぶだけ
        },
        // 表示中のカレンダーの日付をセット
        datesSet: function() {
            document.getElementById('current-date').textContent =
            calendar.view.title;
        },

    });
    
    
    // ここ↓の中には何も書かない(反映させるだけの部品)
    calendar.render();

    //詳細モーダルのメソッド
    function openDetailModal(event) {
        // 詳細モーダルを展開する
        document.getElementById("detail-event-modal").classList.add("hidden");

        // actionに削除用のurlを設定する
        const deleteForm = document.getElementById("delete-event-form");
        deleteForm.action = `/index/event/${event.id}/delete/`;
        deleteForm.addEventListener("submit", function(e) {
            e.preventDefault(); // 一旦送信を止める
            if (confirm("このイベントを削除しますか？")) {
                this.submit(); // OKなら送信
            }
        });

        // 要素取得
        const title = document.getElementById("detail-title"); 
        const user = document.getElementById("detail-user"); 
        const start_date = document.getElementById("detail-start-date");
        const allday_start_date = document.getElementById("check-detail-start-date");
        const allday_start_year = document.getElementById("check-detail-start-year");
        const end_date = document.getElementById("detail-end-date"); 
        const allday_end_date = document.getElementById("check-detail-end-date");
        const allday_end_year = document.getElementById("check-detail-end-year");
        const start_time = document.getElementById("detail-start-time"); 
        const end_time = document.getElementById("detail-end-time"); 
        const repeat = document.querySelector("#detail-repeat p"); 
        const event_url = document.querySelector("#detail-url p"); 
        const locate = document.querySelector("#detail-locate p"); 
        const memo = document.querySelector("#detail-memo p");

        // 基本情報（info.event → event に統一）
        title.textContent = event.title;
        // extendedProps から取得
        const props = event.extendedProps;
        const id = event.id;

        function formatDate(dateStr){
            const [y, m, d] = dateStr.split('-');
            return `${Number(y)}年${Number(m)}月${Number(d)}日`;
        }
        function formatTime(timeStr){
            const [h, n, s] = timeStr.split(':');
            return `${Number(h)}時${Number(n)}分`;
        }

        user.textContent = props.user || "";
        start_date.textContent = formatDate(props.start_date);
        const endDateObj = new Date(props.end_date);
        endDateObj.setDate(endDateObj.getDate() - 1);
        const ey = endDateObj.getFullYear();
        const em = endDateObj.getMonth() + 1;
        const ed = endDateObj.getDate();
        end_date.textContent = formatDate(`${ey}-${String(em).padStart(2,'0')}-${String(ed).padStart(2,'0')}`);
        start_time.textContent = formatTime(props.start_time);
        end_time.textContent = formatTime(props.end_time);
        allday_start_date.textContent = `${Number(props.start_date.slice(5, 7))}月${Number(props.start_date.slice(8, 10))}日`;
        allday_end_date.textContent = `${em}月${ed}日`;
        allday_start_year.textContent = `${Number(props.start_date.slice(0, 4))}年`;
        allday_end_year.textContent = `${Number(props.end_date.slice(0, 4))}年`;

        if(props.repeat=="繰り返しなし"){document.getElementById("detail-repeat").style.display="none";}else{document.getElementById("detail-repeat").style.display="flex"; repeat.textContent = props.repeat || "";}
        if(props.event_url==null){document.getElementById("detail-url").style.display="none";}else{document.getElementById("detail-url").style.display="flex"; event_url.textContent = props.event_url || "";}
        if(props.locate==null){document.getElementById("detail-locate").style.display="none";}else{document.getElementById("detail-locate").style.display="flex"; locate.textContent = props.locate || "";}
        if(props.memo==null){document.getElementById("detail-memo").style.display="none";}else{document.getElementById("detail-memo").style.display="flex"; memo.textContent = props.memo || "";}

        // タイトルの色を変える
        document.getElementById("detail-title").style.color = event.backgroundColor;

        // まず全部表示に戻す
        document.querySelectorAll(".un-check-allday").forEach(e => { e.style.display = ""; });
        document.querySelectorAll(".check-allday").forEach(e => { e.style.display = ""; });

        // そのあと条件分岐
        if(event.allDay){
            document.querySelectorAll(".un-check-allday").forEach(e => { e.style.display = "none"; });
        }else{
            document.querySelectorAll(".check-allday").forEach(e => { e.style.display = "none"; });
        }

        // 現在クリックされているイベント情報を保持する変数に格納
        currentEvent = { id: event.id, props: props, fcEvent: event };

        // todoを拾う
        fetch(`/index/json/todo/list/${id}/`)  // DjangoのURL
        .then(response => {
            if (!response.ok) throw new Error('通信失敗');
            return response.json();
        })
        .then(data => {
            // todoがあるか確認
            if (data.length == 0){
                document.getElementById("detail-todo").style.display = "none";
            }else{
                document.getElementById("detail-todo").style.display = "flex";
            }
            const incomplete = document.querySelector(".incomplete");
            const completed = document.querySelector(".completed");

            // カウント更新関数
            function updateCount() {
                let checked = document.querySelectorAll(".todo-detail-content .todo-check:checked").length;
                document.querySelectorAll(".task-on").forEach(e => { e.textContent = checked; });
            }

            // イベントリスナーの登録を関数にまとめる
            function attachTodoEvents(div) {
                // todoの削除
                div.querySelector(".todo-delete button").addEventListener("click", function() {
                    const todoId = this.dataset.id;
                    fetch(`/index/json/todo/delete/${todoId}/`, {
                        method: 'POST',
                        headers: {
                            // djangoのセキュリティのために必要
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 成功したらDOMから削除
                        if(data.success) {
                            div.remove();
                            updateCount();
                        }
                    })
                    .catch(error => console.error('エラー:', error));
                });

                // todoのチェックボックスの切り替え
                div.querySelector(".todo-check").addEventListener("change", function() {
                    const todoId = this.dataset.id;
                    fetch(`/index/json/todo/check/${todoId}/`, {
                        method: 'POST',
                        headers: {
                            // djangoのセキュリティのために必要
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                    })
                    .then(response => response.json())
                    .then(data => {
                        // チェック状態をコンソールで確認
                        console.log('check:', data.check);
                    })
                    .catch(error => console.error('エラー:', error));

                    // completed/incompleteへの移動
                    const todoItem = this.closest(".todo-content");
                    updateCount();
                    if(this.checked){ completed.appendChild(todoItem); } else { incomplete.appendChild(todoItem); }
                });

                // todoのタイトル変更
                div.querySelector(".todo-title").addEventListener("blur", function() {
                    const todoId = this.dataset.id;
                    fetch(`/index/json/todo/edit/title/${todoId}/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ title: this.value })  // ← 新しいタイトルを送る
                    })
                    .then(response => response.json())
                    .then(data => {})
                    .catch(error => console.error('エラー:', error));
                });
            }

            incomplete.innerHTML = "";
            completed.querySelectorAll(".todo-content").forEach(el => el.remove());

            // todoリストの生成
            data.forEach(todo => {
                // todoのdiv要素を作る
                const div = document.createElement("div");
                div.className = "todo-content";
                div.innerHTML = `
                    <input class="todo-check" type="checkbox" data-id="${todo.id}" ${todo.check ? 'checked' : ''}>
                    <input class="todo-title" data-id="${todo.id}" type="text" value="${todo.title}">
                    <div class="todo-delete"><button data-id="${todo.id}">&times;</button></div>
                `;
                // 完了済みのフィールドに持ってくるか処理する
                if(todo.check){ completed.appendChild(div); } else { incomplete.appendChild(div); }
                attachTodoEvents(div);
            });

            // todoの合計を出力
            document.querySelectorAll(".task-sum").forEach(e => { e.textContent = data.length; });
            updateCount();

            // 詳細モーダルからのtodo新規作成
            (function() {
                const title_area = document.querySelector(".add-todo-input");

                function add_todo() {
                    // 空なら何もしない
                    if (!title_area.value.trim()) return;

                    fetch(`/index/json/todo/create/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            title: title_area.value,
                            event: id  // イベントのidを送る
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // DOMに追加
                        const div = document.createElement("div");
                        div.className = "todo-content";
                        div.innerHTML = `
                            <input class="todo-check" type="checkbox" data-id="${data.id}">
                            <input class="todo-title" data-id="${data.id}" type="text" value="${data.title}">
                            <div class="todo-delete"><button data-id="${data.id}">&times;</button></div>
                        `;
                        incomplete.appendChild(div);
                        // イベントリスナーを登録
                        attachTodoEvents(div);
                        // inputをリセット
                        title_area.value = "";
                        updateCount();
                    })
                    .catch(error => console.error('エラー:', error));
                }

                // blurで追加
                title_area.addEventListener("blur", add_todo);

                // Enterキーでも追加
                title_area.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        add_todo();
                    }
                });
            })();
        })
        .catch(error => { console.error('エラー:', error); });
    }
    // カレzンダーをスワイプできるようにする
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
    class CreateEditSide{
        constructor(){
            this.sidebar = document.getElementById("create-sidebar");
            this.form = document.getElementById("create-event-field")
            this.cancel_btns = document.querySelectorAll(".cancel-btn");
            this.close_btn = document.querySelectorAll(".cancel-btn");
            this.allday_cehck = document.querySelectorAll(".event-allday");
            this.open_btn = document.getElementById("create-sidebar-open")
            this.init();
        }
        open(mode, event) {
            // イベント作成
            if (mode === 'create') {
                this.setCreateMode();
            // イベント編集
            } else if (mode === 'edit') {
                this.setEditMode(event);
            }

            this.show();
        }
        close() {
            this.sidebar.classList.remove("active");
            this.form.action = "";
            this.form.reset();
            getFp("#create-start-date input").clear();
            getFp("#create-end-date input").clear();
            document.querySelector(".create-other-option").style.display = "none";
            document.querySelector(".other-optuin-hidden").style.display = "block";
            setTimeout(() => {
                calendar.updateSize();
                window.dispatchEvent(new Event('resize'));
            }, 100);
        }
        // 内部メソッド---------------------------------
        // サイドバーを開く
        show(){
            this.sidebar.classList.add("active");
            calendar.updateSize();
            setTimeout(() => calendar.updateSize(), 300);
        }
        // イベント作成用メソッド
        setCreateMode() {
            this.form.action = "/index/event/create/";
            this.form.reset();

            // 時間入力を非表示
            document.querySelectorAll(".create-time").forEach(el => {
                el.style.display = "none";
            });

            // 今日の日付をセット
            const today = this.getTodayStr();
            getFp("#create-start-date input").setDate(today, false);
            getFp("#create-end-date input").setDate(today, false);
        }
        // イベント編集用メソッド
        setEditMode(event) {
            const { id, props, fcEvent } = event;

            // actionにイベントIDを代入
            this.form.action = `/index/event/${id}/edit/`;

            // 日付
            getFp("#create-start-date input").setDate(props.start_date, false);
            const endDateObj = new Date(props.end_date);
            endDateObj.setDate(endDateObj.getDate() - 1);
            getFp("#create-end-date input").setDate(endDateObj.toISOString().split('T')[0], false);

            // 時刻
            const startTimeFp = document.querySelector("#create-start-time input")?._flatpickr;
            const endTimeFp   = document.querySelector("#create-end-time input")?._flatpickr;
            if (startTimeFp) startTimeFp.setDate(props.start_time, false);
            if (endTimeFp)   endTimeFp.setDate(props.end_time, false);

            // タイトル
            document.querySelector(".id_title").value = fcEvent.title;

            // 終日
            const alldayCheck = document.querySelector(".event-allday");
            alldayCheck.checked = fcEvent.allDay;
            this.allday();

            // ルーム
            // ※ #create-selectroom 内だけ対象にしてrepeat/colorのセレクタと混在しないようにする
            const roomSelectWrapper = document.querySelector("#create-selectroom .custom-select");
            if (roomSelectWrapper && props.room_id) {
                roomSelectWrapper.querySelectorAll(".custom-select-option").forEach(el => {
                    el.classList.remove("is-selected");
                    if (el.dataset.value == props.room_id) {
                        el.classList.add("is-selected");
                        roomSelectWrapper.querySelector(".custom-select-selected").textContent = el.textContent.trim();
                        roomSelectWrapper.querySelector(".custom-select-value").value = el.dataset.value;
                    }
                });
            }

            // 色
            // ※ #create-color-options 内だけ対象にする
            const colorSelectWrapper = document.querySelector("#create-color-options .custom-select");
            if (colorSelectWrapper && props.color_id) {
                colorSelectWrapper.querySelectorAll(".custom-select-option").forEach(el => {
                    el.classList.remove("is-selected");
                    if (el.dataset.value == props.color_id) {
                        el.classList.add("is-selected");
                        colorSelectWrapper.querySelector(".custom-select-selected").textContent = el.textContent.trim();
                        colorSelectWrapper.querySelector(".custom-select-value").value = el.dataset.value;
                    }
                });
            }

            // 繰り返し
            // ※ #create-repeat-options 内だけ対象にする
            const repeatSelectWrapper = document.querySelector("#create-repeat-options .custom-select");
            if (repeatSelectWrapper && props.repeat_id) {
                repeatSelectWrapper.querySelectorAll(".custom-select-option").forEach(el => {
                    el.classList.remove("is-selected");
                    if (el.dataset.value == props.repeat_id) {
                        el.classList.add("is-selected");
                        repeatSelectWrapper.querySelector(".custom-select-selected").textContent = el.textContent.trim();
                        repeatSelectWrapper.querySelector(".custom-select-value").value = el.dataset.value;
                    }
                });
            }

            // URL・場所・メモ
            if (props.event_url) document.querySelector("#id_url").value = props.event_url;
            if (props.locate)    document.querySelector("#id_location").value = props.locate;
            if (props.memo)      document.querySelector("#id_memo").value = props.memo;

            // メモのUI表示も更新
            const memoOutput = document.getElementById("memo-output");
            if (memoOutput) {
                memoOutput.textContent = props.memo || "メモ";
                memoOutput.style.color = props.memo ? "" : "grey";
            }

            // 編集モードではオプション領域を常に展開する
            const otherOption = document.querySelector(".create-other-option");
            const hiddenBtn   = document.querySelector(".other-optuin-hidden");
            if (otherOption) otherOption.style.display = "block";
            if (hiddenBtn)   hiddenBtn.style.display = "none";
        }
        // 今日の日付を取得するメソッド
        getTodayStr() {
            const d = new Date();
            const y = d.getFullYear();
            const m = String(d.getMonth() + 1).padStart(2, "0");
            const day = String(d.getDate()).padStart(2, "0");
            return `${y}-${m}-${day}`;
        }
        allday() {
            const alldays = document.querySelectorAll(".event-allday");
            alldays.forEach(cb => {
                const timeOptions = cb.closest(".time-options");
                const startTime = timeOptions.querySelector(".create-start .create-time");
                const endTime = timeOptions.querySelector(".create-end .create-time");
                startTime.style.display = cb.checked ? "none" : "";
                endTime.style.display = cb.checked ? "none" : "";
            });
        }
        init() {
            this.open_btn.addEventListener("click", () => this.open('create'));

            // キャンセルボタンが押されたら閉じる
            this.cancel_btns.forEach(btn => {
                btn.addEventListener("click", () => this.close());
            });

            this.allday_cehck.forEach(cb => {
                cb.addEventListener("change", () => this.allday());
            });
        }
    }
    const sidebarfunc = new CreateEditSide();

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

        selectedTextEl.innerHTML = optionEl.innerHTML;
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
        // html要素ごと選択済みに追加する
        selectedTextEl.innerHTML = defaultOption.innerHTML;
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
        sidebarfunc.close()
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

    // 編集ボタンを押したときの挙動
    document.getElementById("detail-edit").addEventListener("click", function(e){
        if (!currentEvent) return;


        // 詳細モーダルを閉じる
        document.getElementById("detail-event-modal").classList.remove("hidden");

        // サイドバーを開く
        sidebarfunc.open(
            'edit',
            currentEvent
        )
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
    document.getElementById("current-dates").addEventListener("click", function(e) {
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
    })();
    // todo詳細モーダル
    (function() {
        //  チェックリスト ?/?完了の表示-------------------------------------------
        const detailtodo = document.getElementById("detail-todo")
        const todo_icon = document.getElementById("todo-icon")
        const overlay     = document.querySelector(".todo-detail-overlay");
        let task_sum = document.querySelectorAll(".todo-detail-content .todo-check");
        const completed = document.querySelector(".completed");
        const incomplete = document.querySelector(".incomplete");
        detailtodo.addEventListener("click", function(e) {
            e.stopPropagation();
            overlay.classList.add("active");
        });
        todo_icon.addEventListener("click", function(e) {
            e.stopPropagation();
            overlay.classList.add("active");
        });
        // 閉じる
        document.addEventListener('click', function(e) {
            const overlay = document.querySelector(".todo-detail-overlay");
            // 閉じるボタン
            if (e.target.closest('.todo-detail-close')) {
                overlay.classList.remove("active");
                return;
            }
            // モーダル外クリック
            if (!e.target.closest('.todo-detail-modal')) {
                overlay.classList.remove("active");
            }
        });
        // ----------------------------------------------------------------------
    })();
    document.getElementById("calendar").addEventListener("click", () => console.log("calendar clicked"));
});

function closeDayEventsModal() {
    document.getElementById("day-events-overlay").classList.remove("active");
}