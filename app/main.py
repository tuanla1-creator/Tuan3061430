"""services/csat-public - phien ban RUT GON, DOC LAP cua tinh nang khao sat CSAT lay tu
services/analytics-service (xem project_carepilot_csat_survey trong memory du an). Tach rieng
thanh service nho nay de DEPLOY LEN CLOUD MIEN PHI (Render...) - phuc vu dung 1 nhu cau: co 1
LINK CONG KHAI on dinh (khong phu thuoc may nguoi dung co dang bat hay khong, khac Cloudflare
quick tunnel truoc do - doi domain moi lan chay lai + can may bat lien tuc) de gui cho khach
hang qua Zalo, khach dien xong thi ket qua hien ngay trong dashboard CarePilot noi bo.

CHU DINH KHONG import cac module GHN-internal khac (crm_client, data_gateway_client,
telesale_client, pitel_client, cohort*, f_buckets*, scheduler, reactivation, reports...) - service
nay KHONG can bat ky secret/API key GHN noi bo nao ca, an toan de dua len 1 host cong khai mien
phi ma khong lo lo bat cu credential nao.

LUU Y VE DO BEN DU LIEU (CAP NHAT 2026-08-29): TUNG luu vao file JSON o data/csat_surveys.json -
2 phieu khao sat THAT cua nguoi dung da bi MAT do dia ephemeral cua Render free tier bi xoa khi
service khoi dong lai/redeploy, dung nhu ghi chu cu da canh bao truoc. Da CHUYEN SANG Supabase
(Postgres qua REST API, xem csat_survey.py) - can dat 2 bien moi truong SUPABASE_URL/SUPABASE_KEY
tren Render (xem README.md muc "Thiet lap Supabase"). Neu 2 bien nay chua duoc dat, moi endpoint
lien quan se tra loi 503 ro rang thay vi am tham mat du lieu."""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import csat_survey, csat_survey_page

app = FastAPI(title="csat-public", description="Khao sat CSAT cong khai cho khach hang GHN")

# Cho phep dashboard CarePilot noi bo (mo qua file://, localhost, hoac domain khac) goi API nay
# tu trinh duyet - xem ghi chu tuong tu trong analytics-service/app/main.py.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _public_base_url():
    """Uu tien PUBLIC_BASE_URL tu dong dat tay trong .env/bien moi truong cua host; Render tu
    dat san RENDER_EXTERNAL_URL cho moi web service nen dung luon neu co, khoi phai tu dien
    tay sau khi biet domain that. Fallback ve localhost cho luc chay dev tren may."""
    return (
        os.getenv("PUBLIC_BASE_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or "http://localhost:8000"
    )


@app.get("/health")
def health():
    return {"ok": True, "service": "csat-public"}


@app.get("/csat/config")
def csat_config():
    return {"status": "ok", "public_base_url": _public_base_url()}


@app.get("/csat/survey-open", response_class=HTMLResponse)
def csat_survey_open_page():
    """Trang khao sat CONG KHAI dung LINK DUNG CHUNG gui cho TAT CA khach - ai bam vao cung
    dien duoc, khong bi khoa sau 1 lan nop dau tien. Xem them ghi chu trong
    services/analytics-service/app/csat_survey.py::add_open_response()."""
    return HTMLResponse(csat_survey_page.render_open_survey_page())


class CsatSurveyCreate(BaseModel):
    customer_name: str | None = None
    phone: str | None = None
    context_label: str | None = None  # vd "Đơn #12345" - ghi chú tự do, không bắt buộc


class CsatSurveySubmit(BaseModel):
    scores: dict[str, int]
    comment: str | None = None
    reasons: dict[str, str] | None = None
    customer_name: str | None = None
    phone: str | None = None


@app.post("/csat/surveys")
def csat_create_survey(body: CsatSurveyCreate):
    """THEM LAI 2026-09-04: tao 1 khao sat RIENG cho 1 khach/don cu the (khac /csat/survey-open
    la link DUNG CHUNG gui hang loat) - nguoi dung yeu cau "muon moi phieu khao sat co ma so
    nhat dinh de doi chieu dung phieu nao la phieu nao". Luong nay (create_survey() +
    GET/POST /csat/survey/{token}) da co san trong services/analytics-service/app/main.py tu
    truoc, chi chua tung duoc bat ben csat-public (service dang chay that) - gio them vao, giu
    SONG SONG voi link chung, KHONG thay the. KHONG tu dong gui qua Zalo (dung dinh huong "khong
    import module GHN-internal" cua service nay) - agent tu copy survey_url tra ve va gui thu
    cong qua Zalo/tin nhan nhu link chung."""
    try:
        record = csat_survey.create_survey(
            customer_id=None,
            customer_name=body.customer_name,
            phone=body.phone,
            context_label=body.context_label,
        )
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    survey_url = f"{_public_base_url()}/csat/survey/{record['token']}"
    return {
        "status": "ok",
        "survey": record,
        "survey_url": survey_url,
        "survey_code": csat_survey.format_survey_code(record.get("seq_no")),
    }


@app.get("/csat/survey/{token}", response_class=HTMLResponse)
def csat_survey_page_get(token: str):
    """Trang khao sat CONG KHAI cho 1 khach/don cu the (link rieng tu POST /csat/surveys o
    tren) - hien "Mã phiếu" ngay tren dau de khach doi chieu dung phieu, khac /csat/survey-open
    la form trong khong gan voi ai."""
    record = csat_survey.get_survey(token)
    if not record:
        return HTMLResponse(csat_survey_page.render_not_found_page(), status_code=404)
    return HTMLResponse(csat_survey_page.render_survey_page(record))


@app.post("/csat/survey/{token}/submit")
def csat_survey_submit(token: str, body: CsatSurveySubmit):
    """Khach bam 'Gui danh gia' tren trang link RIENG (GET /csat/survey/{token} o tren) goi vao
    day. Idempotent theo huong an toan: khao sat da 'completed' roi thi tu choi gui lai (khac
    /csat/survey-open/submit - link chung khong co khai niem 'da nop roi')."""
    try:
        record = csat_survey.submit_survey(token, body.scores, body.comment, reasons=body.reasons)
    except csat_survey.SurveyNotFound:
        raise HTTPException(status_code=404, detail="Không tìm thấy khảo sát.")
    except csat_survey.SurveyAlreadySubmitted:
        raise HTTPException(status_code=409, detail="Khảo sát này đã được đánh giá trước đó.")
    except csat_survey.InvalidScores as e:
        raise HTTPException(status_code=400, detail=str(e))
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"status": "ok", "survey": record}


@app.post("/csat/survey-open/submit")
def csat_survey_open_submit(body: CsatSurveySubmit):
    try:
        record = csat_survey.add_open_response(
            body.scores, body.comment, reasons=body.reasons,
            customer_name=body.customer_name, phone=body.phone,
        )
    except csat_survey.InvalidScores as e:
        raise HTTPException(status_code=400, detail=str(e))
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"status": "ok", "survey": record}


class CsatLogSend(BaseModel):
    count: int = 1  # so NGUOI THAT SU da nhan link trong dot gui nay (1 lan copy co the forward toi nhieu nguoi)


@app.post("/csat/survey-open/log-send")
def csat_survey_open_log_send(body: CsatLogSend = CsatLogSend()):
    """Nguoi dung tu ghi nhan da gui link cho (count) nguoi trong 1 dot - xem
    csat_survey.log_open_send() de biet vi sao khong the tu dong dem (viec dan link la thao tac
    thu cong ben ngoai he thong) va vi sao co tham so count (1 lan copy co the forward toi
    nhieu nguoi)."""
    try:
        records = csat_survey.log_open_send(count=body.count)
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"status": "ok", "count": len(records)}


@app.get("/csat/summary")
def csat_summary(start: str | None = None, end: str | None = None):
    """Thong ke hieu qua dich vu (ty le phan hoi, diem trung binh tung tieu chi, xu huong theo
    ngay, danh sach diem thap can chu y) - dung cho tab "Khảo sát CSKH" trong dashboard CarePilot."""
    try:
        return csat_survey.summary(start=start, end=end)
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/csat/surveys")
def csat_list_surveys():
    try:
        return {"status": "ok", "surveys": csat_survey.list_surveys()}
    except csat_survey.StorageNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except csat_survey.StorageError as e:
        raise HTTPException(status_code=502, detail=str(e))
