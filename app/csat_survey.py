"""Khao sat CSAT (muc do hai long) ve chat luong dich vu CSKH qua Zalo - nguoi dung yeu cau
2026-08-28 "tao 1 form de gui khach hang danh gia chat luong dich vu qua Zalo, thong ke do luong
hieu qua dich vu". 5 tieu chi (nguoi dung tu chon khi duoc hoi, khong phai suy doan):
  1. Chat luong dich vu (giao nhan dung cam ket - thoi gian, tinh trang hang)
  2. Nhan vien ho tro (thai do, su nhiet tinh/chuyen nghiep khi trao doi qua Zalo)
  3. Cham soc khach hang - CSKH (phan hoi nhanh, giai quyet dung van de)
  4. Uu dai (chuong trinh khuyen mai co hap dan/phu hop khong)
  5. Giao dien app/web (de tra cuu, de thao tac)
Moi tieu chi cham 1-5 sao, kem 1 o gop y tu do (khong bat buoc).

**2026-08-29 - DOI LUU TRU tu file JSON tren dia sang Supabase (Postgres qua REST API cua
PostgREST)**, sau khi phat hien 2 phieu khao sat that cua nguoi dung bi MAT tren Render free tier -
dung dung nhu README.md da canh bao truoc: dia free tier la ephemeral, mat sach khi service
redeploy/khoi dong lai. Nguoi dung chon Supabase (mien phi) thay vi nang cap Render len goi tra phi
co dia ben. Xem README.md muc "Thiet lap Supabase" de biet cach tao bang + lay SUPABASE_URL/
SUPABASE_KEY. Neu 2 bien moi truong nay CHUA duoc dat, moi ham goi Cong du lieu se raise
StorageNotConfigured ro rang (khong am tham roi ve file JSON cu nua - da xoa han co che do, tranh
lap lai dung bay "tuong da luu nhung thuc ra khong" mot lan nua).

KHONG co su kien "dong ticket ho tro" TU DONG trong he thong hien tai (tab "Kenh cho ho tro" -
frontend/tabs/07-cho-ho-tro - chi la hang doi giam sat, chua co vong doi ticket/trang thai
resolved) - nen "gui khao sat" o day la HANH DONG THU CONG: agent CSKH tu bam "Gui khao sat" cho
1 khach (trong tab moi frontend/report/khao-sat-cskh-dark.html) khi ho coi cuoc trao doi da xong,
thay vi tu dong bam theo 1 event he thong. Xem thread quyet dinh nay trong memory du an
(project_carepilot_csat_survey)."""

import os
import secrets
from datetime import datetime, timezone

import httpx

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or ""
TABLE = "csat_surveys"

# Thu tu CO Y NGHIA: dung lam thu tu hien thi ca o form khao sat (khach thay) lan o dashboard
# thong ke (agent thay) - sua nhan/hint o day se doi dong loat ca 2 noi, khong can sua lap.
CRITERIA = [
    {
        "key": "chat_luong_dich_vu",
        "label": "Chất lượng dịch vụ",
        "hint": "Đơn hàng được xử lý, giao nhận có đúng như cam kết (thời gian, tình trạng hàng) không?",
    },
    {
        "key": "nhan_vien_ho_tro",
        "label": "Nhân viên hỗ trợ",
        "hint": "Thái độ, sự nhiệt tình và chuyên nghiệp của nhân viên khi trao đổi qua Zalo.",
    },
    {
        "key": "cskh",
        "label": "Chăm sóc khách hàng (CSKH)",
        "hint": "Mức độ phản hồi nhanh chóng, giải quyết đúng vấn đề bạn gặp phải.",
    },
    {
        "key": "uu_dai",
        "label": "Ưu đãi",
        "hint": "Các chương trình khuyến mãi, ưu đãi dành cho khách hàng có hấp dẫn, phù hợp không?",
    },
    {
        "key": "giao_dien_app_web",
        "label": "Giao diện app/web",
        "hint": "Trải nghiệm sử dụng ứng dụng/website GHN (dễ tra cứu, dễ thao tác).",
    },
]
CRITERIA_KEYS = [c["key"] for c in CRITERIA]


class SurveyNotFound(Exception):
    pass


class SurveyAlreadySubmitted(Exception):
    pass


class InvalidScores(Exception):
    pass


class StorageNotConfigured(Exception):
    """SUPABASE_URL/SUPABASE_KEY chua duoc dat trong bien moi truong - xem README.md."""


class StorageError(Exception):
    """Supabase tra loi bat thuong (mang loi, sai quyen, bang chua ton tai...) - forward nguyen
    van thong diep, khong nuot loi im lang (im lang chinh la nguyen nhan lam mat du lieu that
    truoc do ma khong ai biet cho toi khi kiem tra thu cong)."""


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise StorageNotConfigured(
            "Chưa cấu hình SUPABASE_URL/SUPABASE_KEY (biến môi trường trên Render) — xem README.md mục \"Thiết lập Supabase\"."
        )
    return httpx.Client(
        base_url=SUPABASE_URL + "/rest/v1",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )


def _raise_for_status(r):
    if r.status_code >= 400:
        raise StorageError(f"Supabase trả lỗi {r.status_code}: {r.text[:300]}")


def create_survey(customer_id, customer_name, phone=None, zalo_user_id=None, context_label=None):
    """Tao 1 khao sat o trang thai 'pending', tra ve record vua tao (co token dung de
    dung link cong khai /csat/survey/<token>)."""
    token = secrets.token_urlsafe(16)
    payload = {
        "token": token,
        "customer_id": None if customer_id is None else str(customer_id),
        "customer_name": customer_name,
        "phone": phone,
        "zalo_user_id": zalo_user_id,
        "context_label": context_label or "",
        "status": "pending",
    }
    with _client() as c:
        r = c.post(f"/{TABLE}", json=payload, headers={"Prefer": "return=representation"})
        _raise_for_status(r)
        return r.json()[0]


def log_open_send(count=1):
    """Ghi nhan nguoi dung 'da gui' link khao sat dung chung ra ngoai (Zalo, tin nhan...) -
    THEM 2026-08-29 theo yeu cau nguoi dung "co cach nao biet toi da gui bao nhieu link khong".
    Viec dan link vao Zalo la HANH DONG THU CONG ben ngoai he thong nen KHONG THE tu dong dem duoc
    - day la giai phap thay the: nguoi dung tu bam nut ghi nhan sau moi dot gui (xem
    khao-sat-cskh-dark.html), tao (count) ban ghi 'pending' danh dau (KHONG co scores, KHONG hien
    trong bang phan hoi/danh sach diem thap vi cac cho do deu loc status=='completed'), nhung VAN
    duoc summary() dem vao total_sent (dem theo created_at, khong loc status) -> tu do tinh duoc
    response_rate = so nguoi da dien / so lan da bam gui, dung y nghia "ty le phan hoi" that su.

    count: THEM 2026-08-29 sau phan hoi nguoi dung "tôi vừa gửi 100 khách, do share người này qua
    người khác, chỉ copy 1 lần thôi" - 1 lan COPY link co the duoc CHUYEN TIEP toi nhieu nguoi
    (forward qua Zalo), nen khong the gia dinh "1 lan bam nut = 1 nguoi nhan". Cho phep nguoi dung
    tu nhap so nguoi THAT SU da nhan duoc link trong dot gui do, tao dung tung ay ban ghi danh dau
    trong 1 lan goi Supabase (bulk insert qua PostgREST - gui 1 mang thay vi 1 object)."""
    count = max(1, min(int(count), 5000))  # chan hop ly, tranh nhap nham 1 so khong lo

    def _marker():
        return {
            "token": secrets.token_urlsafe(16),
            "customer_id": None,
            "customer_name": None,
            "phone": None,
            "zalo_user_id": None,
            "context_label": "open-link-sent-marker",
            "status": "pending",
        }

    # Gui thanh nhieu lo NHO (<=50/lo) thay vi 1 mang lon duy nhat - da THAY THUC TE mot lan gui
    # count=100 chi tao ra ~35 ban ghi (khong ro nguyen nhan chinh xac - co the do gioi han/timeout
    # phia Supabase free tier khi POST 1 mang lon), trong khi lo 10 thi luon dung du. Chia lo nho
    # giam rui ro mat ban ghi giua chung khi nguoi dung nhap so lon (vd gui hang loat cho 100+
    # khach qua forward Zalo).
    CHUNK = 50
    inserted = []
    with _client() as c:
        remaining = count
        while remaining > 0:
            batch_size = min(CHUNK, remaining)
            payload = [_marker() for _ in range(batch_size)]
            r = c.post(f"/{TABLE}", json=payload, headers={"Prefer": "return=representation"})
            _raise_for_status(r)
            rows = r.json()
            if len(rows) != batch_size:
                raise StorageError(
                    f"Supabase chỉ nhận {len(rows)}/{batch_size} bản ghi trong 1 lô — dữ liệu có thể chưa đầy đủ, thử lại với số nhỏ hơn."
                )
            inserted.extend(rows)
            remaining -= batch_size
    return inserted


def get_survey(token):
    with _client() as c:
        r = c.get(f"/{TABLE}", params={"token": f"eq.{token}", "limit": 1})
        _raise_for_status(r)
        rows = r.json()
        return rows[0] if rows else None


def add_open_response(scores, comment, reasons=None, customer_name=None, phone=None):
    """THEM 2026-08-29: khac voi create_survey()+submit_survey() (1 token = 1 khach, dung 1
    lan roi khoa lai "da danh gia") - ham nay phuc vu 1 LINK DUNG CHUNG gui cho TAT CA khach
    (nguoi dung yeu cau "chi can gui link khao sat cho khach, khach nao dien thi thong ke tra
    ve"), ai bam vao cung thay form trong, cung nop duoc, khong bi chan boi trang thai
    "da hoan thanh" cua nguoi truoc. Validate diem giong het submit_survey(), chi khac la
    KHONG can token/pending truoc - tao thang 1 ban ghi 'completed' hoan chinh.
    customer_name/phone: ca 2 deu KHONG bat buoc (link dung chung khong the ep khach phai dien
    danh tinh), rong thi dung placeholder "Khach qua link khao sat".
    Xem GET/POST /csat/survey-open trong main.py."""
    missing = [k for k in CRITERIA_KEYS if k not in scores]
    if missing:
        raise InvalidScores(f"Thiếu điểm cho tiêu chí: {', '.join(missing)}")
    for k, v in scores.items():
        if k not in CRITERIA_KEYS:
            raise InvalidScores(f"Tiêu chí không hợp lệ: {k}")
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise InvalidScores(f"Điểm '{k}' phải là số nguyên 1-5")

    clean_reasons = {}
    if reasons:
        for k, text in reasons.items():
            if k in CRITERIA_KEYS and scores.get(k, 5) <= 3 and isinstance(text, str) and text.strip():
                clean_reasons[k] = text.strip()[:500]

    now = _now_iso()
    clean_name = (customer_name or "").strip()[:120]
    clean_phone = (phone or "").strip()[:30]
    payload = {
        "token": secrets.token_urlsafe(16),
        "customer_id": None,
        "customer_name": clean_name or "Khách qua link khảo sát",
        "phone": clean_phone or None,
        "zalo_user_id": None,
        "context_label": "open-link",  # danh dau nguon: tu link dung chung, khong phai tu 1 luot gui rieng
        "created_at": now,
        "status": "completed",
        "scores": {k: scores[k] for k in CRITERIA_KEYS},
        "comment": (comment or "").strip()[:2000],
        "reasons": clean_reasons or None,
        "submitted_at": now,
    }
    with _client() as c:
        r = c.post(f"/{TABLE}", json=payload, headers={"Prefer": "return=representation"})
        _raise_for_status(r)
        return r.json()[0]


def submit_survey(token, scores, comment, reasons=None):
    record = get_survey(token)
    if not record:
        raise SurveyNotFound(token)
    if record["status"] == "completed":
        raise SurveyAlreadySubmitted(token)

    missing = [k for k in CRITERIA_KEYS if k not in scores]
    if missing:
        raise InvalidScores(f"Thiếu điểm cho tiêu chí: {', '.join(missing)}")
    for k, v in scores.items():
        if k not in CRITERIA_KEYS:
            raise InvalidScores(f"Tiêu chí không hợp lệ: {k}")
        if not isinstance(v, int) or not (1 <= v <= 5):
            raise InvalidScores(f"Điểm '{k}' phải là số nguyên 1-5")

    # reasons: {tieu_chi_key: ly_do_text} - CHI luu cho tieu chi thuc su <=3 sao (khong tin tuong
    # nguyen si input tu client - loc lai o day, phong truong hop client gui du lieu khong khop).
    clean_reasons = {}
    if reasons:
        for k, text in reasons.items():
            if k in CRITERIA_KEYS and scores.get(k, 5) <= 3 and isinstance(text, str) and text.strip():
                clean_reasons[k] = text.strip()[:500]

    patch = {
        "scores": {k: scores[k] for k in CRITERIA_KEYS},
        "comment": (comment or "").strip()[:2000],  # chan do dai hop ly, tranh 1 khach spam qua to
        "reasons": clean_reasons or None,
        "status": "completed",
        "submitted_at": _now_iso(),
    }
    with _client() as c:
        r = c.patch(f"/{TABLE}", params={"token": f"eq.{token}"}, json=patch, headers={"Prefer": "return=representation"})
        _raise_for_status(r)
        rows = r.json()
        return rows[0] if rows else {**record, **patch}


def list_surveys():
    """Toan bo khao sat (ca pending lan completed), moi gui/tao truoc len dau."""
    with _client() as c:
        r = c.get(f"/{TABLE}", params={"order": "created_at.desc", "limit": 10000})
        _raise_for_status(r)
        return r.json()


def _in_range(iso_str, start, end):
    if not iso_str:
        return False
    d = iso_str[:10]  # 'YYYY-MM-DD' - so sanh dang string la du, cung kieu voi cac module khac trong du an
    if start and d < start:
        return False
    if end and d > end:
        return False
    return True


def summary(start=None, end=None):
    """Thong ke hieu qua dich vu cho frontend/report/khao-sat-cskh-dark.html:
    - response_rate: % khao sat DA GUI (created_at trong ky) da duoc khach tra loi
    - avg_overall + avg_by_criterion: diem trung binh 1-5 (chi tinh tren khao sat DA TRA LOI,
      submitted_at trong ky)
    - trend: diem trung binh tong theo ngay (submitted_at trong ky) - de ve bieu do xu huong
    - low_score: danh sach khao sat co diem trung binh < 3 (can chu y) - deu tinh tren completed
      trong ky, sap moi nhat len dau
    Khong loc theo start/end thi lay TOAN BO lich su. Logic tinh toan ben duoi GIU NGUYEN 100% so
    voi ban luu file JSON truoc day - chi khac nguon `rows` (gio doc tu list_surveys()/Supabase
    thay vi _load()["surveys"].values())."""
    rows = list_surveys()

    sent_in_range = [r for r in rows if _in_range(r["created_at"], start, end)] if (start or end) else rows
    completed_in_range = (
        [r for r in rows if r["status"] == "completed" and _in_range(r["submitted_at"], start, end)]
        if (start or end)
        else [r for r in rows if r["status"] == "completed"]
    )

    total_sent = len(sent_in_range)
    total_completed = len(completed_in_range)
    response_rate = round(total_completed / total_sent * 100, 1) if total_sent else 0.0

    avg_by_criterion = {}
    for key in CRITERIA_KEYS:
        vals = [r["scores"][key] for r in completed_in_range if r.get("scores")]
        avg_by_criterion[key] = round(sum(vals) / len(vals), 2) if vals else None

    overall_vals = []
    for r in completed_in_range:
        if r.get("scores"):
            overall_vals.append(sum(r["scores"].values()) / len(r["scores"]))
    avg_overall = round(sum(overall_vals) / len(overall_vals), 2) if overall_vals else None

    trend_map = {}  # 'YYYY-MM-DD' -> [sum, count]
    for r in completed_in_range:
        if not r.get("scores") or not r.get("submitted_at"):
            continue
        day = r["submitted_at"][:10]
        overall = sum(r["scores"].values()) / len(r["scores"])
        entry = trend_map.setdefault(day, [0.0, 0])
        entry[0] += overall
        entry[1] += 1
    trend = [
        {"date": day, "avg_overall": round(total / count, 2), "count": count}
        for day, (total, count) in sorted(trend_map.items())
    ]

    low_score = []
    for r in completed_in_range:
        if not r.get("scores"):
            continue
        overall = sum(r["scores"].values()) / len(r["scores"])
        if overall < 3:
            low_score.append({**r, "avg_overall": round(overall, 2)})
    low_score.sort(key=lambda r: r["submitted_at"], reverse=True)

    recent = sorted(completed_in_range, key=lambda r: r["submitted_at"], reverse=True)[:20]
    recent = [
        {**r, "avg_overall": round(sum(r["scores"].values()) / len(r["scores"]), 2)}
        for r in recent
        if r.get("scores")
    ]

    # Xep hang ly do khong hai long THEO TUNG tieu chi - Gom theo CHUOI TRUNG KHOP TUYET DOI sau
    # khi chuan hoa (strip + hoa/thuong + gop khoang trang lien tiep) - KHONG phai gom theo y
    # nghia/NLP (khong co model that dung o day, tranh bia ra 1 "phan loai chu de" khong that su
    # ton tai). Neu nhieu khach viet CUNG 1 cau y het nhau thi "count" > 1 phan anh dung tan suat
    # that; neu tat ca deu viet khac nhau thi day chi la danh sach theo thoi gian, moi dong count=1.
    reasons_by_criterion = {}
    for key in CRITERIA_KEYS:
        buckets = {}  # chuoi da chuan hoa -> {"text": ban goc dau tien gap, "count", "last_seen", "score_sum"}
        for r in completed_in_range:
            reasons = r.get("reasons") or {}
            raw = reasons.get(key)
            if not raw:
                continue
            norm = " ".join(raw.strip().lower().split())
            if not norm:
                continue
            b = buckets.setdefault(norm, {"text": raw.strip(), "count": 0, "last_seen": None, "score_sum": 0})
            b["count"] += 1
            b["score_sum"] += (r.get("scores") or {}).get(key, 0)
            if not b["last_seen"] or r["submitted_at"] > b["last_seen"]:
                b["last_seen"] = r["submitted_at"]
        crit_rows = [
            {"text": b["text"], "count": b["count"], "last_seen": b["last_seen"], "avg_score": round(b["score_sum"] / b["count"], 2)}
            for b in buckets.values()
        ]
        # count giam dan (ly do lap lai nhieu nhat len dau); cung count thi last_seen giam dan (moi nhat truoc).
        crit_rows.sort(key=lambda x: (x["count"], x["last_seen"] or ""), reverse=True)
        reasons_by_criterion[key] = crit_rows

    # Xep hang 5 tieu chi tu THAP -> CAO (2026-08-29, yeu cau nguoi dung "trong 5 tieu chi, dau
    # la tieu chi co so diem thap nhat, xep hang giup toi") - KPI "Tieu chi thap nhat" cu chi hien
    # 1 tieu chi, day la BANG XEP HANG DAY DU ca 5. avg=None (chua co du lieu) luon xep CUOI, khong
    # coi la "thap nhat" (khong bia so 0 cho tieu chi chua ai cham).
    criteria_ranking = []
    for c in CRITERIA:
        key = c["key"]
        avg = avg_by_criterion.get(key)
        count_low = sum(
            1 for r in completed_in_range
            if r.get("scores") and r["scores"].get(key) is not None and r["scores"][key] <= 3
        )
        criteria_ranking.append({
            "key": key, "label": c["label"], "avg": avg, "count_low": count_low,
        })
    criteria_ranking.sort(key=lambda x: (x["avg"] is None, x["avg"] if x["avg"] is not None else 0))
    best_avg = next((x["avg"] for x in criteria_ranking if x["avg"] is not None), None)
    for i, x in enumerate(criteria_ranking):
        x["rank"] = i + 1
        x["gap_from_best"] = round(best_avg - x["avg"], 2) if (best_avg is not None and x["avg"] is not None) else None

    # Chi tiet tung phieu cham THAP (<=3 sao) THEO TUNG tieu chi - THEM 2026-08-31 theo yeu cau
    # nguoi dung "Moi tieu chi se co muc xem chi tiet, bam vao se hien thi chi tiet cac phieu cua
    # khach nao danh gia te phan do". Khac voi reasons_by_criterion o tren (gom theo NOI DUNG ly do
    # trung khop, mat danh tinh tung khach) - day la DANH SACH TUNG PHIEU rieng le (ten khach, ngay,
    # diem so, ly do/gop y CHINH khach do viet), sap moi nhat len dau, gioi han 20 dong/tieu chi
    # giong cac danh sach khac trong file nay (tranh payload phinh to khi du lieu nhieu).
    low_score_by_criterion = {}
    for c in CRITERIA:
        key = c["key"]
        rows = []
        for r in completed_in_range:
            scores = r.get("scores") or {}
            sc = scores.get(key)
            if sc is None or sc > 3:
                continue
            rows.append({
                "customer_name": r.get("customer_name") or "Khách qua link khảo sát",
                "phone": r.get("phone"),
                "submitted_at": r.get("submitted_at"),
                "score": sc,
                "reason": (r.get("reasons") or {}).get(key),
                "comment": r.get("comment"),
            })
        rows.sort(key=lambda x: x["submitted_at"] or "", reverse=True)
        low_score_by_criterion[key] = rows[:20]

    # Thong ke "van de khach hang gap phai nhieu nhat" - GOM tat ca ly do tu reasons_by_criterion
    # (da co san, tach theo tung tieu chi) THANH 1 danh sach chung, sap theo so lan nhac toi nhieu
    # nhat truoc (2026-08-29, yeu cau nguoi dung "phan tich thong ke noi dung nhung van de ma khach
    # thuong xuyen gap phai nhat") - van GOM theo CHUOI TRUNG KHOP TUYET DOI nhu reasons_by_criterion,
    # khong bia them "phan loai chu de" bang NLP khong co that trong du an nay.
    top_issues = []
    for c in CRITERIA:
        for row in reasons_by_criterion.get(c["key"], []):
            top_issues.append({
                "criterion_key": c["key"], "criterion_label": c["label"],
                "text": row["text"], "count": row["count"],
                "avg_score": row["avg_score"], "last_seen": row["last_seen"],
            })
    # Uu tien TIEU CHI bi phan anh nhieu nhat len truoc (2026-09-01, yeu cau nguoi dung "tieu chi
    # nao bi phan anh nhieu nhat uu tien hien thi truoc") - truoc day chi sap theo count/last_seen
    # cua TUNG dong ly do rieng le, nen 1 tieu chi co 3 dong (moi dong 1 khach viet khac nhau, count
    # deu =1) bi xep lan lon voi tieu chi chi co 1 dong, khong phan anh dung "tieu chi nao dang bi
    # nhac toi nhieu nhat noi chung". Tinh TONG so luot phan anh (tong count) cho tung tieu chi lam
    # khoa sap xep CHINH truoc - gom het cac dong CUNG 1 tieu chi bi phan anh nhieu nhat len dau,
    # dung count/last_seen cua tung dong lam khoa phu de sap xep trong noi bo 1 tieu chi.
    criterion_total_mentions = {}
    for row in top_issues:
        criterion_total_mentions[row["criterion_key"]] = criterion_total_mentions.get(row["criterion_key"], 0) + row["count"]
    top_issues.sort(key=lambda x: (criterion_total_mentions[x["criterion_key"]], x["count"], x["last_seen"] or ""), reverse=True)
    top_issues = top_issues[:10]

    ai_insights = _generate_insights(criteria_ranking, top_issues, avg_overall, total_completed)

    return {
        "status": "ok",
        "criteria": CRITERIA,
        "total_sent": total_sent,
        "total_completed": total_completed,
        "response_rate": response_rate,
        "avg_overall": avg_overall,
        "reasons_by_criterion": reasons_by_criterion,
        "avg_by_criterion": avg_by_criterion,
        "trend": trend,
        "low_score": low_score[:20],
        "recent": recent,
        "criteria_ranking": criteria_ranking,
        "top_issues": top_issues,
        "ai_insights": ai_insights,
        "low_score_by_criterion": low_score_by_criterion,
    }


# Nguong so luong phan hoi toi thieu de dua ra nhan dinh - duoi muc nay, 1-2 phieu le co the keo
# lech trung binh rat nhieu, "nhan dinh" luc do chi la nhieu, khong co y nghia thong ke.
_MIN_SAMPLE_FOR_INSIGHT = 5

# Goi y giai phap - moi cau CO DIEU KIEN, luon gan voi so lieu that (diem, so luot cham thap, noi
# dung gop y that) chu khong phai van ban chung chung khong lien quan du lieu. Ban than PHAN LOGIC
# (tieu chi nao dang la diem yeu, muc do nghiem trong) van la RULE-BASED (nguong so tren so that,
# xem _generate_insights() ben duoi) - KHONG doi sang de 1 AI tu quyet dinh "tieu chi nao dang te",
# tranh AI "bia" ra ket luan khong dung voi so lieu. **2026-09-01: rieng PHAN TRICH DAN gop y khach
# (1 cau dai) gio goi THAT Claude API de tom tat that su** (nguoi dung xac nhan sau khi hoi lai
# "sao ko tom tat duoc nhi" - _truncate_quote() truoc chi CAT BOT ky tu, khong hieu noi dung) - xem
# _summarize_with_ai() ben duoi, luon fallback ve _truncate_quote() neu thieu ANTHROPIC_API_KEY
# hoac goi API loi.
_ACTION_MAP = {
    "chat_luong_dich_vu": "Rà soát lại quy trình giao nhận, đối chiếu thời gian/tình trạng hàng thực tế so với cam kết ở các đơn liên quan đến những phản hồi điểm thấp.",
    "nhan_vien_ho_tro": "Đào tạo lại kỹ năng trao đổi qua Zalo (thái độ, tốc độ phản hồi) cho nhân viên hỗ trợ, ưu tiên rà soát các ca có điểm thấp gần đây.",
    "cskh": "Xem xét rút ngắn thời gian phản hồi CSKH và kiểm tra lại quy trình có giải quyết đúng vấn đề khách nêu hay không.",
    "uu_dai": "Rà soát, làm mới chương trình ưu đãi hiện tại; có thể khảo sát thêm nhu cầu cụ thể của nhóm khách đang chấm điểm thấp.",
    "giao_dien_app_web": "Kiểm tra lại trải nghiệm app/web ở các bước khách hay gặp khó, đối chiếu trực tiếp với nội dung góp ý bên dưới.",
}


def _truncate_quote(text, limit=55):
    """Rut gon 1 cau gop y dai (nguyen van khach viet, co the la 1 doan van dai lan man) xuong con
    toi da `limit` ky tu + '...' - dung lam FALLBACK cho _summarize_with_ai() khi khong goi duoc AI
    that (thieu key/loi mang). Day la CAT BOT hien thi don thuan, khong hieu/dien giai lai noi dung."""
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


# THEM 2026-09-01 sau khi nguoi dung hoi lai "sao ko tom tat duoc nhi" va xac nhan muon doi sang AI
# THAT - day la NGOAI LE co chu dich them 1 secret vao module nay (truoc gio co tinh giu KHONG
# secret nao trong logic insight, chi _truncate_quote() thuan code). ANTHROPIC_API_KEY PHAI do
# nguoi dung tu dat (bien moi truong tren Render, KHONG duoc hardcode trong repo) - neu chua co, ham
# duoi day tu dong fallback ve _truncate_quote(), khong bao gio lam sap /csat/summary chi vi thieu
# key hoac goi API loi (mang cham/timeout/rate limit...) - dung tinh than "khong nuot loi im lang"
# nhung van BAO VE endpoint chinh, giong _client()/StorageError o tren.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or ""
_AI_SUMMARY_MODEL = "claude-haiku-4-5-20251001"  # model nhanh + re, chi de tom tat 1 cau ngan
_ai_summary_cache = {}  # van ban goc (da strip) -> ban tom tat - CHI trong bo nho tien trinh nay,
                        # mat khi restart server (Render free tier con "ngu" sau 15 phut khong dung
                        # roi thuc day lai) - chap nhan duoc, day chi la toi uu tranh goi lai API
                        # cho DUNG 1 cau gop y o nhung lan /csat/summary ke tiep.


def _summarize_with_ai(text):
    """Goi THAT Claude API (model Haiku, nhanh+re) de tom tat 1 cau gop y dai cua khach thanh 1 cum
    tu ngan gon - thay cho _truncate_quote() (chi cat bot ky tu, khong hieu noi dung). LUON fallback
    ve _truncate_quote() neu: chua cau hinh ANTHROPIC_API_KEY, goi API loi (mang/timeout/rate
    limit...), hoac tra ve rong. Cache theo dung van ban goc de KHONG goi lai API cho cung 1 cau
    gop y."""
    text = (text or "").strip()
    if not text:
        return text
    if text in _ai_summary_cache:
        return _ai_summary_cache[text]
    fallback = _truncate_quote(text)
    if not ANTHROPIC_API_KEY:
        _ai_summary_cache[text] = fallback
        return fallback
    try:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _AI_SUMMARY_MODEL,
                "max_tokens": 40,
                "messages": [{
                    "role": "user",
                    "content": (
                        "Tóm tắt góp ý sau của khách hàng thành ĐÚNG 1 cụm từ ngắn gọn (tối đa 8 "
                        "từ), giữ nguyên tiếng Việt, không thêm ý kiến/đánh giá gì khác, không dùng "
                        "dấu ngoặc kép, chỉ trả về đúng cụm từ tóm tắt, không giải thích thêm:\n\n" + text
                    ),
                }],
            },
            timeout=8.0,
        )
        r.raise_for_status()
        summarized = r.json()["content"][0]["text"].strip()
        result = summarized or fallback
    except Exception:
        result = fallback
    _ai_summary_cache[text] = result
    return result


def _generate_insights(criteria_ranking, top_issues, avg_overall, total_completed):
    if total_completed < _MIN_SAMPLE_FOR_INSIGHT:
        return [{
            "severity": "info", "criterion_key": None, "criterion_label": None,
            "title": "Chưa đủ dữ liệu để đưa ra nhận định",
            "detail": f"Kỳ này mới có {total_completed} phản hồi — cần tối thiểu {_MIN_SAMPLE_FOR_INSIGHT} phản hồi để thống kê có ý nghĩa, tránh kết luận vội trên vài phiếu lẻ. Nhận định sẽ tự cập nhật khi có thêm dữ liệu.",
            "suggestion": None,
        }]

    insights = []
    flagged_keys = set()
    worst_candidates = [c for c in criteria_ranking if c["avg"] is not None and c["avg"] < 4][:2]
    for c in worst_candidates:
        severity = "high" if c["avg"] < 3 else "medium"
        # CHI lay 1 gop y tieu bieu nhat (truoc lay 2) + TOM TAT THAT bang AI (xem _summarize_with_ai())
        # - "AI Insight" la 1 nhan dinh CO DONG, khong phai noi lai het du lieu tho.
        related = [i for i in top_issues if i["criterion_key"] == c["key"]][:1]
        evidence = [f"TB {c['avg']:.1f}/5" + (" — thấp nhất" if c["rank"] == 1 else "")]
        if c["count_low"]:
            evidence.append(f"{c['count_low']} phản hồi ≤3 sao")
        if related:
            evidence.append(f"góp ý: \"{_summarize_with_ai(related[0]['text'])}\"")
        insights.append({
            "severity": severity, "criterion_key": c["key"], "criterion_label": c["label"],
            "title": f"{c['label']} đang là điểm yếu nhất" if c["rank"] == 1 else f"{c['label']} cũng cần lưu ý",
            "detail": " · ".join(evidence),
            "suggestion": _ACTION_MAP.get(c["key"]),
        })
        flagged_keys.add(c["key"])

    # THEM 2026-09-01 - phat hien qua nguoi dung "chat luong dich vu nguoi ta danh gia kem kia sao
    # khong phan tich": tieu chi co diem TRUNG BINH van >=4 (nen khong lot vao worst_candidates o
    # tren) nhung van co 1 CUM phan hoi ca the cham that su thap (>=2 phieu <=3 sao) - trung binh
    # cao co the "che lap" 1 nhom khach dang gap dung 1 van de cu the (vd nhieu khach 5 sao + vai
    # khach 2-3 sao vi cung 1 ly do that) neu chi nhin trung binh se khong bao gio thay duoc. Nguong
    # >=2 de tranh bao dong tren 1 phieu le ngau nhien/khong dai dien.
    _NOTABLE_LOW_COUNT = 2
    for c in criteria_ranking:
        if len(insights) >= 3 or c["key"] in flagged_keys:
            continue
        if c["avg"] is None or c["count_low"] < _NOTABLE_LOW_COUNT:
            continue
        related = [i for i in top_issues if i["criterion_key"] == c["key"]][:1]
        evidence = [f"TB {c['avg']:.1f}/5 (vẫn ổn)", f"{c['count_low']} phản hồi ≤3 sao"]
        if related:
            evidence.append(f"góp ý: \"{_summarize_with_ai(related[0]['text'])}\"")
        insights.append({
            "severity": "medium", "criterion_key": c["key"], "criterion_label": c["label"],
            "title": f"{c['label']} có một nhóm đánh giá thấp đáng chú ý",
            "detail": " · ".join(evidence),
            "suggestion": _ACTION_MAP.get(c["key"]),
        })
        flagged_keys.add(c["key"])

    if not insights:
        insights.append({
            "severity": "positive", "criterion_key": None, "criterion_label": None,
            "title": "Chưa phát hiện điểm yếu rõ rệt",
            "detail": f"Cả 5 tiêu chí đều đạt trung bình ≥4/5 trong kỳ này (điểm tổng {avg_overall}/5).",
            "suggestion": "Tiếp tục duy trì chất lượng hiện tại, theo dõi thêm ở kỳ tiếp theo.",
        })
    return insights
