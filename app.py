from __future__ import annotations

import io
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from pandas.errors import EmptyDataError


st.set_page_config(page_title="고객클레임 현황 관리 대시보드", layout="wide")

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
STATUS = ["접수", "분석중", "조치중", "완료", "보류"]
ASSIGNEES = ["미배정", "김대리", "이과장", "박차장", "최부장"]

SAMPLE_ROWS = [
    {"date": "2024-01-13", "brand": "일룸", "claimNo": "I202401130071-01", "type": "생산", "major": "시공미결", "mid": "가공", "detail": "보링불량", "cause": "외주(세진)", "customer": "송도 현장", "product": "측판", "model": "ILM-BR-07", "actionDept": "생산팀", "qty": 1, "cost": 76000, "ppm": 145, "dueDate": "2024-01-14", "memo": "가공 치공구 점검", "status": "조치중", "assignee": "이과장"},
    {"date": "2024-01-12", "brand": "데스커", "claimNo": "D202401120061-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "이물질", "cause": "외주(올품)", "customer": "하남 현장", "product": "상판", "model": "DS-TOP-88", "actionDept": "구매팀", "qty": 1, "cost": 98000, "ppm": 162, "dueDate": "2024-01-13", "memo": "외주 청정관리 요청", "status": "분석중", "assignee": "김대리"},
    {"date": "2024-01-11", "brand": "퍼시스", "claimNo": "F202401110051-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "색상불일치", "cause": "외주(제일)", "customer": "김포 현장", "product": "도장부품", "model": "PSC-COLOR-11", "actionDept": "구매팀", "qty": 1, "cost": 112000, "ppm": 176, "dueDate": "2024-01-12", "memo": "색상 기준 샘플 재배포", "status": "접수", "assignee": "미배정"},
    {"date": "2024-01-10", "brand": "일룸", "claimNo": "I202401100041-01", "type": "생산", "major": "시공미결", "mid": "포장", "detail": "포장누락", "cause": "외주(에픽)", "customer": "용인 현장", "product": "부품박스", "model": "ILM-PK-01", "actionDept": "물류팀", "qty": 1, "cost": 42000, "ppm": 119, "dueDate": "2024-01-11", "memo": "외주 포장 기준 전달", "status": "보류", "assignee": "최부장"},
    {"date": "2024-01-09", "brand": "데스커", "claimNo": "D202401090031-01", "type": "생산불만", "major": "고객불만", "mid": "외관", "detail": "스크래치", "cause": "외주(유진)", "customer": "분당 현장", "product": "서랍 전면", "model": "DS-FR-10", "actionDept": "구매팀", "qty": 2, "cost": 93000, "ppm": 158, "dueDate": "2024-01-10", "memo": "입고검사 강화 필요", "status": "완료", "assignee": "박차장"},
    {"date": "2024-01-08", "brand": "퍼시스", "claimNo": "F202401080021-01", "type": "생산불만", "major": "고객불만", "mid": "자재", "detail": "표면 찍힘", "cause": "외주(송아)", "customer": "서초 현장", "product": "도어", "model": "PSC-DOOR-01", "actionDept": "구매팀", "qty": 1, "cost": 87000, "ppm": 148, "dueDate": "2024-01-09", "memo": "외주업체 재작업 요청", "status": "조치중", "assignee": "이과장"},
]


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


def render_claim_dialog(row: pd.Series) -> None:
    st.markdown("**기본 정보**")
    c1, c2 = st.columns(2)
    c1.write(f"브랜드: {row['brand']}")
    c2.write(f"모델: {row['model']}")
    c1.write(f"유형: {row['type']}")
    c2.write(f"구분: {row['major']} / {row['mid']}")
    c1.write(f"원인: {row['cause']}")
    c2.write(f"품명: {row['product']}")
    c1.write(f"수량: {int(row['qty'])} EA")
    c2.write(f"완료예정일: {row['dueDate']}")

    st.markdown("**처리 관리**")
    c3, c4 = st.columns(2)
    c3.write(f"담당자: {row['assignee']}")
    c4.write(f"상태: {row['status']}")
    c3.write(f"처리비용: {format_won(float(row['cost']))}")
    c4.write(f"PPM: {int(row['ppm'])}")
    st.write(f"담당부서: {row['actionDept']}")

    request_text = row["memo"] or f"{row['customer']} 현장에서 {row['detail']}이 발생했습니다. ({row['brand']} / {row['model']} / {row['product']})"
    st.markdown("**요청내용 / 조치내용**")
    st.text_area("request_detail_view", value=request_text, height=220, disabled=True, label_visibility="collapsed")


st.title("고객클레임 현황 관리 대시보드")
st.caption("엑셀 또는 CSV를 올리면 대시보드가 갱신됩니다. 파일이 없을 때는 샘플 데이터를 먼저 보여줍니다.")

uploaded = st.file_uploader("엑셀 또는 CSV 업로드", type=["xlsx", "xls", "csv"])

if uploaded:
    try:
        df = load_uploaded_file(uploaded)
        st.success(f"{uploaded.name} 파일 기준으로 대시보드를 표시합니다.")
    except Exception as error:
        st.error(str(error))
        df = sample_dataframe()
        st.info("업로드 데이터를 읽지 못해 샘플 대시보드를 대신 표시합니다.")
else:
    df = sample_dataframe()
    st.info("샘플 데이터로 대시보드를 먼저 표시합니다. 실제 파일을 올리면 바로 교체됩니다.")

if "dialog_claim" not in st.session_state:
    st.session_state.dialog_claim = None

with st.sidebar:
    st.header("필터")
    brand = st.multiselect("브랜드", sorted(df["brand"].dropna().astype(str).unique()))
    major = st.multiselect("구분(대)", sorted(df["major"].dropna().astype(str).unique()))
    mid = st.multiselect("구분(중)", sorted(df["mid"].dropna().astype(str).unique()))
    cause = st.multiselect("원인", sorted(df["cause"].dropna().astype(str).unique()))
    claim_type = st.multiselect("유형", sorted(df["type"].dropna().astype(str).unique()))
    year = st.multiselect("년도", sorted(df["year"].dropna().astype(str).unique()))
    month = st.multiselect("월", sorted(df["month"].dropna().astype(str).unique()))
    query = st.text_input("검색", placeholder="접수번호, 모델, 하자상세, 고객명")

filtered = df.copy()
for column, selected in {"brand": brand, "major": major, "mid": mid, "cause": cause, "type": claim_type, "year": year, "month": month}.items():
    if selected:
        filtered = filtered[filtered[column].astype(str).isin(selected)]

if query:
    lowered = query.lower()
    mask = filtered.astype(str).apply(lambda col: col.str.lower().str.contains(lowered, na=False))
    filtered = filtered[mask.any(axis=1)]

total_count = len(filtered)
total_cost = float(filtered["cost"].sum())
avg_ppm = float(filtered["ppm"].mean()) if total_count else 0
completed = int((filtered["status"].astype(str) == "완료").sum())
completion_rate = (completed / total_count * 100) if total_count else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("총 건수", f"{total_count:,}건")
k2.metric("처리비용 합계", format_won(total_cost))
k3.metric("평균 PPM", f"{avg_ppm:.0f}")
k4.metric("완료율", f"{completion_rate:.1f}%")

trend = filtered.groupby("month").size().reset_index(name="건수").sort_values("month")
major_dist = filtered["major"].fillna("").astype(str)
major_dist = major_dist[major_dist != ""].value_counts(normalize=True).mul(100).reset_index()
major_dist.columns = ["구분", "비율"]

left_chart, right_chart = st.columns([2, 1])
with left_chart:
    st.subheader("월별 클레임 추이")
    if trend.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        st.line_chart(trend.set_index("month"))

with right_chart:
    st.subheader("구분(대) 비중")
    if major_dist.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        pie = alt.Chart(major_dist).mark_arc(innerRadius=45).encode(
            theta="비율:Q",
            color="구분:N",
            tooltip=["구분:N", alt.Tooltip("비율:Q", format=".1f")],
        )
        st.altair_chart(pie, use_container_width=True)
        st.dataframe(major_dist.style.format({"비율": "{:.1f}%"}), use_container_width=True, hide_index=True)

c1, c2, c3 = st.columns(3)
for column, title, target in [("cause", "원인별 현황", c1), ("brand", "브랜드별 현황", c2), ("type", "유형별 현황", c3)]:
    with target:
        st.subheader(title)
        counts = top_n(filtered, column, 8)
        if counts.empty:
            st.write("표시할 데이터가 없습니다.")
        else:
            chart = alt.Chart(counts).mark_bar().encode(
                x=alt.X("count:Q", title="건수"),
                y=alt.Y("name:N", sort="-x", title=""),
                tooltip=["name:N", "count:Q"],
            )
            st.altair_chart(chart, use_container_width=True)

left_top, right_recent = st.columns([1, 2.3])

with left_top:
    st.subheader("하자상세 TOP 10")
    detail_top = top_n(filtered, "detail", 10)
    if detail_top.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        detail_top["순위"] = range(1, len(detail_top) + 1)
        st.dataframe(detail_top[["순위", "name", "count"]], use_container_width=True, hide_index=True)

with right_recent:
    st.subheader("최근 세부내역 20건")
    recent = filtered.sort_values("date", ascending=False).head(20).reset_index(drop=True)
    if recent.empty:
        st.write("표시할 데이터가 없습니다.")
    else:
        headers = st.columns([1.1, 0.9, 1.8, 1.6, 1.6, 1.2, 1.0, 1.0, 1.1, 0.9, 1.0])
        for col, title in zip(headers, ["일자", "브랜드", "접수번호", "구분", "하자상세", "원인", "담당자", "상태", "비용", "PPM", "동작"]):
            col.markdown(f"**{title}**")

        for idx, row in recent.iterrows():
            cols = st.columns([1.1, 0.9, 1.8, 1.6, 1.6, 1.2, 1.0, 1.0, 1.1, 0.9, 1.0])
            cols[0].write(str(row["date"]))
            cols[1].write(str(row["brand"]))
            cols[2].write(str(row["claimNo"]))
            cols[3].write(f"{row['major']} / {row['mid']}")
            cols[4].write(str(row["detail"]))
            cols[5].write(str(row["cause"]))
            cols[6].write(str(row["assignee"]))
            cols[7].write(str(row["status"]))
            cols[8].write(format_won(float(row["cost"])))
            cols[9].write(f"{int(row['ppm'])}")
            if cols[10].button("상세조회", key=f"detail_{idx}_{row['claimNo']}"):
                st.session_state.dialog_claim = row["claimNo"]

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

with st.expander("원본 데이터 보기"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
