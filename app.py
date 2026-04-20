from __future__ import annotations

import io
from typing import Iterable

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="고객클레임 현황 관리 대시보드", layout="wide")

ALL = "전체"
STATUS = ["접수", "분석중", "조치중", "완료", "보류"]
ASSIGNEES = ["미배정", "김대리", "이과장", "박차장", "최부장"]
BAR_COLORS = ["#3565e0", "#f7a30a", "#1fb784", "#ef4444", "#8257e6", "#21acc7", "#84cc16", "#f97316"]

HEADER_MAP = {
    "date": "date", "일자": "date", "등록일": "date", "반납일자": "date",
    "brand": "brand", "브랜드": "brand", "제조지": "brand",
    "claimno": "claimNo", "접수번호": "claimNo", "클레임번호": "claimNo",
    "type": "type", "유형": "type", "형태": "type",
    "major": "major", "구분(대)": "major", "구분대": "major", "구분": "major",
    "mid": "mid", "구분(중)": "mid", "구분중": "mid", "세부유": "mid", "세부유형": "mid",
    "detail": "detail", "하자상세": "detail", "상세": "detail",
    "cause": "cause", "원인": "cause", "로트": "cause",
    "customer": "customer", "고객명": "customer", "현장명": "customer",
    "product": "product", "품명": "product", "부품명": "product",
    "model": "model", "모델": "model", "제품코드": "model",
    "actiondept": "actionDept", "담당부서": "actionDept", "조치부서": "actionDept",
    "qty": "qty", "수량": "qty",
    "cost": "cost", "비용": "cost", "금액": "cost",
    "ppm": "ppm",
    "duedate": "dueDate", "완료예정일": "dueDate",
    "memo": "memo", "메모": "memo", "조치내용": "memo",
    "requestdetail": "requestDetail", "요청내용": "requestDetail",
}

SAMPLE_RAW = [
    {"date": "2024-01-13", "brand": "일룸", "claimNo": "I202401130071-01", "type": "생산", "major": "시공미결", "mid": "가공", "detail": "보링불량", "cause": "외주(세진)", "customer": "송도 현장", "product": "측판", "model": "ILM-BR-07", "actionDept": "생산팀", "qty": 1, "cost": 76000, "ppm": 145, "dueDate": "2024-01-14", "memo": "가공 치공구 점검"},
    {"date": "2024-01-12", "brand": "데스커", "claimNo": "D202401120061-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "이물질", "cause": "외주(올품)", "customer": "하남 현장", "product": "상판", "model": "DS-TOP-88", "actionDept": "구매팀", "qty": 1, "cost": 98000, "ppm": 162, "dueDate": "2024-01-13", "memo": "외주 청정관리 요청"},
    {"date": "2024-01-11", "brand": "퍼시스", "claimNo": "F202401110051-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "색상불일치", "cause": "외주(제일)", "customer": "김포 현장", "product": "도장부품", "model": "PSC-COLOR-11", "actionDept": "구매팀", "qty": 1, "cost": 112000, "ppm": 176, "dueDate": "2024-01-12", "memo": "색상 기준 샘플 재배포"},
    {"date": "2024-01-10", "brand": "일룸", "claimNo": "I202401100041-01", "type": "생산", "major": "시공미결", "mid": "포장", "detail": "포장누락", "cause": "외주(에픽)", "customer": "용인 현장", "product": "부품박스", "model": "ILM-PK-01", "actionDept": "물류팀", "qty": 1, "cost": 42000, "ppm": 119, "dueDate": "2024-01-11", "memo": "외주 포장 기준 전달"},
    {"date": "2024-01-09", "brand": "데스커", "claimNo": "D202401090031-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "스크래치", "cause": "외주(유진)", "customer": "분당 현장", "product": "서랍 전면", "model": "DS-FR-10", "actionDept": "구매팀", "qty": 2, "cost": 93000, "ppm": 158, "dueDate": "2024-01-10", "memo": "입고검사 강화 필요"},
    {"date": "2024-01-08", "brand": "퍼시스", "claimNo": "F202401080021-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "표면 찍힘", "cause": "외주(송아)", "customer": "서초 현장", "product": "도어", "model": "PSC-DOOR-01", "actionDept": "구매팀", "qty": 1, "cost": 87000, "ppm": 148, "dueDate": "2024-01-09", "memo": "외주업체 재작업 요청"},
    {"date": "2024-01-07", "brand": "일룸", "claimNo": "I202401070012-01", "type": "생산", "major": "시공미결", "mid": "가공", "detail": "루타가공불량", "cause": "3라인", "customer": "일룸 가구 현장", "product": "상판", "model": "ILM-RT-22", "actionDept": "생산팀", "qty": 1, "cost": 61000, "ppm": 132, "dueDate": "2024-01-08", "memo": "가공조건 재점검"},
    {"date": "2024-01-06", "brand": "일룸", "claimNo": "I202401060011-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "이물질", "cause": "4라인", "customer": "일룸 서재 현장", "product": "상판", "model": "ILM-TOP-01", "actionDept": "생산팀", "qty": 1, "cost": 92000, "ppm": 154, "dueDate": "2024-01-07", "memo": "외관 검사 강화"},
]


def inject_style() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, header, footer { visibility: hidden; height: 0; }
        .stApp { background: linear-gradient(180deg, #f8fbff 0%, #eef4fc 100%); }
        .block-container { max-width: 1480px; padding-top: 0.5rem; padding-bottom: 2rem; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border-radius: 22px;
            border: none !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            padding: 0.2rem 0.2rem 0.35rem 0.2rem;
        }
        div[data-testid="stMetric"] {
            background: white;
            border-radius: 22px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.07);
            padding: 0.75rem 0.9rem;
        }
        div[data-testid="stMetricLabel"] {
            color: #64748b;
            font-size: 12px;
            font-weight: 600;
        }
        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-size: 20px;
            font-weight: 800;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 11px;
        }
        div[data-testid="stSelectbox"] > label,
        div[data-testid="stTextInput"] > label {
            font-weight: 700 !important;
            color: #475569 !important;
            font-size: 11px !important;
        }
        div[data-testid="stSelectbox"] > div > div,
        div[data-testid="stTextInput"] input {
            min-height: 40px !important;
            border-radius: 13px !important;
            font-size: 13px !important;
        }
        div[data-testid="stButton"] > button {
            border-radius: 999px !important;
            min-height: 40px !important;
            font-weight: 700 !important;
            white-space: nowrap !important;
            font-size: 12px !important;
        }
        button[kind="primary"] {
            background: #0f172a !important;
            border-color: #0f172a !important;
        }
        .section-title {
            font-size: 17px;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 3px;
        }
        .section-desc {
            font-size: 12px;
            color: #64748b;
            margin-bottom: 10px;
        }
        .brand-pill {
            display: inline-block;
            white-space: nowrap;
            padding: 5px 9px;
            border-radius: 999px;
            border: 1px solid #cbd5e1;
            background: white;
            font-size: 11px;
            font-weight: 700;
            color: #0f172a;
        }
        .status-pill {
            display: inline-block;
            white-space: nowrap;
            padding: 5px 10px;
            border-radius: 999px;
            background: #0f172a;
            color: white;
            font-size: 11px;
            font-weight: 700;
        }
        .top-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            background: #edf3fb;
            border-radius: 18px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .rank-badge {
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #0f172a;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 13px;
            flex-shrink: 0;
        }
        .top-name {
            font-weight: 800;
            color: #0f172a;
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .count-badge {
            border-radius: 999px;
            padding: 5px 11px;
            border: 1px solid #cbd5e1;
            background: white;
            font-size: 11px;
            font-weight: 700;
            color: #0f172a;
            white-space: nowrap;
        }
        .detail-label { font-size: 12px; color: #64748b; }
        .detail-value { font-size: 14px; color: #0f172a; font-weight: 700; margin-bottom: 8px; }
        .request-box {
            margin-top: 14px;
            background: #f8fafc;
            border-radius: 18px;
            padding: 16px;
            color: #334155;
            line-height: 1.7;
            font-size: 14px;
            white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt(n: float | int) -> str:
    return f"{int(n or 0):,}"


def normalize_row(row: dict, idx: int = 0) -> dict:
    date = str(row.get("date") or "")
    normalized = {
        "date": date,
        "brand": str(row.get("brand") or ""),
        "claimNo": str(row.get("claimNo") or f"CLAIM-{idx + 1:04d}"),
        "type": str(row.get("type") or ""),
        "major": str(row.get("major") or ""),
        "mid": str(row.get("mid") or ""),
        "detail": str(row.get("detail") or ""),
        "cause": str(row.get("cause") or ""),
        "customer": str(row.get("customer") or ""),
        "product": str(row.get("product") or ""),
        "model": str(row.get("model") or ""),
        "actionDept": str(row.get("actionDept") or ""),
        "qty": int(pd.to_numeric(row.get("qty", 0), errors="coerce") or 0),
        "cost": int(pd.to_numeric(row.get("cost", 0), errors="coerce") or 0),
        "ppm": int(pd.to_numeric(row.get("ppm", 0), errors="coerce") or 0),
        "dueDate": str(row.get("dueDate") or ""),
        "memo": str(row.get("memo") or ""),
        "requestDetail": str(row.get("requestDetail") or ""),
        "status": str(row.get("status") or STATUS[idx % len(STATUS)]),
        "assignee": str(row.get("assignee") or ASSIGNEES[idx % len(ASSIGNEES)]),
    }
    normalized["year"] = date[:4]
    normalized["month"] = date[:7]
    normalized["day"] = date[8:10]
    return normalized


def sample_rows() -> list[dict]:
    return [normalize_row(row, idx) for idx, row in enumerate(SAMPLE_RAW)]


def canonicalize_columns(columns: Iterable[str]) -> list[str]:
    return [HEADER_MAP.get(str(col).strip().replace(" ", "").lower(), str(col).strip()) for col in columns]


def detect_header_row(frame: pd.DataFrame) -> int:
    for idx in range(min(len(frame), 10)):
        values = [str(v).strip() for v in frame.iloc[idx].tolist()]
        hits = sum(1 for value in values if value.replace(" ", "").lower() in HEADER_MAP)
        if hits >= 3:
            return idx
    return 0


def read_uploaded_frame(uploaded_file) -> pd.DataFrame:
    suffix = uploaded_file.name.lower().split(".")[-1]
    raw = uploaded_file.getvalue()

    if suffix == "csv":
        for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except Exception:
                continue
        raise ValueError("CSV 파일 인코딩을 읽지 못했습니다.")

    if suffix in {"xlsx", "xls"}:
        excel = pd.ExcelFile(io.BytesIO(raw))
        best_sheet = None
        best_score = -1
        best_header = 0
        for sheet in excel.sheet_names:
            preview = excel.parse(sheet_name=sheet, header=None, dtype=str)
            header_row = detect_header_row(preview)
            header_values = [str(v).strip() for v in preview.iloc[header_row].tolist()]
            score = sum(1 for value in header_values if value.replace(" ", "").lower() in HEADER_MAP)
            if score > best_score:
                best_score = score
                best_sheet = sheet
                best_header = header_row
        if best_sheet is None or best_score < 3:
            raise ValueError("반영할 행을 찾지 못했습니다. 헤더와 데이터 형식을 확인해 주세요.")
        return excel.parse(sheet_name=best_sheet, header=best_header)

    raise ValueError("지원하지 않는 파일 형식입니다. CSV, XLS, XLSX만 가능합니다.")


def frame_to_rows(frame: pd.DataFrame) -> list[dict]:
    clean = frame.copy()
    clean.columns = canonicalize_columns(clean.columns)
    clean = clean.dropna(how="all").fillna("")
    if "date" not in clean.columns:
        raise ValueError("반영할 행을 찾지 못했습니다. 헤더와 데이터 형식을 확인해 주세요.")
    rows = []
    for idx, record in enumerate(clean.to_dict(orient="records")):
        if not str(record.get("date") or "").strip():
            continue
        rows.append(normalize_row(record, idx))
    if not rows:
        raise ValueError("반영할 데이터가 없습니다.")
    return rows


def ensure_state() -> None:
    if "rows" not in st.session_state:
        st.session_state.rows = sample_rows()
    if "selected_claim" not in st.session_state:
        st.session_state.selected_claim = None
    if "show_import" not in st.session_state:
        st.session_state.show_import = False


def filter_options(rows: list[dict], key: str) -> list[str]:
    return [ALL] + sorted({str(row.get(key) or "") for row in rows if str(row.get(key) or "")})


def top_n(rows: list[dict], key: str, limit: int) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "")
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    return pd.DataFrame(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit], columns=["name", "value"])


def request_text(row: dict) -> str:
    if row.get("requestDetail"):
        return str(row["requestDetail"])
    return (
        f"제{row['qty']}원 시공팀 {row['customer']} 시공건으로, {row['detail']}이 발생한 건입니다. "
        f"({row['brand']} {row['model']} {row['product']})\n\n"
        f"1) 수주건명 : {row['customer']}\n"
        f"2) 접수번호 : {row['claimNo']}\n"
        f"3) 시공일자 : {row['date']}\n\n"
        f"원인 : {row['cause']} / 담당부서 : {row['actionDept']}\n"
        f"조치내용 : {row['memo']}"
    )


@st.dialog("엑셀 데이터 반영")
def import_dialog() -> None:
    uploaded = st.file_uploader("CSV / XLS / XLSX 파일 선택", type=["csv", "xls", "xlsx"])
    if uploaded is not None:
        try:
            st.session_state.rows = frame_to_rows(read_uploaded_frame(uploaded))
            st.session_state.selected_claim = None
            st.session_state.show_import = False
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


@st.dialog("클레임 상세 관리")
def detail_dialog(row: dict) -> None:
    st.caption(f"{row['claimNo']} / {row['brand']} / {row['date']}")
    left, right = st.columns(2)
    with left:
        for label, value in [
            ("브랜드", row["brand"]),
            ("모델", row["model"]),
            ("유형", row["type"]),
            ("구분", f"{row['major']} / {row['mid']}"),
            ("원인", row["cause"]),
            ("품명", row["product"]),
        ]:
            st.markdown(f'<div class="detail-label">{label}</div><div class="detail-value">{value}</div>', unsafe_allow_html=True)
    with right:
        for label, value in [
            ("수량", f"{row['qty']} EA"),
            ("완료예정일", row["dueDate"]),
            ("담당자", row["assignee"]),
            ("처리상태", row["status"]),
            ("처리비용", f"{fmt(row['cost'])}원"),
            ("PPM", str(row["ppm"])),
        ]:
            st.markdown(f'<div class="detail-label">{label}</div><div class="detail-value">{value}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="request-box">{request_text(row)}</div>', unsafe_allow_html=True)
    if st.button("닫기", key=f"close_{row['claimNo']}"):
        st.session_state.selected_claim = None
        st.rerun()


def render_top_list(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("표시할 데이터가 없습니다.")
        return
    for idx, row in frame.reset_index(drop=True).iterrows():
        st.markdown(
            f"""
            <div class="top-item">
                <div style="display:flex;align-items:center;gap:12px;min-width:0;">
                    <div class="rank-badge">{idx + 1}</div>
                    <div class="top-name">{row["name"]}</div>
                </div>
                <div class="count-badge">{int(row["value"])}건</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_bar_chart(frame: pd.DataFrame, height: int = 210) -> alt.Chart:
    color_frame = frame.copy()
    color_frame["color"] = [BAR_COLORS[idx % len(BAR_COLORS)] for idx in range(len(color_frame))]
    bar = (
        alt.Chart(color_frame)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("name:N", title="", sort=None, axis=alt.Axis(labelAngle=0, labelLimit=120)),
            y=alt.Y("value:Q", title="", axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("name:N", scale=alt.Scale(domain=color_frame["name"].tolist(), range=color_frame["color"].tolist()), legend=None),
            tooltip=[alt.Tooltip("name:N", title="구분"), alt.Tooltip("value:Q", title="건수")],
        )
        .properties(height=height)
    )
    label = bar.mark_text(dy=-8, color="#334155").encode(text=alt.Text("value:Q", format=".0f"))
    return bar + label


inject_style()
ensure_state()

if st.session_state.show_import:
    import_dialog()
if st.session_state.selected_claim:
    detail_dialog(st.session_state.selected_claim)

rows = st.session_state.rows

with st.container(border=True):
    top_left, top_right = st.columns([7, 6])
    with top_left:
        st.markdown('<div class="section-title">조회 조건</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-desc">엑셀 표 붙여넣기 또는 CSV 업로드로 데이터를 추가하거나 교체할 수 있습니다.</div>', unsafe_allow_html=True)
    with top_right:
        a, b, c = st.columns([1, 1, 1.05])
        if a.button("필터 초기화", use_container_width=True):
            st.rerun()
        if b.button("샘플 복원", use_container_width=True):
            st.session_state.rows = sample_rows()
            st.session_state.selected_claim = None
            st.rerun()
        if c.button("엑셀 데이터 넣기", use_container_width=True, type="primary"):
            st.session_state.show_import = True
            st.rerun()

    f1, f2, f3, f4, f5, f6 = st.columns(6)
    brand = f1.selectbox("브랜드", filter_options(rows, "brand"))
    major = f2.selectbox("구분(대)", filter_options(rows, "major"))
    mid = f3.selectbox("구분(중)", filter_options(rows, "mid"))
    cause = f4.selectbox("원인", filter_options(rows, "cause"))
    type_value = f5.selectbox("유형", filter_options(rows, "type"))
    year = f6.selectbox("년도", filter_options(rows, "year"))

    f7, f8, f9 = st.columns([1.05, 1.05, 2.65])
    month = f7.selectbox("월", filter_options(rows, "month"))
    day = f8.selectbox("일", filter_options(rows, "day"))
    search = f9.text_input("검색", placeholder="접수번호, 모델, 하자상세, 고객명 검색")

filtered = []
query = search.strip().lower()
for row in rows:
    haystack = " ".join([row["claimNo"], row["customer"], row["product"], row["model"], row["detail"], row["cause"], row["memo"]]).lower()
    if brand != ALL and row["brand"] != brand:
        continue
    if major != ALL and row["major"] != major:
        continue
    if mid != ALL and row["mid"] != mid:
        continue
    if cause != ALL and row["cause"] != cause:
        continue
    if type_value != ALL and row["type"] != type_value:
        continue
    if year != ALL and row["year"] != year:
        continue
    if month != ALL and row["month"] != month:
        continue
    if day != ALL and row["day"] != day:
        continue
    if query and query not in haystack:
        continue
    filtered.append(row)

total_count = len(filtered)
open_count = sum(1 for row in filtered if row["status"] != "완료")
completed_count = total_count - open_count
completion_rate = (completed_count / total_count * 100) if total_count else 0.0
total_cost = sum(int(row["cost"]) for row in filtered)
avg_ppm = (sum(int(row["ppm"]) for row in filtered) / total_count) if total_count else 0.0

month_counts = {}
for row in rows:
    month_counts[row["month"]] = month_counts.get(row["month"], 0) + 1
monthly_all = sorted(month_counts.items())
latest = monthly_all[-1][1] if monthly_all else 0
prev = monthly_all[-2][1] if len(monthly_all) > 1 else 0
delta = latest - prev

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("총 클레임 건수", f"{fmt(total_count)}건", delta=f"{delta:+d}건")
k2.metric("미완료 건수", f"{fmt(open_count)}건")
k3.metric("완료율", f"{completion_rate:.1f}%")
k4.metric("처리비용 합계", f"{fmt(total_cost)}원")
k5.metric("평균 PPM", f"{avg_ppm:.0f}")

monthly = pd.DataFrame(filtered)
if monthly.empty:
    monthly = pd.DataFrame(columns=["month", "claimNo"])
monthly_trend = monthly.groupby("month", as_index=False).agg(count=("claimNo", "count")).sort_values("month")
major_pie = top_n(filtered, "major", 6)
cause_top = top_n(filtered, "cause", 6)
brand_top = top_n(filtered, "brand", 6)
type_top = top_n(filtered, "type", 6)
detail_top = top_n(filtered, "detail", 10)
recent_df = pd.DataFrame(filtered).sort_values("date", ascending=False).head(20) if filtered else pd.DataFrame()

c1, c2 = st.columns([1.75, 1.05])
with c1:
    with st.container(border=True):
        st.markdown("#### 월별 클레임 추이")
        if monthly_trend.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            line = (
                alt.Chart(monthly_trend)
                .mark_line(point=alt.OverlayMarkDef(size=60, filled=True, color="#3565e0"), color="#3565e0", strokeWidth=2.8)
                .encode(
                    x=alt.X("month:N", title="", axis=alt.Axis(labelPadding=10)),
                    y=alt.Y("count:Q", title="", axis=alt.Axis(tickMinStep=1, gridDash=[2, 4])),
                    tooltip=[alt.Tooltip("month:N", title="월"), alt.Tooltip("count:Q", title="건수")],
                )
                .properties(height=250)
            )
            labels = line.mark_text(dy=-10, color="#3565e0").encode(text="count:Q")
            st.altair_chart(line + labels, use_container_width=True)

with c2:
    with st.container(border=True):
        st.markdown("#### 구분(대) 비중")
        if major_pie.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            pie_source = major_pie.copy()
            total = pie_source["value"].sum()
            pie_source["ratio"] = pie_source["value"] / total if total else 0
            donut = (
                alt.Chart(pie_source)
                .mark_arc(innerRadius=38, outerRadius=82)
                .encode(
                    theta=alt.Theta("value:Q"),
                    color=alt.Color("name:N", scale=alt.Scale(range=["#3565e0", "#f7a30a", "#1fb784", "#ef4444"]), legend=alt.Legend(title="구분", orient="right")),
                    tooltip=[
                        alt.Tooltip("name:N", title="구분"),
                        alt.Tooltip("value:Q", title="건수"),
                        alt.Tooltip("ratio:Q", title="비중", format=".1%"),
                    ],
                )
                .properties(height=250)
            )
            st.altair_chart(donut, use_container_width=True)

b1, b2, b3 = st.columns(3)
with b1:
    with st.container(border=True):
        st.markdown("#### 원인별 현황")
        if cause_top.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            st.altair_chart(render_bar_chart(cause_top), use_container_width=True)
with b2:
    with st.container(border=True):
        st.markdown("#### 브랜드별 현황")
        if brand_top.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            st.altair_chart(render_bar_chart(brand_top), use_container_width=True)
with b3:
    with st.container(border=True):
        st.markdown("#### 유형별 현황")
        if type_top.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            st.altair_chart(render_bar_chart(type_top), use_container_width=True)

t1, t2 = st.columns([0.72, 2.48])
with t1:
    with st.container(border=True):
        st.markdown("#### 하자상세 TOP 10")
        render_top_list(detail_top)

with t2:
    with st.container(border=True):
        st.markdown("#### 최근 세부내역 20건")
        if recent_df.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            widths = [1.0, 0.75, 1.65, 1.15, 1.0, 0.95, 0.72, 0.72, 0.78, 0.48, 0.88]
            headers = st.columns(widths)
            labels = ["일자", "브랜드", "접수번호", "구분", "하자상세", "원인", "담당자", "상태", "비용", "PPM", "동작"]
            for col, label in zip(headers, labels):
                col.markdown(f"<div style='font-size:11px;font-weight:800;color:#475569'>{label}</div>", unsafe_allow_html=True)
            st.divider()
            for _, row in recent_df.iterrows():
                cols = st.columns(widths)
                cols[0].markdown(f"<div style='font-size:11px;white-space:nowrap'>{row['date']}</div>", unsafe_allow_html=True)
                cols[1].markdown(f"<span class='brand-pill'>{row['brand']}</span>", unsafe_allow_html=True)
                cols[2].markdown(f"<div style='font-size:11px;white-space:nowrap;font-weight:800'>{row['claimNo']}</div>", unsafe_allow_html=True)
                cols[3].markdown(f"<div style='font-size:11px'>{row['major']} / {row['mid']}</div>", unsafe_allow_html=True)
                cols[4].markdown(f"<div style='font-size:11px;white-space:nowrap'>{row['detail']}</div>", unsafe_allow_html=True)
                cols[5].markdown(f"<div style='font-size:11px;white-space:nowrap'>{row['cause']}</div>", unsafe_allow_html=True)
                cols[6].markdown(f"<div style='font-size:11px;white-space:nowrap'>{row['assignee']}</div>", unsafe_allow_html=True)
                cols[7].markdown(f"<span class='status-pill'>{row['status']}</span>", unsafe_allow_html=True)
                cols[8].markdown(f"<div style='font-size:11px;white-space:nowrap'>{fmt(row['cost'])}원</div>", unsafe_allow_html=True)
                cols[9].markdown(f"<div style='font-size:11px;white-space:nowrap'>{row['ppm']}</div>", unsafe_allow_html=True)
                if cols[10].button("상세조회", key=f"detail_{row['claimNo']}", use_container_width=True):
                    st.session_state.selected_claim = row.to_dict()
                    st.rerun()
                st.divider()
