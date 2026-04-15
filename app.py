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
    "cause": "cause",
    "원인": "cause",
    "로트": "cause",
    "customer": "customer",
    "고객명": "customer",
    "현장명": "customer",
    "product": "product",
    "품명": "product",
    "부품명": "product",
    "model": "model",
    "모델": "model",
    "제품코드": "model",
    "actiondept": "actionDept",
    "담당부서": "actionDept",
    "조치부서": "actionDept",
    "qty": "qty",
    "수량": "qty",
    "cost": "cost",
    "비용": "cost",
    "금액": "cost",
    "ppm": "ppm",
    "duedate": "dueDate",
    "완료예정일": "dueDate",
    "memo": "memo",
    "메모": "memo",
    "조치내용": "memo",
    "requestdetail": "requestDetail",
    "요청내용": "requestDetail",
}

SAMPLE_RAW = [
    {
        "date": "2024-01-13",
        "brand": "일룸",
        "claimNo": "I202401130071-01",
        "type": "생산",
        "major": "시공미결",
        "mid": "가공",
        "detail": "보링불량",
        "cause": "외주(세진)",
        "customer": "송도 현장",
        "product": "측판",
        "model": "ILM-BR-07",
        "actionDept": "생산팀",
        "qty": 1,
        "cost": 76000,
        "ppm": 145,
        "dueDate": "2024-01-14",
        "memo": "가공 치공구 점검",
    },
    {
        "date": "2024-01-12",
        "brand": "데스커",
        "claimNo": "D202401120061-01",
        "type": "생산불만",
        "major": "고객불만",
        "mid": "외관",
        "detail": "이물질",
        "cause": "외주(올품)",
        "customer": "하남 현장",
        "product": "상판",
        "model": "DS-TOP-88",
        "actionDept": "구매팀",
        "qty": 1,
        "cost": 98000,
        "ppm": 162,
        "dueDate": "2024-01-13",
        "memo": "외주 청정관리 요청",
    },
    {
        "date": "2024-01-11",
        "brand": "퍼시스",
        "claimNo": "F202401110051-01",
        "type": "생산불만",
        "major": "고객불만",
        "mid": "자재",
        "detail": "색상불일치",
        "cause": "외주(제일)",
        "customer": "김포 현장",
        "product": "도장부품",
        "model": "PSC-COLOR-11",
        "actionDept": "구매팀",
        "qty": 1,
        "cost": 112000,
        "ppm": 176,
        "dueDate": "2024-01-12",
        "memo": "색상 기준 샘플 재배포",
    },
    {
        "date": "2024-01-10",
        "brand": "일룸",
        "claimNo": "I202401100041-01",
        "type": "생산",
        "major": "시공미결",
        "mid": "포장",
        "detail": "포장누락",
        "cause": "외주(에픽)",
        "customer": "용인 현장",
        "product": "부품박스",
        "model": "ILM-PK-01",
        "actionDept": "물류팀",
        "qty": 1,
        "cost": 42000,
        "ppm": 119,
        "dueDate": "2024-01-11",
        "memo": "외주 포장 기준 전달",
    },
    {
        "date": "2024-01-09",
        "brand": "데스커",
        "claimNo": "D202401090031-01",
        "type": "생산불만",
        "major": "고객불만",
        "mid": "외관",
        "detail": "스크래치",
        "cause": "외주(유진)",
        "customer": "분당 현장",
        "product": "서랍 전면",
        "model": "DS-FR-10",
        "actionDept": "구매팀",
        "qty": 2,
        "cost": 93000,
        "ppm": 158,
        "dueDate": "2024-01-10",
        "memo": "입고검사 강화 필요",
    },
    {
        "date": "2024-01-08",
        "brand": "퍼시스",
        "claimNo": "F202401080021-01",
        "type": "생산불만",
        "major": "고객불만",
        "mid": "자재",
        "detail": "표면 찍힘",
        "cause": "외주(송아)",
        "customer": "서초 현장",
        "product": "도어",
        "model": "PSC-DOOR-01",
        "actionDept": "구매팀",
        "qty": 1,
        "cost": 87000,
        "ppm": 148,
        "dueDate": "2024-01-09",
        "memo": "외주업체 재작업 요청",
    },
    {
        "date": "2024-01-07",
        "brand": "일룸",
        "claimNo": "I202401070012-01",
        "type": "생산",
        "major": "시공미결",
        "mid": "가공",
        "detail": "루타가공불량",
        "cause": "3라인",
        "customer": "일룸 가구 현장",
        "product": "상판",
        "model": "ILM-RT-22",
        "actionDept": "생산팀",
        "qty": 1,
        "cost": 61000,
        "ppm": 132,
        "dueDate": "2024-01-08",
        "memo": "가공조건 재점검",
    },
    {
        "date": "2024-01-06",
        "brand": "일룸",
        "claimNo": "I202401060011-01",
        "type": "생산불만",
        "major": "고객불만",
        "mid": "외관",
        "detail": "이물질",
        "cause": "4라인",
        "customer": "일룸 서재 현장",
        "product": "상판",
        "model": "ILM-TOP-01",
        "actionDept": "생산팀",
        "qty": 1,
        "cost": 92000,
        "ppm": 154,
        "dueDate": "2024-01-07",
        "memo": "외관 검사 강화",
    },
]


def inject_style() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f8fafc 0%, #eef4fb 100%); }
        .block-container { max-width: 1480px; padding-top: 1.5rem; padding-bottom: 2rem; }
        .hero-card {
            background: linear-gradient(135deg, #172033 0%, #243246 60%, #35465f 100%);
            border-radius: 28px; padding: 28px 32px; color: white;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
            margin-bottom: 1.5rem;
        }
        .hero-pill {
            display: inline-block; padding: 8px 14px; border-radius: 999px;
            background: rgba(255,255,255,0.12); font-size: 13px; font-weight: 700;
        }
        .hero-title { font-size: 34px; font-weight: 800; margin: 18px 0 10px; letter-spacing: -0.02em; }
        .hero-desc { color: #dbe6f5; font-size: 15px; line-height: 1.7; margin: 0; }
        .section-card, .kpi-card, .chart-card, .top-card, .table-card {
            background: white; border-radius: 24px; box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
        }
        .section-card { padding: 18px 20px 8px; margin-bottom: 1.35rem; }
        .section-title { font-size: 18px; font-weight: 800; color: #0f172a; }
        .section-desc { font-size: 13px; color: #64748b; margin-top: 3px; }
        .kpi-card { padding: 18px 18px 16px; min-height: 140px; }
        .kpi-label { color: #64748b; font-size: 14px; margin-bottom: 8px; }
        .kpi-value { color: #0f172a; font-size: 28px; font-weight: 800; line-height: 1.2; letter-spacing: -0.02em; }
        .kpi-desc { color: #64748b; font-size: 12px; margin-top: 6px; }
        .trend-pill {
            margin-top: 12px; display: inline-block; padding: 6px 10px; border-radius: 999px;
            font-size: 12px; font-weight: 700; color: #dc2626; background: #fee2e2;
        }
        .chart-card, .top-card, .table-card { padding: 16px 16px 12px; }
        .card-title { font-size: 17px; font-weight: 800; color: #0f172a; margin-bottom: 8px; }
        .top-item {
            display: flex; align-items: center; justify-content: space-between; gap: 12px;
            background: #edf3fb; border-radius: 22px; padding: 14px 16px; margin-bottom: 12px;
        }
        .rank-badge {
            width: 34px; height: 34px; border-radius: 999px; background: #0f172a; color: white;
            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 14px;
            flex-shrink: 0;
        }
        .top-name { font-weight: 800; color: #0f172a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .count-badge {
            border-radius: 999px; padding: 7px 12px; border: 1px solid #cbd5e1; background: white;
            font-size: 13px; font-weight: 700; color: #0f172a; white-space: nowrap;
        }
        .detail-box {
            background: white; border-radius: 24px; box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            padding: 18px 20px; margin-top: 16px;
        }
        .detail-grid {
            display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px;
        }
        .detail-label { font-size: 12px; color: #64748b; }
        .detail-value { font-size: 14px; color: #0f172a; font-weight: 700; }
        .request-box {
            margin-top: 14px; background: #f8fafc; border-radius: 18px; padding: 16px;
            color: #334155; line-height: 1.7; font-size: 14px; white-space: pre-wrap;
        }
        div[data-testid="stFileUploader"] section { padding: 0.4rem 0.6rem; }
        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label { font-weight: 700 !important; color: #334155 !important; }
        button[kind="secondary"], button[kind="primary"] { border-radius: 999px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt(n: float | int) -> str:
    return f"{int(n or 0):,}"


def pct(n: float) -> str:
    return f"{n:.1f}%"


def normalize_row(row: dict, idx: int = 0) -> dict:
    date = str(row.get("date") or "")
    normalized = {
        "date": date,
        "brand": str(row.get("brand") or ""),
        "claimNo": str(row.get("claimNo") or f"CLAIM-{idx+1:04d}"),
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
    result = []
    for col in columns:
        key = str(col).strip().replace(" ", "").lower()
        result.append(HEADER_MAP.get(key, str(col).strip()))
    return result


def detect_header_row(frame: pd.DataFrame) -> int:
    for idx in range(min(len(frame), 10)):
        values = [str(v).strip() for v in frame.iloc[idx].tolist()]
        hits = 0
        for value in values:
            key = value.replace(" ", "").lower()
            if key in HEADER_MAP:
                hits += 1
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
            score = 0
            for value in header_values:
                if value.replace(" ", "").lower() in HEADER_MAP:
                    score += 1
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
    clean = clean.dropna(how="all")
    clean = clean.fillna("")

    if "date" not in clean.columns:
        raise ValueError("반영할 행을 찾지 못했습니다. 헤더와 데이터 형식을 확인해 주세요.")

    rows = []
    for idx, record in enumerate(clean.to_dict(orient="records")):
        date = str(record.get("date") or "").strip()
        if not date:
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


def filter_options(rows: list[dict], key: str) -> list[str]:
    return [ALL] + sorted({str(row.get(key) or "") for row in rows if str(row.get(key) or "")})


def top_n(rows: list[dict], key: str, limit: int) -> pd.DataFrame:
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row.get(key) or "")
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return pd.DataFrame(ordered, columns=["name", "value"])


def render_kpi(title: str, value: str, desc: str, trend: str | None = None) -> None:
    trend_html = f'<div class="trend-pill">{trend}</div>' if trend else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-desc">{desc}</div>
            {trend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_top_detail(frame: pd.DataFrame) -> None:
    st.markdown('<div class="top-card"><div class="card-title">하자상세 TOP 10</div>', unsafe_allow_html=True)
    if frame.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
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
    st.markdown("</div>", unsafe_allow_html=True)


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


def show_detail(row: dict) -> None:
    st.markdown('<div class="detail-box">', unsafe_allow_html=True)
    st.markdown(f"### 클레임 상세 관리")
    st.caption(f"{row['claimNo']} / {row['brand']} / {row['date']}")
    st.markdown('<div class="detail-grid">', unsafe_allow_html=True)

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
    if st.button("상세창 닫기", key="close_detail"):
        st.session_state.selected_claim = None
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


inject_style()
ensure_state()
rows = st.session_state.rows

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-pill">품질보증팀 고객클레임 관리</div>
        <div class="hero-title">고객클레임 현황 관리 대시보드</div>
        <p class="hero-desc">고객 클레임 접수, 원인, 처리상태, 비용, PPM을 한눈에 확인할 수 있도록 구성한 화면입니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-card">', unsafe_allow_html=True)
top_left, top_right = st.columns([6, 4])
with top_left:
    st.markdown('<div class="section-title">조회 조건</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">엑셀 또는 CSV 업로드로 데이터를 추가하거나 교체할 수 있습니다.</div>', unsafe_allow_html=True)
with top_right:
    c1, c2, c3 = st.columns(3)
    if c1.button("필터 초기화", use_container_width=True):
        st.rerun()
    if c2.button("샘플 복원", use_container_width=True):
        st.session_state.rows = sample_rows()
        st.session_state.selected_claim = None
        st.rerun()
    uploaded_file = c3.file_uploader("엑셀 데이터 넣기", type=["csv", "xls", "xlsx"], label_visibility="collapsed")
    if uploaded_file is not None:
        try:
            imported_rows = frame_to_rows(read_uploaded_frame(uploaded_file))
            st.session_state.rows = imported_rows
            st.session_state.selected_claim = None
            st.success(f"{len(imported_rows)}건을 반영했습니다.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

filter_cols = st.columns(6)
brand = filter_cols[0].selectbox("브랜드", filter_options(rows, "brand"))
major = filter_cols[1].selectbox("구분(대)", filter_options(rows, "major"))
mid = filter_cols[2].selectbox("구분(중)", filter_options(rows, "mid"))
cause = filter_cols[3].selectbox("원인", filter_options(rows, "cause"))
type_value = filter_cols[4].selectbox("유형", filter_options(rows, "type"))
year = filter_cols[5].selectbox("년도", filter_options(rows, "year"))

sub_cols = st.columns([1, 1, 2.6])
month = sub_cols[0].selectbox("월", filter_options(rows, "month"))
day = sub_cols[1].selectbox("일", filter_options(rows, "day"))
search = sub_cols[2].text_input("검색", placeholder="접수번호, 모델, 하자상세, 고객명 검색")
st.markdown("</div>", unsafe_allow_html=True)

filtered = []
query = search.strip().lower()
for row in rows:
    haystack = " ".join(
        [
            row["claimNo"],
            row["customer"],
            row["product"],
            row["model"],
            row["detail"],
            row["cause"],
            row["memo"],
        ]
    ).lower()
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

monthly_all = top_n(rows, "month", 20)
latest = int(monthly_all.iloc[0]["value"]) if not monthly_all.empty else 0
prev = int(monthly_all.iloc[1]["value"]) if len(monthly_all) > 1 else 0
delta = latest - prev

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    render_kpi("총 클레임 건수", f"{fmt(total_count)}건", "현재 조건 기준 접수 건수", f"전월 대비 {delta:+d}건")
with k2:
    render_kpi("미완료 건수", f"{fmt(open_count)}건", "접수 · 분석 · 조치중 포함")
with k3:
    render_kpi("완료율", pct(completion_rate), "완료 상태 기준 처리율")
with k4:
    render_kpi("처리비용 합계", f"{fmt(total_cost)}원", "선택 조건 기준 누적 비용")
with k5:
    render_kpi("평균 PPM", f"{avg_ppm:.0f}", "선택 조건 기준 평균 수준")

monthly = pd.DataFrame(filtered)
if monthly.empty:
    monthly = pd.DataFrame(columns=["month", "claimNo"])

monthly_trend = (
    monthly.groupby("month", as_index=False)
    .agg(count=("claimNo", "count"))
    .sort_values("month")
)
major_pie = top_n(filtered, "major", 6)
cause_top = top_n(filtered, "cause", 6)
brand_top = top_n(filtered, "brand", 6)
type_top = top_n(filtered, "type", 6)
detail_top = top_n(filtered, "detail", 10)
recent_df = (
    pd.DataFrame(filtered)
    .sort_values("date", ascending=False)
    .head(20)
    if filtered
    else pd.DataFrame()
)

left, right = st.columns([1.8, 1.0])
with left:
    st.markdown('<div class="chart-card"><div class="card-title">월별 클레임 추이</div>', unsafe_allow_html=True)
    if monthly_trend.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        line = (
            alt.Chart(monthly_trend)
            .mark_line(point=alt.OverlayMarkDef(size=70, filled=True, color="#2563eb"), color="#2563eb", strokeWidth=3)
            .encode(
                x=alt.X("month:N", title=""),
                y=alt.Y("count:Q", title="", axis=alt.Axis(tickMinStep=1)),
                tooltip=[alt.Tooltip("month:N", title="월"), alt.Tooltip("count:Q", title="건수")],
            )
            .properties(height=310)
        )
        st.altair_chart(line, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="chart-card"><div class="card-title">구분(대) 비중</div>', unsafe_allow_html=True)
    if major_pie.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        pie_source = major_pie.copy()
        pie_source["label"] = pie_source["name"] + " " + pie_source["value"].astype(str) + "건"
        donut = (
            alt.Chart(pie_source)
            .mark_arc(innerRadius=55, outerRadius=110)
            .encode(
                theta=alt.Theta("value:Q"),
                color=alt.Color("name:N", scale=alt.Scale(range=["#2f64df", "#f59e0b", "#10b981", "#ef4444"])),
                tooltip=[
                    alt.Tooltip("name:N", title="구분"),
                    alt.Tooltip("value:Q", title="건수"),
                    alt.Tooltip("value:Q", title="비중", format=".1%"),
                ],
            )
            .properties(height=310)
        )
        st.altair_chart(donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

b1, b2, b3 = st.columns(3)
for column, title, frame, color in [
    (b1, "원인별 현황", cause_top, "#2563eb"),
    (b2, "브랜드별 현황", brand_top, "#10b981"),
    (b3, "유형별 현황", type_top, "#f59e0b"),
]:
    with column:
        st.markdown(f'<div class="chart-card"><div class="card-title">{title}</div>', unsafe_allow_html=True)
        if frame.empty:
            st.info("표시할 데이터가 없습니다.")
        else:
            bars = (
                alt.Chart(frame)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color=color)
                .encode(
                    x=alt.X("name:N", sort=None, title=""),
                    y=alt.Y("value:Q", title="", axis=alt.Axis(tickMinStep=1)),
                    tooltip=[alt.Tooltip("name:N", title="구분"), alt.Tooltip("value:Q", title="건수")],
                )
                .properties(height=260)
            )
            labels = bars.mark_text(dy=-8, color="#334155").encode(text="value:Q")
            st.altair_chart(bars + labels, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

t1, t2 = st.columns([0.95, 2.05])
with t1:
    render_top_detail(detail_top)

with t2:
    st.markdown('<div class="table-card"><div class="card-title">최근 세부내역 20건</div>', unsafe_allow_html=True)
    if recent_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        header = st.columns([1.1, 0.9, 1.7, 1.3, 1.1, 1.1, 0.9, 0.9, 0.9, 0.7, 0.9])
        labels = ["일자", "브랜드", "접수번호", "구분", "하자상세", "원인", "담당자", "상태", "비용", "PPM", "동작"]
        for col, label in zip(header, labels):
            col.markdown(f"**{label}**")

        for _, row in recent_df.iterrows():
            cols = st.columns([1.1, 0.9, 1.7, 1.3, 1.1, 1.1, 0.9, 0.9, 0.9, 0.7, 0.9])
            cols[0].write(str(row["date"]))
            cols[1].write(str(row["brand"]))
            cols[2].write(f"**{row['claimNo']}**")
            cols[3].write(f"{row['major']} / {row['mid']}")
            cols[4].write(str(row["detail"]))
            cols[5].write(str(row["cause"]))
            cols[6].write(str(row["assignee"]))
            cols[7].write(str(row["status"]))
            cols[8].write(f"{fmt(row['cost'])}원")
            cols[9].write(str(row["ppm"]))
            if cols[10].button("상세조회", key=f"detail_{row['claimNo']}"):
                st.session_state.selected_claim = row.to_dict()
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

selected = st.session_state.selected_claim
if selected:
    show_detail(selected)
