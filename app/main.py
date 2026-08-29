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

LUU Y VE DO BEN DU LIEU: file JSON o data/csat_surveys.json la luu tru DUY NHAT (xem
csat_survey.py) - tren cac nen cloud free tier dung "ephemeral disk" (vd Render free web
service), du lieu nay CO THE MAT khi service redeploy (mac du thuong con nguyen qua cac lan
"spin down do het hoat dong" - chua kiem chung chac chan). Neu can dam bao khong bao gio mat du
lieu that, nen nang cap len persistent disk (Render) hoac chuyen luu tru sang 1 database ben
ngoai - CHUA lam trong ban nay theo dung pham vi yeu cau."""

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


class CsatSurveySubmit(BaseModel):
    scores: dict[str, int]
    comment: str | None = None
    reasons: dict[str, str] | None = None
    customer_name: str | None = None
    phone: str | None = None


@app.post("/csat/survey-open/submit")
def csat_survey_open_submit(body: CsatSurveySubmit):
    try:
        record = csat_survey.add_open_response(
            body.scores, body.comment, reasons=body.reasons,
            customer_name=body.customer_name, phone=body.phone,
        )
    except csat_survey.InvalidScores as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "survey": record}


@app.get("/csat/summary")
def csat_summary(start: str | None = None, end: str | None = None):
    """Thong ke hieu qua dich vu (ty le phan hoi, diem trung binh tung tieu chi, xu huong theo
    ngay, danh sach diem thap can chu y) - dung cho tab "Khảo sát CSKH" trong dashboard CarePilot."""
    return csat_survey.summary(start=start, end=end)


@app.get("/csat/surveys")
def csat_list_surveys():
    return {"status": "ok", "surveys": csat_survey.list_surveys()}
