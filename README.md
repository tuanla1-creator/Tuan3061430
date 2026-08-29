# csat-public

Phiên bản rút gọn, độc lập của tính năng khảo sát CSAT (xem `project_carepilot_csat_survey`
trong memory dự án) — tách riêng để **deploy lên cloud miễn phí, chạy 24/7**, không phụ thuộc
máy cá nhân có đang bật hay không (khác với Cloudflare quick tunnel trước đó — đổi domain mỗi
lần chạy lại lệnh + cần máy bật liên tục).

Không import bất kỳ module GHN nội bộ nào khác (không cần API key/credential nào cả) — an toàn
để đưa lên host công khai miễn phí.

## Chạy thử ở máy (trước khi deploy)

```bash
cd services/csat-public
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Mở `http://localhost:8000/csat/survey-open` để xem form, `http://localhost:8000/csat/summary`
để xem thống kê JSON.

## Deploy lên Render.com (miễn phí, không cần thẻ)

1. Đẩy code trong thư mục `services/csat-public/` này lên 1 repo GitHub mới (repo riêng, không
   cần đẩy cả dự án CarePilot).
2. Vào [render.com](https://render.com) → đăng nhập bằng GitHub → **New +** → **Web Service**.
3. Chọn repo vừa tạo. Render sẽ tự đọc `render.yaml` trong repo và điền sẵn cấu hình
   (Python, free plan, build/start command) — chỉ cần bấm **Deploy**.
4. Sau khi deploy xong (vài phút), Render cho 1 URL dạng `https://<tên>.onrender.com` — đó là
   link cố định, không đổi theo thời gian (khác hẳn link `trycloudflare.com` tạm thời).
5. Link khảo sát gửi khách: `https://<tên>.onrender.com/csat/survey-open`.

## ⚠️ Lưu ý về độ bền dữ liệu

Dữ liệu khảo sát lưu trong 1 file JSON ngay trên đĩa của service (`data/csat_surveys.json`).
Trên gói free của Render, đĩa là **ephemeral** — có thể bị xoá sạch mỗi khi bạn deploy lại code
mới (chưa kiểm chứng chắc chắn việc "ngủ do không hoạt động" có xoá hay không). Nếu số lượng
khảo sát quan trọng và cần đảm bảo không bao giờ mất, nên nâng cấp sang Render persistent disk
(có phí) hoặc chuyển lưu trữ sang 1 database ngoài (chưa làm ở bản này).

## Free tier "ngủ" sau 15 phút không có ai truy cập

Lần đầu ai đó mở link sau một thời gian dài không ai vào, trang có thể mất ~30-60 giây để tải
(Render đánh thức service). Các lần sau trong cùng phiên hoạt động sẽ nhanh bình thường.

