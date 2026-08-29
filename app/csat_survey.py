"""Khao sat CSAT (muc do hai long) ve chat luong dich vu CSKH qua Zalo - nguoi dung yeu cau
2026-08-28 "tao 1 form de gui khach hang danh gia chat luong dich vu qua Zalo, thong ke do luong
hieu qua dich vu". 5 tieu chi (nguoi dung tu chon khi duoc hoi, khong phai suy doan):
  1. Chat luong dich vu (giao nhan dung cam ket - thoi gian, tinh trang hang)
  2. Nhan vien ho tro (thai do, su nhiet tinh/chuyen nghiep khi trao doi qua Zalo)
  3. Cham soc khach hang - CSKH (phan hoi nhanh, giai quyet dung van de)
  4. Uu dai (chuong trinh khuyen mai co hap dan/phu hop khong)
  5. Giao dien app/web (de tra cuu, de thao tac)
Moi tieu chi cham 1-5 sao, kem 1 o gop y tu do (khong bat buoc).

KHONG co su kien "dong ticket ho tro" TU DONG trong he thong hien tai (tab "Kenh cho ho tro" -
frontend/tabs/07-cho-ho-tro - chi la hang doi giam sat, chua co vong doi ticket/trang thai
resolved) - nen "gui khao sat" o day la HANH DONG THU CONG: agent CSKH tu bam "Gui khao sat" cho
1 khach (trong tab moi frontend/report/khao-sat-cskh-dark.html) khi ho coi cuoc trao doi da xong,
thay vi tu dong bam theo 1 event he thong. Xem thread quyet dinh nay trong memory du an
(project_carepilot_csat_survey).

Luu tru: file JSON atomic, CUNG mau voi customer_notes.py/f_bucket_history.py (khong dung
SQLite/DB that - dung tinh than "prototype, du lieu mat khi xoa file la binh thuong" cua du an).
Key la token (chuoi ngau nhien, dung lam URL cong khai KHONG doan duoc de khach bam tu Zalo vao
thang trang khao sat ma khong can dang nhap)."""

import json
import os
import secrets
from datetime import datetime, timezone

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "csat_surveys.json")

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


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load():
    path = os.path.normpath(DATA_PATH)
    if not os.path.exists(path):
        return {"surveys": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("surveys", {})
            return data
    except (json.JSONDecodeError, OSError):
        return {"surveys": {}}  # file hong/rong - coi nhu chua co khao sat nao, khong lam sap trang


def _save(data):
    path = os.path.normpath(DATA_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp_path, path)


def create_survey(customer_id, customer_name, phone=None, zalo_user_id=None, context_label=None):
    """Tao 1 khao sat o trang thai 'pending', tra ve record vua tao (co token dung de
    dung link cong khai /csat/survey/<token>). Ghi atomic ngay."""
    token = secrets.token_urlsafe(16)
    record = {
        "token": token,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "phone": phone,
        "zalo_user_id": zalo_user_id,
        "context_label": context_label or "",
        "created_at": _now_iso(),
        "status": "pending",
        "scores": None,
        "comment": None,
        "reasons": None,
        "submitted_at": None,
    }
    data = _load()
    data["surveys"][token] = record
    _save(data)
    return record


def get_survey(token):
    return _load()["surveys"].get(token)


def add_open_response(scores, comment, reasons=None, customer_name=None, phone=None):
    """THEM 2026-08-29: khac voi create_survey()+submit_survey() (1 token = 1 khach, dung 1
    lan roi khoa lai "da danh gia") - ham nay phuc vu 1 LINK DUNG CHUNG gui cho TAT CA khach
    (nguoi dung yeu cau "chi can gui link khao sat cho khach, khach nao dien thi thong ke tra
    ve"), ai bam vao cung thay form trong, cung nop duoc, khong bi chan boi trang thai
    "da hoan thanh" cua nguoi truoc. Validate diem giong het submit_survey(), chi khac la
    KHONG can token/pending truoc - tao thang 1 ban ghi 'completed' hoan chinh.
    customer_name/phone: THEM sau (nguoi dung yeu cau "cho thêm mục nhập tên và sdt") - ca 2
    deu KHONG bat buoc (link dung chung khong the ep khach phai dien danh tinh), rong thi
    dung placeholder "Khach qua link khao sat" nhu truoc day.
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
    record = {
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
    data = _load()
    data["surveys"][record["token"]] = record
    _save(data)
    return record


def submit_survey(token, scores, comment, reasons=None):
    data = _load()
    record = data["surveys"].get(token)
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

    # reasons: {tieu_chi_key: ly_do_text} - THEM 2026-08-28, CHI luu cho tieu chi thuc su <=3 sao
    # (khong tin tuong nguyen si input tu client - loc lai o day, phong truong hop client gui du
    # lieu khong khop, vd JS bi sua/goi thang API bo qua UI). Khong bat buoc phai co ly do cho MOI
    # tieu chi diem thap - khach co the bo trong.
    clean_reasons = {}
    if reasons:
        for k, text in reasons.items():
            if k in CRITERIA_KEYS and scores.get(k, 5) <= 3 and isinstance(text, str) and text.strip():
                clean_reasons[k] = text.strip()[:500]

    record["scores"] = {k: scores[k] for k in CRITERIA_KEYS}
    record["comment"] = (comment or "").strip()[:2000]  # chan do dai hop ly, tranh 1 khach spam file qua to
    record["reasons"] = clean_reasons or None
    record["status"] = "completed"
    record["submitted_at"] = _now_iso()
    data["surveys"][token] = record
    _save(data)
    return record


def list_surveys():
    """Toan bo khao sat (ca pending lan completed), moi gui/tao truoc len dau."""
    rows = list(_load()["surveys"].values())
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows


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
    Khong loc theo start/end thi lay TOAN BO lich su."""
    rows = list(_load()["surveys"].values())

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

    # Xep hang ly do khong hai long THEO TUNG tieu chi - THEM 2026-08-28 (nguoi dung yeu cau, xem
    # changelog dau file). Gom theo CHUOI TRUNG KHOP TUYET DOI sau khi chuan hoa (strip + hoa/thuong
    # + gop khoang trang lien tiep) - KHONG phai gom theo y nghia/NLP (khong co model that dung o
    # day, tranh bia ra 1 "phan loai chu de" khong that su ton tai). Neu nhieu khach viet CUNG 1 cau
    # y het nhau (vd cung sao chep 1 cau tu goi y nao do) thi "count" > 1 phan anh dung tan suat that;
    # neu tat ca deu viet khac nhau (thuong gap voi van ban tu do) thi day chi la danh sach theo thoi
    # gian, moi dong count=1 - KHONG bia them y nghia "pho bien" neu du lieu khong cho thay dieu do.
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
        rows = [
            {"text": b["text"], "count": b["count"], "last_seen": b["last_seen"], "avg_score": round(b["score_sum"] / b["count"], 2)}
            for b in buckets.values()
        ]
        # count giam dan (ly do lap lai nhieu nhat len dau); cung count thi last_seen giam dan (moi nhat truoc).
        rows.sort(key=lambda x: (x["count"], x["last_seen"] or ""), reverse=True)
        reasons_by_criterion[key] = rows

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
    }
