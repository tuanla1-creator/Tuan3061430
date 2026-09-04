# csat-public

Phiên bản rút gọn, độc lập của tính năng khảo sát CSAT (xem `project_carepilot_csat_survey`
trong memory dự án) — tách riêng để **deploy lên cloud miễn phí, chạy 24/7**, không phụ thuộc
máy cá nhân có đang bật hay không (khác với Cloudflare quick tunnel trước đó — đổi domain mỗi
lần chạy lại lệnh + cần máy bật liên tục).

Không import bất kỳ module GHN nội bộ nào khác — an toàn để đưa lên host công khai miễn phí.
Cần `SUPABASE_URL`/`SUPABASE_KEY` để lưu dữ liệu (bắt buộc, xem mục bên dưới); `ANTHROPIC_API_KEY`
là **tuỳ chọn** (thêm 2026-09-01) — chỉ dùng để tóm tắt góp ý khách bằng AI thật trong "AI Insight",
không có cũng chạy bình thường (tự rút gọn bằng cách cắt ký tự thay vì tóm tắt thật).

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

## ⚠️ Đã từng mất dữ liệu thật (2026-08-29) — giờ dùng Supabase, không còn dùng file JSON nữa

Bản đầu tiên lưu khảo sát vào 1 file JSON ngay trên đĩa của service (`data/csat_surveys.json`).
Trên gói free của Render, đĩa là **ephemeral** — 2 phiếu khảo sát thật của người dùng đã bị **xoá
sạch** khi service khởi động lại/redeploy, đúng như cảnh báo cũ ở đây đã nói trước. Để không lặp
lại, service này giờ lưu qua **Supabase** (Postgres miễn phí) thay vì file JSON — làm theo phần
dưới đây để thiết lập.

## Thiết lập Supabase (bắt buộc, làm 1 lần)

1. Vào [supabase.com](https://supabase.com) → đăng ký tài khoản miễn phí (có thể dùng GitHub để
   đăng nhập nhanh) → **New project** → đặt tên tuỳ ý, chọn 1 mật khẩu database (lưu lại, ít dùng
   tới nhưng phòng khi cần), chọn khu vực gần nhất → **Create new project** (đợi ~1-2 phút để
   Supabase khởi tạo).
2. Vào project vừa tạo → menu bên trái chọn **SQL Editor** → **New query** → dán đoạn SQL sau rồi
   bấm **Run**:

   ```sql
   create table csat_surveys (
     token text primary key,
     seq_no bigserial,
     customer_id text,
     customer_name text,
     phone text,
     zalo_user_id text,
     context_label text,
     created_at timestamptz not null default now(),
     status text not null default 'pending',
     scores jsonb,
     comment text,
     reasons jsonb,
     submitted_at timestamptz
   );
   ```

   `seq_no` (thêm 2026-09-04) tự động tăng dần ở MỌI bản ghi mới (không phân biệt tạo từ link
   chung hay link riêng) — dùng để sinh "Mã phiếu" (vd `KS000123`) hiển thị cho khách đối chiếu,
   xem mục "Thiết lập mã phiếu" bên dưới nếu bảng đã tạo từ trước (chưa có cột này).

3. Vào **Project Settings** (biểu tượng bánh răng) → **API** → lấy 2 giá trị:
   - **Project URL** (dạng `https://xxxxxxxxxxxx.supabase.co`) → đây là `SUPABASE_URL`.
   - **anon public** key (chuỗi dài trong mục "Project API keys") → đây là `SUPABASE_KEY`.
4. Vào Render → chọn service `csat-public` → **Environment** → **Add Environment Variable** →
   thêm đúng 2 biến:
   - `SUPABASE_URL` = Project URL vừa lấy (không có dấu `/` ở cuối)
   - `SUPABASE_KEY` = anon public key vừa lấy
5. Render sẽ tự khởi động lại service sau khi lưu biến môi trường — xong, từ giờ mọi phiếu khảo
   sát mới sẽ lưu bền vào Supabase, không còn bị mất khi Render khởi động lại/redeploy nữa.

Muốn xem lại dữ liệu thô bất kỳ lúc nào: vào Supabase → **Table Editor** → bảng `csat_surveys`.

## Thiết lập "Mã phiếu" (bắt buộc nếu bảng đã tạo TRƯỚC 2026-09-04)

Tính năng "Tạo link khảo sát riêng" (mỗi khách/đơn 1 link, kèm mã phiếu vd `KS000123` để khách
đối chiếu đúng phiếu nào là phiếu nào) cần cột `seq_no` trong bảng `csat_surveys`. Nếu bảng đã
tạo theo hướng dẫn phía trên **trước ngày 2026-09-04**, cột này chưa có — vào Supabase →
**SQL Editor** → **New query** → chạy đúng 1 câu sau (chỉ cần chạy 1 lần, an toàn với dữ liệu cũ,
không xoá gì cả):

```sql
alter table csat_surveys add column if not exists seq_no bigserial;
```

Không chạy câu này thì mọi thứ khác vẫn hoạt động bình thường — chỉ riêng "Mã phiếu" sẽ không
hiện (ẩn hẳn badge trên trang khách, hoặc hiện "—" ở khối "Tạo link khảo sát riêng" trên dashboard)
thay vì số thật (xem `format_survey_code()` trong `csat_survey.py`, tự fallback an toàn, không
làm sập trang).

## Thiết lập AI tóm tắt góp ý (tuỳ chọn, 2026-09-01)

Mặc định "AI Insight" chỉ **cắt bớt** góp ý dài của khách (kèm dấu "…") — không hiểu nội dung nên
không thể viết lại ngắn gọn. Nếu muốn góp ý được **tóm tắt thật** (AI đọc và diễn đạt lại), thêm 1
biến môi trường:

1. Vào [console.anthropic.com](https://console.anthropic.com) → đăng nhập/đăng ký → **API Keys** →
   tạo 1 API key mới (dạng `sk-ant-...`).
2. Vào Render → chọn service `csat-public` → **Environment** → **Add Environment Variable**:
   - `ANTHROPIC_API_KEY` = API key vừa tạo
3. Render tự khởi động lại service sau khi lưu — từ giờ góp ý dài trong "AI Insight" sẽ được tóm
   tắt thật bằng Claude (model Haiku, nhanh và rẻ) thay vì chỉ cắt ký tự.

**Lưu ý chi phí**: mỗi câu góp ý CHỈ được tóm tắt 1 lần rồi lưu tạm trong bộ nhớ service (mất khi
service khởi động lại/ngủ-thức dậy) — không gọi lại API cho cùng 1 câu ở những lần tải trang sau,
nên chi phí rất nhỏ (vài request mỗi khi có góp ý MỚI, không phải mỗi lần ai đó mở dashboard).
Không đặt biến này thì tính năng vẫn chạy bình thường, chỉ quay về cắt bớt ký tự như trước.

## Free tier "ngủ" sau 15 phút không có ai truy cập

Lần đầu ai đó mở link sau một thời gian dài không ai vào, trang có thể mất ~30-60 giây để tải
(Render đánh thức service). Các lần sau trong cùng phiên hoạt động sẽ nhanh bình thường.

