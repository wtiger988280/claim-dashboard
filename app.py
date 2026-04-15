from __future__ import annotations

import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError


st.set_page_config(page_title="고객클레임 현황 관리 대시보드", layout="wide")

STATUS = ["접수", "분석중", "조치중", "완료", "보류"]
ASSIGNEES = ["미배정", "김대리", "이과장", "박차장", "최부장"]

HEADER_MAP = {
    "date": "date",
    "일자": "date",
    "등록일": "date",
    "반납일자": "date",
    "brand": "brand",
    "브랜드": "brand",
    "제조지": "brand",
    "claimno": "claimNo",
    "접수번호": "claimNo",
    "클레임번호": "claimNo",
    "type": "type",
    "유형": "type",
    "형태": "type",
    "major": "major",
    "구분(대)": "major",
    "구분대": "major",
    "구분": "major",
    "mid": "mid",
    "구분(중)": "mid",
    "구분중": "mid",
    "세부유": "mid",
    "세부유형": "mid",
    "detail": "detail",
    "하자상세": "detail",
    "상세": "detail",
    "유형별": "detail",
    "유형분류": "detail",
    "cause": "cause",
    "원인": "cause",
    "customer": "customer",
    "고객명": "customer",
    "고객": "customer",
    "product": "product",
    "품명": "product",
    "제품": "product",
    "부품명": "product",
    "model": "model",
    "모델": "model",
    "제품코드": "model",
    "actiondept": "actionDept",
    "담당부서": "actionDept",
    "조치부서": "actionDept",
    "조치건": "actionDept",
    "회수구분": "actionDept",
    "서비스": "actionDept",
    "qty": "qty",
    "수량": "qty",
    "cost": "cost",
    "비용": "cost",
    "금액": "cost",
    "ppm": "ppm",
    "duedate": "dueDate",
    "완료예정일": "dueDate",
    "예정일": "dueDate",
    "memo": "memo",
    "메모": "memo",
    "비고": "memo",
    "로트": "memo",
}

NUMERIC_COLUMNS = {"qty", "cost", "ppm"}
REQUIRED_HINTS = {"date", "brand", "claimNo", "major", "mid", "detail", "cause", "customer", "product", "model"}

SAMPLE_ROWS = [
    {"date": "2024-01-13", "brand": "일룸", "claimNo": "I202401130071-01", "type": "생산", "major": "시공미결", "mid": "가공", "detail": "보링불량", "cause": "외주(세진)", "customer": "송도 현장", "product": "측판", "model": "ILM-BR-07", "actionDept": "생산팀", "qty": 1, "cost": 76000, "ppm": 145, "dueDate": "2024-01-14", "memo": "가공 치공구 점검", "status": "접수", "assignee": "미배정"},
    {"date": "2024-01-12", "brand": "데스커", "claimNo": "D202401120061-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "이물질", "cause": "외주(올품)", "customer": "하남 현장", "product": "상판", "model": "DS-TOP-88", "actionDept": "구매팀", "qty": 1, "cost": 98000, "ppm": 162, "dueDate": "2024-01-13", "memo": "외주 청정관리 요청", "status": "분석중", "assignee": "김대리"},
    {"date": "2024-01-11", "brand": "퍼시스", "claimNo": "F202401110051-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "색상불일치", "cause": "외주(제일)", "customer": "김포 현장", "product": "도장부품", "model": "PSC-COLOR-11", "actionDept": "구매팀", "qty": 1, "cost": 112000, "ppm": 176, "dueDate": "2024-01-12", "memo": "색상 기준 샘플 재배포", "status": "조치중", "assignee": "이과장"},
    {"date": "2024-01-10", "brand": "일룸", "claimNo": "I202401100041-01", "type": "생산", "major": "시공미결", "mid": "포장", "detail": "포장누락", "cause": "외주(에픽)", "customer": "용인 현장", "product": "부품박스", "model": "ILM-PK-01", "actionDept": "물류팀", "qty": 1, "cost": 42000, "ppm": 119, "dueDate": "2024-01-11", "memo": "외주 포장 기준 전달", "status": "보류", "assignee": "최부장"},
    {"date": "2024-01-09", "brand": "데스커", "claimNo": "D202401090031-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "스크래치", "cause": "외주(유진)", "customer": "분당 현장", "product": "서랍 전면", "model": "DS-FR-10", "actionDept": "구매팀", "qty": 2, "cost": 93000, "ppm": 158, "dueDate": "2024-01-10", "memo": "입고검사 강화 필요", "status": "완료", "assignee": "박차장"},
    {"date": "2024-01-08", "brand": "퍼시스", "claimNo": "F202401080021-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "표면 찍힘", "cause": "외주(송아)", "customer": "서초 현장", "product": "도어", "model": "PSC-DOOR-01", "actionDept": "구매팀", "qty": 1, "cost": 87000, "ppm": 148, "dueDate": "2024-01-09", "memo": "외주업체 재작업 요청", "status": "접수", "assignee": "이과장"},
    {"date": "2024-01-07", "brand": "일룸", "claimNo": "I202401070012-01", "type": "생산", "major": "시공미결", "mid": "가공", "detail": "루타가공불량", "cause": "3라인", "customer": "일룸 가구 현장", "product": "상판", "model": "ILM-RT-22", "actionDept": "생산팀", "qty": 1, "cost": 61000, "ppm": 132, "dueDate": "2024-01-08", "memo": "가공조건 재점검", "status": "접수", "assignee": "김대리"},
    {"date": "2024-01-06", "brand": "일룸", "claimNo": "I202401060011-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "이물질", "cause": "4라인", "customer": "일룸 서재 현장", "product": "상판", "model": "ILM-TOP-01", "actionDept": "생산팀", "qty": 1, "cost": 92000, "ppm": 154, "dueDate": "2024-01-07", "memo": "외관 검사 강화", "status": "접수", "assignee": "미배정"},
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%); }
        .block-container { max-width: 1500px; padding-top: 28px; padding-bottom: 36px; }
        .hero {
            background: linear-gradient(135deg, #172033 0%, #263247 100%);
            border-radius: 28px;
            padding: 20px 28px 30px 28px;
            color: white;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.15);
            margin-bottom: 24px;
        }
        .hero-chip {
            display: inline-flex;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 16px;
        }
        .hero h1 {
            margin: 0;
            font-size: 48px;
            font-weight: 900;
            line-height: 1.18;
            letter-spacing: -0.02em;
        }
        .hero p {
            margin: 18px 0 0 0;
            color: #dbe4f3;
            font-size: 16px;
        }
        .filter-wrap, .kpi-card, .panel {
            background: white;
            border-radius: 26px;
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(226, 232, 240, 0.9);
        }
        .filter-wrap { padding: 22px 22px 16px 22px; margin-bottom: 22px; }
        .kpi-card { padding: 18px 22px; min-height: 148px; }
        .panel { padding: 20px 20px 18px 20px; }
        .panel-title, .filter-title {
            color: #0f172a;
            font-size: 18px;
            font-weight: 900;
            margin-bottom: 6px;
        }
        .filter-note, .kpi-note {
            color: #64748b;
            font-size: 13px;
        }
        .kpi-title {
            color: #64748b;
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .kpi-value {
            color: #0f172a;
            font-size: 24px;
            font-weight: 900;
            line-height: 1.15;
            margin-bottom: 8px;
        }
        .trend-pill {
            display: inline-flex;
            padding: 7px 12px;
            border-radius: 999px;
            background: #fee2e2;
            color: #dc2626;
            font-size: 12px;
            font-weight: 800;
            margin-top: 10px;
        }
        .top-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            background: #f1f5f9;
            border-radius: 18px;
            padding: 10px 12px;
            margin-bottom: 12px;
        }
        .rank {
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: #020617;
            color: white;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 900;
            flex: 0 0 auto;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            background: white;
            font-size: 11px;
            font-weight: 800;
            white-space: nowrap;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 999px;
            background: #0f172a;
            color: white;
            font-size: 11px;
            font-weight: 800;
        }
        .legend-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }
        .stMultiSelect label, .stTextInput label, .stFileUploader label { font-weight: 700 !important; }
        .stButton button {
            border-radius: 999px;
            font-weight: 800;
            padding: 10px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_header(value: object) -> str:
    return str(value or "").strip().replace(" ", "").lower()


def normalize_columns(columns: list[object]) -> list[str]:
    normalized: list[str] = []
    for column in columns:
        raw = str(column or "").strip()
        key = HEADER_MAP.get(raw) or HEADER_MAP.get(clean_header(raw))
        normalized.append(key or raw)
    return normalized


def score_headers(columns: list[object]) -> int:
    return sum(1 for col in normalize_columns(columns) if col in REQUIRED_HINTS)


def dataframe_from_best_header(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all").reset_index(drop=True)
    if df.empty:
        return df
    best_index = 0
    best_score = -1
    for idx in range(min(len(df), 10)):
        score = score_headers(list(df.iloc[idx].fillna("").astype(str)))
        if score > best_score:
            best_score = score
            best_index = idx
    headers = normalize_columns(list(df.iloc[best_index].fillna("").astype(str)))
    data = df.iloc[best_index + 1 :].copy().reset_index(drop=True)
    data.columns = headers
    return data.dropna(how="all")


def normalize_value(key: str, value: object) -> object:
    if pd.isna(value):
        return ""
    if key in NUMERIC_COLUMNS:
        text = str(value).strip().replace(",", "")
        if not text:
            return 0
        try:
            number = float(text)
            return int(number) if number.is_integer() else number
        except ValueError:
            return 0
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if key in {"date", "dueDate"} and text:
        try:
            parsed = pd.to_datetime(text)
            if not pd.isna(parsed):
                return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass
    return text


def read_excel_flexible(buffer: io.BytesIO, engine: str | None = None) -> pd.DataFrame:
    buffer.seek(0)
    workbook = pd.read_excel(buffer, sheet_name=None, header=None, engine=engine)
    best_df = None
    best_score = -1
    for _, sheet_df in workbook.items():
        candidate = dataframe_from_best_header(sheet_df)
        if candidate.empty:
            continue
        score = score_headers(list(candidate.columns))
        if score > best_score:
            best_score = score
            best_df = candidate
    if best_df is None:
        raise ValueError("반영할 행을 찾지 못했습니다. 헤더와 데이터 형식을 확인해 주세요.")
    return best_df


def read_legacy_xls(file_bytes: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(file_bytes)
    try:
        return read_excel_flexible(buffer)
    except Exception:
        pass
    for encoding in ("utf-8", "cp949", "euc-kr", "latin1"):
        try:
            tables = pd.read_html(io.StringIO(file_bytes.decode(encoding)))
            if tables:
                return dataframe_from_best_header(tables[0])
        except (UnicodeDecodeError, ValueError, EmptyDataError):
            continue
    raise ValueError(".xls 파일을 읽지 못했습니다. 가능하면 .xlsx 또는 .csv로 저장해서 올려 주세요.")


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    required = ["date", "brand", "claimNo", "type", "major", "mid", "detail", "cause", "customer", "product", "model", "actionDept", "qty", "cost", "ppm", "dueDate", "memo", "status", "assignee"]
    for idx, column in enumerate(required):
        if column not in df.columns:
            if column == "status":
                df[column] = [STATUS[i % len(STATUS)] for i in range(len(df))]
            elif column == "assignee":
                df[column] = [ASSIGNEES[i % len(ASSIGNEES)] for i in range(len(df))]
            else:
                df[column] = ""
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").fillna(0)
    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0)
    df["ppm"] = pd.to_numeric(df["ppm"], errors="coerce").fillna(0)
    df["year"] = df["date"].astype(str).str.slice(0, 4)
    df["month"] = df["date"].astype(str).str.slice(0, 7)
    df["day"] = df["date"].astype(str).str.slice(8, 10)
    return df


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    file_bytes = uploaded_file.getvalue()
    if suffix == ".csv":
        df = pd.read_csv(io.BytesIO(file_bytes))
        df.columns = normalize_columns(list(df.columns))
    elif suffix == ".xlsx":
        df = read_excel_flexible(io.BytesIO(file_bytes), engine="openpyxl")
    elif suffix == ".xls":
        df = read_legacy_xls(file_bytes)
    else:
        raise ValueError("csv, xls, xlsx 파일만 업로드할 수 있습니다.")
    records: list[dict] = []
    for record in df.dropna(how="all").to_dict(orient="records"):
        row = {key: normalize_value(key, value) for key, value in record.items() if key}
        if row.get("claimNo") or row.get("customer") or row.get("detail"):
            records.append(row)
    if not records:
        raise ValueError("반영할 행을 찾지 못했습니다. 헤더와 데이터 형식을 확인해 주세요.")
    return ensure_columns(pd.DataFrame(records))


def sample_dataframe() -> pd.DataFrame:
    return ensure_columns(pd.DataFrame(SAMPLE_ROWS))


def top_n(df: pd.DataFrame, column: str, n: int) -> pd.DataFrame:
    series = df[column].fillna("").astype(str)
    series = series[series != ""]
    return series.value_counts().head(n).rename_axis("name").reset_index(name="count")


def format_won(value: float) -> str:
    return f"{int(value):,}원"


def metric_card(title: str, value: str, desc: str, trend: str | None = None) -> None:
    trend_html = f"<div class='trend-pill'>{trend}</div>" if trend else ""
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div><div class='kpi-note'>{desc}</div>{trend_html}</div>",
        unsafe_allow_html=True,
    )


def render_claim_dialog(row: pd.Series) -> None:
    left, right = st.columns(2)
    with left:
        st.markdown("**기본 정보**")
        st.write(f"브랜드: {row['brand']}")
        st.write(f"모델: {row['model']}")
        st.write(f"유형: {row['type']}")
        st.write(f"구분: {row['major']} / {row['mid']}")
        st.write(f"원인: {row['cause']}")
        st.write(f"품명: {row['product']}")
        st.write(f"수량: {int(row['qty'])} EA")
        st.write(f"완료예정일: {row['dueDate']}")
    with right:
        st.markdown("**처리 관리**")
        st.write(f"담당자: {row['assignee']}")
        st.write(f"상태: {row['status']}")
        st.write(f"처리비용: {format_won(float(row['cost']))}")
        st.write(f"PPM: {int(row['ppm'])}")
        st.write(f"담당부서: {row['actionDept']}")
    request_text = row["memo"] or f"{row['customer']} 현장에서 {row['detail']}이 발생했습니다. ({row['brand']} / {row['model']} / {row['product']})"
    st.markdown("**요청내용 / 조치내용**")
    st.text_area("request_detail_view", value=request_text, height=220, disabled=True, label_visibility="collapsed")


def select_with_all(column, label: str, values: list[str], key: str) -> str:
    options = ["전체"] + values
    return column.selectbox(label, options, index=0, key=key)


inject_css()

if "dialog_claim" not in st.session_state:
    st.session_state.dialog_claim = None

st.markdown(
    """
    <div class="hero">
      <div class="hero-chip">품질보증팀 고객클레임 관리</div>
      <h1>고객클레임 현황 관리 대시보드</h1>
      <p>고객 클레임 접수, 원인, 처리상태, 비용, PPM을 한눈에 확인할 수 있도록 구성한 화면입니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded = None
st.markdown("<div class='filter-wrap'>", unsafe_allow_html=True)
header_cols = st.columns([4.4, 1.1, 1.0, 1.4])
header_cols[0].markdown("<div class='filter-title'>조회 조건</div><div class='filter-note'>엑셀 표 붙여넣기 또는 CSV 업로드로 데이터를 추가하거나 교체할 수 있습니다.</div>", unsafe_allow_html=True)
reset_clicked = header_cols[1].button("필터 초기화")
sample_clicked = header_cols[2].button("샘플 복원")
uploaded = header_cols[3].file_uploader("엑셀 데이터 넣기", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

if uploaded:
    try:
        df = load_uploaded_file(uploaded)
    except Exception as error:
        st.error(str(error))
        df = sample_dataframe()
elif sample_clicked:
    df = sample_dataframe()
else:
    df = sample_dataframe()

row1 = st.columns(6)
brand = select_with_all(row1[0], "브랜드", sorted(df["brand"].dropna().astype(str).unique()), "brand_filter")
major = select_with_all(row1[1], "구분(대)", sorted(df["major"].dropna().astype(str).unique()), "major_filter")
mid = select_with_all(row1[2], "구분(중)", sorted(df["mid"].dropna().astype(str).unique()), "mid_filter")
cause = select_with_all(row1[3], "원인", sorted(df["cause"].dropna().astype(str).unique()), "cause_filter")
claim_type = select_with_all(row1[4], "유형", sorted(df["type"].dropna().astype(str).unique()), "type_filter")
year = select_with_all(row1[5], "년도", sorted(df["year"].dropna().astype(str).unique()), "year_filter")

row2 = st.columns([1, 1, 4])
month = select_with_all(row2[0], "월", sorted(df["month"].dropna().astype(str).unique()), "month_filter")
day = select_with_all(row2[1], "일", sorted(df["day"].dropna().astype(str).unique()), "day_filter")
query = row2[2].text_input("검색", placeholder="접수번호, 모델, 하자상세, 고객명 검색", key="query_filter")
st.markdown("</div>", unsafe_allow_html=True)

if reset_clicked:
    for key in ["brand_filter", "major_filter", "mid_filter", "cause_filter", "type_filter", "year_filter", "month_filter", "day_filter"]:
        st.session_state[key] = "전체"
    st.session_state["query_filter"] = ""
    st.rerun()

filtered = df.copy()
for column, selected in {
    "brand": brand,
    "major": major,
    "mid": mid,
    "cause": cause,
    "type": claim_type,
    "year": year,
    "month": month,
    "day": day,
}.items():
    if selected != "전체":
        filtered = filtered[filtered[column].astype(str) == str(selected)]

if query:
    lowered = query.lower()
    mask = filtered.astype(str).apply(lambda col: col.str.lower().str.contains(lowered, na=False))
    filtered = filtered[mask.any(axis=1)]

total_count = len(filtered)
total_cost = float(filtered["cost"].sum())
avg_ppm = float(filtered["ppm"].mean()) if total_count else 0
completed = int((filtered["status"].astype(str) == "완료").sum())
open_count = total_count - completed
completion_rate = (completed / total_count * 100) if total_count else 0
monthly_all = df.groupby("month").size().sort_index()
delta = 0 if len(monthly_all) < 2 else int(monthly_all.iloc[-1] - monthly_all.iloc[-2])

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    metric_card("총 클레임 건수", f"{total_count}건", "현재 조건 기준 접수 건수", f"전월 대비 {delta:+d}건")
with k2:
    metric_card("미완료 건수", f"{open_count}건", "접수 · 분석 · 조치중 포함")
with k3:
    metric_card("완료율", f"{completion_rate:.1f}%", "완료 상태 기준 처리율")
with k4:
    metric_card("처리비용 합계", format_won(total_cost), "선택 조건 기준 누적 비용")
with k5:
    metric_card("평균 PPM", f"{avg_ppm:.0f}", "선택 조건 기준 평균 수준")

trend = filtered.groupby("month").size().reset_index(name="건수").sort_values("month")
major_counts = filtered["major"].fillna("").astype(str)
major_counts = major_counts[major_counts != ""].value_counts().reset_index()
major_counts.columns = ["구분", "건수"]
major_counts["비율"] = major_counts["건수"] / major_counts["건수"].sum() * 100 if not major_counts.empty else 0

top_row_left, top_row_right = st.columns([2.1, 1.1])
with top_row_left:
    st.markdown("<div class='panel'><div class='panel-title'>월별 클레임 추이</div>", unsafe_allow_html=True)
    if trend.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        base = alt.Chart(trend).encode(x=alt.X("month:N", title=""), y=alt.Y("건수:Q", title="", scale=alt.Scale(zero=True)))
        chart = base.mark_line(color="#2563eb", point=alt.OverlayMarkDef(color="#2563eb", size=70, filled=True)).properties(height=250)
        labels = base.mark_text(dy=-12, color="#2563eb").encode(text="건수:Q")
        st.altair_chart(chart + labels, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with top_row_right:
    st.markdown("<div class='panel'><div class='panel-title'>구분(대) 비중</div>", unsafe_allow_html=True)
    if major_counts.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        pie = alt.Chart(major_counts).mark_arc(innerRadius=48).encode(
            theta="건수:Q",
            color=alt.Color("구분:N", scale=alt.Scale(range=["#2563eb", "#f59e0b", "#10b981", "#ef4444"])),
            tooltip=["구분:N", "건수:Q", alt.Tooltip("비율:Q", format=".1f")],
        ).properties(height=250)
        st.altair_chart(pie, use_container_width=True)
        color_map = {"고객불만": "#2563eb", "시공미결": "#f59e0b"}
        for _, row in major_counts.iterrows():
            color = color_map.get(row["구분"], "#10b981")
            st.markdown(f"<div class='legend-row'><span class='dot' style='background:{color}'></span>{row['구분']} {int(row['건수'])}건</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

mid1, mid2, mid3 = st.columns(3)
for column, title, target in [("cause", "원인별 현황", mid1), ("brand", "브랜드별 현황", mid2), ("type", "유형별 현황", mid3)]:
    with target:
        st.markdown(f"<div class='panel'><div class='panel-title'>{title}</div>", unsafe_allow_html=True)
        counts = top_n(filtered, column, 6)
        if counts.empty:
            st.write("표시할 데이터가 없습니다.")
        else:
            counts["color"] = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4"][: len(counts)]
            bars = alt.Chart(counts).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
                x=alt.X("name:N", title="", sort=None),
                y=alt.Y("count:Q", title=""),
                color=alt.Color("color:N", scale=None),
                tooltip=["name:N", "count:Q"],
            ).properties(height=220)
            labels = alt.Chart(counts).mark_text(dy=-10).encode(x="name:N", y="count:Q", text="count:Q")
            st.altair_chart(bars + labels, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

bottom_left, bottom_right = st.columns([1.05, 2.95])
with bottom_left:
    st.markdown("<div class='panel'><div class='panel-title'>하자상세 TOP 10</div>", unsafe_allow_html=True)
    detail_top = top_n(filtered, "detail", 10)
    if detail_top.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        for idx, row in detail_top.iterrows():
            st.markdown(
                f"<div class='top-item'><div style='display:flex;align-items:center;gap:10px;min-width:0;'><span class='rank'>{idx + 1}</span><span style='font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{row['name']}</span></div><span class='pill'>{row['count']}건</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_right:
    st.markdown("<div class='panel'><div class='panel-title'>최근 세부내역 20건</div>", unsafe_allow_html=True)
    recent = filtered.sort_values("date", ascending=False).head(20).reset_index(drop=True)
    if recent.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        headers = st.columns([1.0, 0.9, 1.8, 1.6, 1.5, 1.0, 0.9, 0.9, 1.0, 0.7, 1.0])
        for col, title in zip(headers, ["일자", "브랜드", "접수번호", "구분", "하자상세", "원인", "담당자", "상태", "비용", "PPM", "동작"]):
            col.markdown(f"**{title}**")
        for idx, row in recent.iterrows():
            cols = st.columns([1.0, 0.9, 1.8, 1.6, 1.5, 1.0, 0.9, 0.9, 1.0, 0.7, 1.0])
            cols[0].write(str(row["date"]))
            cols[1].markdown(f"<span class='pill'>{row['brand']}</span>", unsafe_allow_html=True)
            cols[2].write(str(row["claimNo"]))
            cols[3].write(f"{row['major']} / {row['mid']}")
            cols[4].write(str(row["detail"]))
            cols[5].write(str(row["cause"]))
            cols[6].write(str(row["assignee"]))
            cols[7].markdown(f"<span class='status-pill'>{row['status']}</span>", unsafe_allow_html=True)
            cols[8].write(format_won(float(row["cost"])))
            cols[9].write(str(int(row["ppm"])))
            if cols[10].button("상세조회", key=f"detail_{idx}_{row['claimNo']}"):
                st.session_state.dialog_claim = row["claimNo"]
    st.markdown("</div>", unsafe_allow_html=True)

selected_claim = st.session_state.get("dialog_claim")
selected_df = df[df["claimNo"].astype(str) == str(selected_claim)] if selected_claim else pd.DataFrame()

if not selected_df.empty and hasattr(st, "dialog"):
    row = selected_df.iloc[0]

    @st.dialog("클레임 상세 관리", width="large")
    def open_claim_dialog() -> None:
        st.caption(f"{row['claimNo']} / {row['brand']} / {row['date']}")
        render_claim_dialog(row)
        if st.button("닫기", key="dialog_close_btn"):
            st.session_state.dialog_claim = None
            st.rerun()

    open_claim_dialog()
elif not selected_df.empty:
    row = selected_df.iloc[0]
    st.markdown("---")
    st.subheader("클레임 상세 관리")
    st.caption(f"{row['claimNo']} / {row['brand']} / {row['date']}")
    render_claim_dialog(row)
