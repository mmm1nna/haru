import streamlit as st
import sqlite3
from pathlib import Path
from datetime import date, datetime
import pandas as pd

# ---------------------------------------------------------
# 하루(HARU) - 가족 성장 기록 앱
# 실행: streamlit run app.py
# 기본 저장소: SQLite (app.py와 같은 폴더의 haru.db)
# ---------------------------------------------------------

st.set_page_config(
    page_title="하루 | 우리의 성장을 기록하다",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).with_name("haru.db")

COLORS = {
    "primary": "#718875",
    "sage": "#E9EDE4",
    "cream": "#F6F6F0",
    "text": "#344438",
    "muted": "#718075",
    "white": "#FFFFFF",
}

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Pretendard', sans-serif;
        color: {COLORS['text']};
    }}
    .stApp {{ background: {COLORS['cream']}; }}
    [data-testid="stSidebar"] {{ background: {COLORS['sage']}; }}
    .brand {{
        font-size: 2.15rem; font-weight: 800; letter-spacing: -1.5px;
        color: {COLORS['primary']}; margin-bottom: 0;
    }}
    .subbrand {{ color: {COLORS['muted']}; font-size: .95rem; margin-top: -4px; }}
    .hero {{
        background: linear-gradient(120deg, #E9EDE4, #F8F7F0);
        border: 1px solid #DDE5D9; border-radius: 22px;
        padding: 28px 30px; margin: 8px 0 22px 0;
    }}
    .hero h2 {{ margin: 0 0 8px 0; font-size: 1.65rem; }}
    .hero p {{ margin: 0; color: #647568; }}
    .metric-card {{
        background: white; border: 1px solid #E5E9E1; border-radius: 16px;
        padding: 18px 20px; min-height: 112px;
    }}
    .metric-label {{ color: #718075; font-size: .9rem; }}
    .metric-value {{ color: #344438; font-size: 1.8rem; font-weight: 800; margin-top: 5px; }}
    .section-title {{ font-size: 1.18rem; font-weight: 750; margin: 18px 0 10px 0; }}
    .record-card {{
        background: white; border: 1px solid #E7EAE3; border-radius: 15px;
        padding: 16px 18px; margin-bottom: 10px;
    }}
    .tag {{
        display: inline-block; padding: 4px 9px; border-radius: 20px;
        background: #E9EDE4; color: #526B56; font-size: .78rem; font-weight: 600;
        margin-right: 5px;
    }}
    div.stButton > button[kind="primary"] {{
        background: {COLORS['primary']}; border: 0; border-radius: 10px;
    }}
    div.stButton > button {{ border-radius: 10px; }}
    div[data-testid="stForm"] {{
        background: white; padding: 18px; border: 1px solid #E5E9E1;
        border-radius: 15px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT '가족',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS growth_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                subject TEXT NOT NULL,
                record_type TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                event_date TEXT NOT NULL,
                visibility TEXT NOT NULL DEFAULT '가족 공개',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT '진행 중',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS appreciations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS record_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                self_record_id INTEGER NOT NULL,
                observation_record_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(self_record_id, observation_record_id)
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        if count == 0:
            now = datetime.now().isoformat(timespec="seconds")
            conn.executemany(
                "INSERT INTO members(name, role, created_at) VALUES (?, ?, ?)",
                [
                    ("엄마", "부모", now),
                    ("아빠", "부모", now),
                    ("오빠", "자녀", now),
                    ("나", "자녀", now),
                    ("여동생", "자녀", now),
                ],
            )


def query(sql, params=()):
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql, params=()):
    with connect() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def get_members():
    return [r["name"] for r in query("SELECT name FROM members ORDER BY id")]


def page_header(title, description=""):
    st.markdown(f"## {title}")
    if description:
        st.caption(description)


init_db()
members = get_members()

if "current_user" not in st.session_state:
    st.session_state.current_user = members[0] if members else "가족"
if st.session_state.current_user not in members and members:
    st.session_state.current_user = members[0]

# Sidebar
with st.sidebar:
    st.markdown('<p class="brand">하루</p>', unsafe_allow_html=True)
    st.markdown('<p class="subbrand">우리의 성장을 기록하다</p>', unsafe_allow_html=True)
    st.divider()
    current_user = st.selectbox(
        "현재 사용자",
        members,
        index=members.index(st.session_state.current_user) if st.session_state.current_user in members else 0,
        key="user_selector",
    )
    st.session_state.current_user = current_user
    st.caption("테스트용 사용자 선택입니다.")
    st.divider()
    menu = st.radio(
        "메뉴",
        ["홈", "성장 기록", "가족 성장", "마음 전달", "성장 아카이브", "가족 설정"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("🌱 작은 노력도 소중하게, 하루하루 차곡차곡.")

# HOME
if menu == "홈":
    st.markdown(
        """
        <div class="hero">
            <h2>오늘의 작은 성장도 기록해 보세요 🌿</h2>
            <p>결과만이 아니라 노력한 과정과 서로가 발견한 순간을 함께 남겨요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    records = query("SELECT * FROM growth_records ORDER BY created_at DESC")
    goals = query("SELECT * FROM goals WHERE status != '완료'")
    messages = query("SELECT * FROM appreciations ORDER BY created_at DESC")
    c1, c2, c3 = st.columns(3)
    for col, label, value in [
        (c1, "함께 쌓은 성장 기록", len(records)),
        (c2, "진행 중인 목표", len(goals)),
        (c3, "전달된 응원", len(messages)),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}개</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">최근 성장 기록</div>', unsafe_allow_html=True)
    if records:
        for r in records[:5]:
            kind = "나의 기록" if r["record_type"] == "self" else "발견 기록"
            st.markdown(
                f"""<div class="record-card">
                <span class="tag">{kind}</span><span class="tag">{r['category']}</span>
                <b>{r['title']}</b><br>
                <span style="color:#718075;font-size:.85rem">{r['author']} → {r['subject']} · {r['event_date']}</span>
                <p style="margin:9px 0 0 0">{r['content']}</p></div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("아직 기록이 없어요. 오늘의 작은 노력부터 남겨 보세요.")

    st.markdown('<div class="section-title">진행 중인 목표</div>', unsafe_allow_html=True)
    if goals:
        for g in goals[:4]:
            due = f" · 목표일 {g['due_date']}" if g["due_date"] else ""
            st.write(f"🎯 **{g['owner']}** — {g['title']}{due}")
    else:
        st.caption("등록된 목표가 없습니다.")

# GROWTH RECORDS
elif menu == "성장 기록":
    page_header("성장 기록", "나의 노력과 가족이 발견한 모습을 각각 기록하고 함께 살펴보세요.")
    tab1, tab2, tab3 = st.tabs(["나의 노력 기록", "가족의 발견 기록", "기록 연결"])
    with tab1:
        with st.form("self_record_form", clear_on_submit=True):
            st.subheader("내가 해낸 작은 일")
            subject = st.selectbox("기록할 사람", members, index=members.index(current_user))
            title = st.text_input("제목", placeholder="예: 어려웠던 수학 문제를 끝까지 풀어 봄")
            category = st.selectbox("분류", ["공부", "일상", "도전", "취미", "관계", "기타"])
            event_date = st.date_input("날짜", value=date.today())
            content = st.text_area("어떤 노력을 했나요? 어떻게 느꼈나요?", height=120)
            visibility = st.radio("공개 범위", ["가족 공개", "나만 보기"], horizontal=True)
            submitted = st.form_submit_button("성장 기록 저장", type="primary", use_container_width=True)
            if submitted:
                if not title.strip() or not content.strip():
                    st.error("제목과 내용을 입력해 주세요.")
                else:
                    execute(
                        """INSERT INTO growth_records
                        (author, subject, record_type, category, title, content, event_date, visibility, created_at)
                        VALUES (?, ?, 'self', ?, ?, ?, ?, ?, ?)""",
                        (current_user, subject, category, title.strip(), content.strip(),
                         event_date.isoformat(), visibility, datetime.now().isoformat(timespec="seconds")),
                    )
                    st.success("나의 성장 기록을 저장했어요.")
                    st.rerun()

    with tab2:
        with st.form("observation_form", clear_on_submit=True):
            st.subheader("가족에게서 발견한 성장")
            author = st.selectbox("작성자", members, index=members.index(current_user), key="obs_author")
            subject = st.selectbox("누구의 모습인가요?", members, key="obs_subject")
            title = st.text_input("발견한 순간", placeholder="예: 동생에게 먼저 다가가 도와줌")
            category = st.selectbox("분류", ["공부", "일상", "도전", "취미", "관계", "기타"], key="obs_category")
            event_date = st.date_input("날짜", value=date.today(), key="obs_date")
            content = st.text_area("어떤 점이 인상 깊었나요?", height=120, key="obs_content")
            visibility = st.radio("공개 범위", ["가족 공개", "나만 보기"], horizontal=True, key="obs_visibility")
            submitted = st.form_submit_button("발견 기록 저장", type="primary", use_container_width=True)
            if submitted:
                if not title.strip() or not content.strip():
                    st.error("제목과 내용을 입력해 주세요.")
                else:
                    execute(
                        """INSERT INTO growth_records
                        (author, subject, record_type, category, title, content, event_date, visibility, created_at)
                        VALUES (?, ?, 'observation', ?, ?, ?, ?, ?, ?)""",
                        (author, subject, category, title.strip(), content.strip(),
                         event_date.isoformat(), visibility, datetime.now().isoformat(timespec="seconds")),
                    )
                    st.success("가족의 발견을 기록했어요.")
                    st.rerun()

    with tab3:
        st.subheader("서로의 기록 연결하기")
        st.caption("같은 경험에 대한 나의 기록과 가족의 발견 기록을 연결할 수 있어요.")
        self_rows = query("SELECT * FROM growth_records WHERE record_type='self' ORDER BY created_at DESC")
        obs_rows = query("SELECT * FROM growth_records WHERE record_type='observation' ORDER BY created_at DESC")
        if not self_rows or not obs_rows:
            st.info("연결하려면 나의 노력 기록과 가족의 발견 기록이 각각 하나 이상 필요해요.")
        else:
            self_options = {
                f"#{r['id']} {r['subject']} · {r['title']} ({r['event_date']})": r["id"]
                for r in self_rows
            }
            obs_options = {
                f"#{r['id']} {r['subject']} · {r['title']} ({r['event_date']})": r["id"]
                for r in obs_rows
            }
            with st.form("link_form"):
                self_label = st.selectbox("나의 노력 기록", list(self_options.keys()))
                obs_label = st.selectbox("가족의 발견 기록", list(obs_options.keys()))
                link_submit = st.form_submit_button("두 기록 연결", type="primary")
                if link_submit:
                    try:
                        execute(
                            "INSERT INTO record_links(self_record_id, observation_record_id, created_at) VALUES (?, ?, ?)",
                            (self_options[self_label], obs_options[obs_label], datetime.now().isoformat(timespec="seconds")),
                        )
                        st.success("두 기록을 연결했어요.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.warning("이미 연결된 기록이에요.")

        links = query(
            """SELECT l.id, a.title AS self_title, a.subject AS self_subject,
                      b.title AS obs_title, b.author AS obs_author, b.subject AS obs_subject
               FROM record_links l
               JOIN growth_records a ON a.id=l.self_record_id
               JOIN growth_records b ON b.id=l.observation_record_id
               ORDER BY l.created_at DESC"""
        )
        if links:
            st.markdown("#### 연결된 성장 기록")
            for l in links:
                st.markdown(
                    f"""<div class="record-card">
                    <b>{l['self_subject']}의 기록</b>: {l['self_title']}<br>
                    <b>{l['obs_author']}가 발견한 {l['obs_subject']}의 모습</b>: {l['obs_title']}
                    </div>""",
                    unsafe_allow_html=True,
                )

# FAMILY GROWTH
elif menu == "가족 성장":
    page_header("가족 성장", "가족 구성원 각자의 목표와 성장 과정을 확인해요.")
    with st.expander("새로운 목표 만들기", expanded=True):
        with st.form("goal_form", clear_on_submit=True):
            owner = st.selectbox("목표를 가진 사람", members, index=members.index(current_user))
            title = st.text_input("목표", placeholder="예: 매일 영어 단어 15개 복습하기")
            description = st.text_area("목표를 위한 계획 또는 필요한 도움", height=80)
            due_date = st.date_input("목표일", value=date.today())
            submitted = st.form_submit_button("목표 저장", type="primary")
            if submitted:
                if not title.strip():
                    st.error("목표를 입력해 주세요.")
                else:
                    execute(
                        "INSERT INTO goals(owner, title, description, due_date, status, created_at) VALUES (?, ?, ?, ?, '진행 중', ?)",
                        (owner, title.strip(), description.strip(), due_date.isoformat(), datetime.now().isoformat(timespec="seconds")),
                    )
                    st.success("목표를 저장했어요.")
                    st.rerun()

    goals = query("SELECT * FROM goals ORDER BY created_at DESC")
    if goals:
        for g in goals:
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**🎯 {g['owner']} · {g['title']}**")
                    if g["description"]:
                        st.caption(g["description"])
                    st.caption(f"목표일: {g['due_date'] or '미정'} · 상태: {g['status']}")
                with right:
                    new_status = st.selectbox(
                        "상태", ["진행 중", "완료", "잠시 보류"],
                        index=["진행 중", "완료", "잠시 보류"].index(g["status"]),
                        key=f"goal_status_{g['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != g["status"]:
                        execute("UPDATE goals SET status=? WHERE id=?", (new_status, g["id"]))
                        st.rerun()
    else:
        st.info("첫 번째 목표를 만들어 보세요.")

    st.markdown("### 구성원별 기록")
    cols = st.columns(min(3, max(1, len(members))))
    for i, member in enumerate(members):
        count = query("SELECT COUNT(*) AS n FROM growth_records WHERE subject=?", (member,))[0]["n"]
        with cols[i % len(cols)]:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{member}</div>'
                f'<div class="metric-value">{count}개</div><div class="metric-label">성장 기록</div></div>',
                unsafe_allow_html=True,
            )
    st.caption("기록 개수는 관심이나 사랑의 크기를 의미하지 않으며, 가족 구성원을 비교하거나 순위를 매기기 위한 지표가 아니에요.")

# APPRECIATIONS
elif menu == "마음 전달":
    page_header("마음 전달", "고마움과 응원을 구체적인 말로 전해 보세요.")
    with st.form("appreciation_form", clear_on_submit=True):
        recipient = st.selectbox("받는 사람", [m for m in members if m != current_user] or members)
        message_type = st.selectbox("메시지 종류", ["칭찬", "응원", "감사", "사랑"])
        message = st.text_area("전하고 싶은 말", placeholder="오늘 네가 보여 준 모습 중 어떤 점이 좋았는지 적어 보세요.", height=120)
        submitted = st.form_submit_button("마음 전하기", type="primary", use_container_width=True)
        if submitted:
            if not message.strip():
                st.error("전하고 싶은 말을 입력해 주세요.")
            else:
                execute(
                    "INSERT INTO appreciations(author, recipient, message_type, message, created_at) VALUES (?, ?, ?, ?, ?)",
                    (current_user, recipient, message_type, message.strip(), datetime.now().isoformat(timespec="seconds")),
                )
                st.success(f"{recipient}에게 마음을 전했어요.")
                st.rerun()

    st.markdown("### 우리 가족에게 도착한 마음")
    messages = query("SELECT * FROM appreciations ORDER BY created_at DESC")
    if messages:
        for m in messages:
            st.markdown(
                f"""<div class="record-card">
                <span class="tag">{m['message_type']}</span>
                <b>{m['author']} → {m['recipient']}</b>
                <p style="margin:9px 0 0 0">{m['message']}</p>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("아직 도착한 메시지가 없어요. 먼저 따뜻한 말을 전해 보세요.")

# ARCHIVE
elif menu == "성장 아카이브":
    page_header("성장 아카이브", "지나온 하루를 돌아보며 쌓여 온 변화를 확인해요.")
    all_records = query("SELECT * FROM growth_records ORDER BY event_date DESC, created_at DESC")
    if all_records:
        df = pd.DataFrame([dict(r) for r in all_records])
        people = ["전체"] + members
        selected_person = st.selectbox("구성원", people)
        if selected_person != "전체":
            df = df[df["subject"] == selected_person]
        if not df.empty:
            df["event_date"] = pd.to_datetime(df["event_date"])
            min_date = df["event_date"].min().date()
            max_date = df["event_date"].max().date()
            st.caption(f"기록 기간: {min_date} ~ {max_date}")
            counts = df.groupby("subject").size().reset_index(name="기록 수")
            st.markdown("### 기록 현황")
            st.bar_chart(counts.set_index("subject"))
            st.markdown("### 기록 모아보기")
            for _, r in df.iterrows():
                kind = "나의 기록" if r["record_type"] == "self" else "발견 기록"
                st.markdown(
                    f"""<div class="record-card">
                    <span class="tag">{kind}</span><span class="tag">{r['category']}</span>
                    <b>{r['title']}</b><br>
                    <span style="color:#718075;font-size:.85rem">{r['event_date'].date()} · {r['author']} → {r['subject']}</span>
                    <p style="margin:9px 0 0 0">{r['content']}</p></div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("선택한 구성원의 기록이 아직 없어요.")
    else:
        st.info("기록이 쌓이면 이곳에서 가족의 성장 과정을 돌아볼 수 있어요.")

# SETTINGS
elif menu == "가족 설정":
    page_header("가족 설정", "가족 구성원을 관리하고 프로필을 확인해요.")
    st.markdown("### 가족 구성원")
    current_members = query("SELECT * FROM members ORDER BY id")
    for m in current_members:
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            st.write(f"**{m['name']}**")
        with c2:
            st.caption(m["role"])
        with c3:
            if len(current_members) > 1 and st.button("삭제", key=f"delete_member_{m['id']}"):
                execute("DELETE FROM members WHERE id=?", (m["id"],))
                st.rerun()

    st.markdown("### 구성원 추가")
    with st.form("member_form", clear_on_submit=True):
        new_name = st.text_input("이름 또는 가족 호칭", placeholder="예: 할머니")
        new_role = st.selectbox("역할", ["부모", "자녀", "가족"])
        add = st.form_submit_button("구성원 추가", type="primary")
        if add:
            if not new_name.strip():
                st.error("이름을 입력해 주세요.")
            elif new_name.strip() in get_members():
                st.error("이미 등록된 이름이에요.")
            else:
                execute(
                    "INSERT INTO members(name, role, created_at) VALUES (?, ?, ?)",
                    (new_name.strip(), new_role, datetime.now().isoformat(timespec="seconds")),
                )
                st.success("가족 구성원을 추가했어요.")
                st.rerun()

    st.warning(
        "현재 버전은 기능 확인용 SQLite 저장 방식이에요. Streamlit Cloud에 배포하면 "
        "여러 기기에서 같은 데이터가 안정적으로 공유되거나 영구 보존된다고 보장할 수 없어요. "
        "실제 가족이 함께 사용할 때는 Supabase 연동과 계정별 접근 권한 설정이 필요해요."
    )

st.divider()
st.caption("하루 HARU · 우리의 성장을 기록하다")
