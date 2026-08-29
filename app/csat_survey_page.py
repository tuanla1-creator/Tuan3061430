"""Render trang HTML khao sat CONG KHAI (khach bam link tu tin nhan Zalo vao thang day, khong
dang nhap) - CO CHU DINH tach rieng theme voi frontend/report/*-dark.html (dashboard NOI BO cho
agent CSKH xem thong ke): trang nay huong toi KHACH HANG mo bang trinh duyet trong app Zalo tren
dien thoai, nen dung theme SANG, gon, mobile-first, thuong hieu GHN cam - khong dung dark/
glassmorphism cua dashboard noi bo (khong hop tone voi 1 form khao sat gui ra ngoai).

Tu chua hoan toan (khong goi font/script/asset ngoai) vi trinh duyet trong app Zalo tren dien
thoai co the mang, cham hoac chan tai nguyen ngoai mien."""

import html

from .csat_survey import CRITERIA

_ORANGE = "#FF7A00"
_ORANGE_DEEP = "#E85F00"


def _esc(s):
    return html.escape(str(s or ""))


def _shell(title, body_html, extra_head=""):
    return f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{_esc(title)}</title>
<style>
:root{{ --orange:{_ORANGE}; --orange-deep:{_ORANGE_DEEP}; --ink:#1A1D23; --ink-2:#5B6270; --bg:#F5F6F8; --card:#FFFFFF; --border:#E7E9ED; --star-off:#DADDE3; --good:#1BAF7A; }}
*,*::before,*::after{{box-sizing:border-box;}}
html,body{{margin:0; padding:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}}
body{{min-height:100vh; display:flex; justify-content:center; padding:0 0 40px;}}
.wrap{{width:100%; max-width:480px;}}
.hero{{background:linear-gradient(135deg,var(--orange),var(--orange-deep)); color:#fff; padding:28px 20px 40px; text-align:center;}}
.hero .logo{{font-weight:800; font-size:15px; letter-spacing:.06em; text-transform:uppercase; opacity:.92;}}
.hero h1{{margin:10px 0 0; font-size:19px; font-weight:800; line-height:1.35;}}
.hero p{{margin:8px 0 0; font-size:13px; opacity:.92; line-height:1.5;}}
.card{{background:var(--card); border-radius:16px; box-shadow:0 8px 28px rgba(20,20,30,.08); margin:-24px 16px 0; padding:20px 18px 22px; position:relative;}}
.crit{{padding:16px 0; border-bottom:1px solid var(--border);}}
.crit:last-of-type{{border-bottom:none;}}
.crit-label{{font-size:14.5px; font-weight:700; color:var(--ink);}}
.crit-hint{{font-size:12.5px; color:var(--ink-2); margin-top:3px; line-height:1.45;}}
.stars{{display:flex; gap:6px; margin-top:10px;}}
.star-input{{display:none;}}
.star-btn{{width:38px; height:38px; cursor:pointer; display:flex; align-items:center; justify-content:center;}}
.star-btn svg{{width:30px; height:30px; fill:var(--star-off); transition:fill .12s ease, transform .12s ease;}}
.star-btn:active svg{{transform:scale(.9);}}
.crit.rated .crit-label::after{{content:" ✓"; color:var(--good); font-weight:800;}}
.comment-block{{padding-top:16px;}}
.comment-block label{{font-size:14.5px; font-weight:700; display:block; margin-bottom:8px;}}
textarea, input[type="text"], input[type="tel"]{{width:100%; border-radius:10px; border:1px solid var(--border); padding:10px 12px; font:inherit; font-size:13.5px; color:var(--ink); background:#FAFBFC; box-sizing:border-box;}}
textarea{{min-height:88px; resize:vertical;}}
textarea:focus, input[type="text"]:focus, input[type="tel"]:focus{{outline:none; border-color:var(--orange);}}
.contact-block{{padding-bottom:18px; border-bottom:1px solid var(--border); margin-bottom:4px;}}
.contact-field{{margin-bottom:12px;}}
.contact-field:last-child{{margin-bottom:0;}}
.contact-field label{{font-size:12.5px; font-weight:700; color:var(--ink-2); display:block; margin-bottom:6px;}}
.reason-block{{display:none; margin-top:10px;}}
.reason-block.show{{display:block;}}
.reason-block label{{font-size:12.5px; font-weight:700; color:var(--ink-2); display:block; margin-bottom:6px;}}
.reason-block textarea{{min-height:56px; font-size:12.5px;}}
.submit-btn{{width:100%; margin-top:20px; padding:14px; border:none; border-radius:12px; background:var(--orange); color:#fff; font-size:15px; font-weight:800; cursor:pointer; transition:background .15s ease, opacity .15s ease;}}
.submit-btn:hover{{background:var(--orange-deep);}}
.submit-btn:disabled{{opacity:.55; cursor:not-allowed;}}
.err-msg{{margin-top:12px; font-size:12.5px; color:#D03B3B; font-weight:600; text-align:center; display:none;}}
.footer-note{{text-align:center; font-size:11.5px; color:var(--ink-2); margin:16px 16px 0;}}
.state-card{{background:var(--card); border-radius:16px; box-shadow:0 8px 28px rgba(20,20,30,.08); margin:-24px 16px 0; padding:36px 22px; text-align:center;}}
.state-card .icon{{width:56px; height:56px; margin:0 auto 14px;}}
.state-card h2{{margin:0 0 8px; font-size:17px; font-weight:800;}}
.state-card p{{margin:0; font-size:13.5px; color:var(--ink-2); line-height:1.55;}}
{extra_head}
</style>
</head>
<body>
<div class="wrap">
{body_html}
</div>
</body>
</html>"""


def _star_icon():
    return '<svg viewBox="0 0 24 24"><path d="M12 2.5l2.9 6.2 6.8.7-5.1 4.6 1.5 6.7L12 17.1l-6.1 3.6 1.5-6.7-5.1-4.6 6.8-.7z"/></svg>'


def render_survey_page(record):
    """record: dict tu csat_survey.get_survey() (khong None - da kiem tra o goi noi trong main.py)."""
    customer_name = record.get("customer_name") or "bạn"
    hero = f"""
<div class="hero">
  <div class="logo">GHN · Chăm sóc khách hàng</div>
  <h1>Chào {_esc(customer_name)}, bạn đánh giá dịch vụ CSKH qua Zalo thế nào?</h1>
  <p>Mỗi lượt đánh giá đều giúp chúng tôi phục vụ bạn tốt hơn. Chỉ mất khoảng 30 giây.</p>
</div>"""

    if record["status"] == "completed":
        body = hero + """
<div class="state-card">
  <div class="icon">""" + _check_icon() + """</div>
  <h2>Cảm ơn bạn đã đánh giá!</h2>
  <p>Phản hồi của bạn đã được ghi nhận. Chúc bạn một ngày tốt lành!</p>
</div>
<p class="footer-note">© GHN — Giao Hàng Nhanh</p>"""
        return _shell("Đã ghi nhận đánh giá — GHN", body)

    crit_blocks = []
    for c in CRITERIA:
        stars = "".join(
            f"""<label class="star-btn" data-star="{i}">
                <input class="star-input" type="radio" name="score_{_esc(c['key'])}" value="{i}">
                {_star_icon()}
              </label>"""
            for i in range(1, 6)
        )
        crit_blocks.append(f"""
<div class="crit" data-crit="{_esc(c['key'])}">
  <div class="crit-label">{_esc(c['label'])}</div>
  <div class="crit-hint">{_esc(c['hint'])}</div>
  <div class="stars" data-key="{_esc(c['key'])}">{stars}</div>
  <div class="reason-block" data-reason-for="{_esc(c['key'])}">
    <label for="reason_{_esc(c['key'])}">Bạn chưa hài lòng ở điểm nào? (không bắt buộc)</label>
    <textarea id="reason_{_esc(c['key'])}" maxlength="500" placeholder="Cho chúng tôi biết lý do cụ thể..."></textarea>
  </div>
</div>""")

    form_html = f"""
<div class="card">
  {''.join(crit_blocks)}
  <div class="comment-block">
    <label for="comment">Góp ý thêm (không bắt buộc)</label>
    <textarea id="comment" maxlength="2000" placeholder="Bạn muốn góp ý điều gì cho chúng tôi?"></textarea>
  </div>
  <button class="submit-btn" id="submitBtn" type="button">Gửi đánh giá</button>
  <div class="err-msg" id="errMsg"></div>
</div>
<p class="footer-note">© GHN — Giao Hàng Nhanh</p>
"""

    script = f"""
<script>
(function(){{
  'use strict';
  var TOKEN = {record['token']!r};
  var CRITERIA_KEYS = {[c['key'] for c in CRITERIA]!r};
  var scores = {{}};

  // Ô "Lý do" riêng cho từng tiêu chí - CHỈ hiện khi khách chấm tiêu chí đó ≤3 sao (thêm
  // 2026-08-28 theo yêu cầu xếp hạng lý do không hài lòng THEO TỪNG tiêu chí, thay vì 1 ô góp ý
  // chung không tách được). >3 sao thì ẩn lại (không xoá nội dung đã gõ, phòng khách bấm nhầm rồi
  // đổi lại sao thấp).
  document.querySelectorAll('.stars').forEach(function(group){{
    var key = group.getAttribute('data-key');
    var reasonBlock = document.querySelector('.reason-block[data-reason-for="' + key + '"]');
    group.querySelectorAll('.star-btn').forEach(function(btn){{
      btn.addEventListener('click', function(){{
        var val = parseInt(btn.getAttribute('data-star'), 10);
        scores[key] = val;
        btn.querySelector('input').checked = true;
        group.querySelectorAll('.star-btn').forEach(function(b){{
          var v = parseInt(b.getAttribute('data-star'), 10);
          b.querySelector('svg').style.fill = (v <= val) ? '{_ORANGE}' : '#DADDE3';
        }});
        group.closest('.crit').classList.add('rated');
        if (reasonBlock) reasonBlock.classList.toggle('show', val <= 3);
      }});
    }});
  }});

  var errEl = document.getElementById('errMsg');
  document.getElementById('submitBtn').addEventListener('click', function(){{
    var missing = CRITERIA_KEYS.filter(function(k){{ return !scores[k]; }});
    if (missing.length) {{
      errEl.textContent = 'Vui lòng đánh giá đủ ' + CRITERIA_KEYS.length + ' tiêu chí bên trên nhé.';
      errEl.style.display = 'block';
      return;
    }}
    errEl.style.display = 'none';
    // Gom "reasons" - CHỈ với tiêu chí đang chấm ≤3 sao VÀ có gõ nội dung (bỏ qua ô trống hoặc ô
    // đang ẩn vì tiêu chí đó >3 sao) - khớp đúng ý nghĩa "lý do không hài lòng ở tiêu chí này".
    var reasons = {{}};
    CRITERIA_KEYS.forEach(function(k){{
      if (scores[k] <= 3) {{
        var el = document.getElementById('reason_' + k);
        var text = el ? el.value.trim() : '';
        if (text) reasons[k] = text;
      }}
    }});
    var btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = 'Đang gửi...';
    fetch(window.location.pathname + '/submit', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{ scores: scores, comment: document.getElementById('comment').value, reasons: reasons }})
    }}).then(function(res){{
      if (!res.ok) return res.json().then(function(e){{ throw new Error(e.detail || 'Có lỗi xảy ra'); }});
      return res.json();
    }}).then(function(){{
      window.location.reload();
    }}).catch(function(err){{
      errEl.textContent = err.message || 'Có lỗi xảy ra, vui lòng thử lại.';
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Gửi đánh giá';
    }});
  }});
}})();
</script>"""

    return _shell(f"Khảo sát dịch vụ — {customer_name}", hero + form_html + script)


def _check_icon():
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="#1BAF7A" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" '
        'fill="rgba(27,175,122,0.12)" stroke="#1BAF7A"/><path d="M8 12.5l2.5 2.5 5.5-6"/></svg>'
    )


def render_open_survey_page():
    """THEM 2026-08-29: trang khao sat cho 1 LINK DUNG CHUNG gui cho TAT CA khach (khac
    render_survey_page() o tren - moi khach 1 token rieng, khoa lai sau khi nop). Trang nay
    KHONG gan voi 1 khach/token cu the nao, ai bam vao cung thay form trong va nop duoc, nop
    xong hien loi cam on tai cho (JS thay noi dung form bang trang thai cam on, KHONG reload
    trang - de neu dua cho nhieu nguoi dung chung 1 thiet bi thi nguoi tiep theo tu bam lai
    link neu can, khong bi ket qua nguoi truoc "khoa" mat form). Goi qua GET /csat/survey-open,
    nop qua POST /csat/survey-open/submit (xem csat_survey.add_open_response())."""
    hero = """
<div class="hero">
  <div class="logo">GHN · Chăm sóc khách hàng</div>
  <h1>Bạn thấy dịch vụ CSKH qua Zalo của GHN thế nào?</h1>
  <p>5 câu hỏi ngắn, khoảng 30 giây — góp ý của bạn giúp chúng tôi phục vụ tốt hơn.</p>
</div>"""

    crit_blocks = []
    for c in CRITERIA:
        stars = "".join(
            f"""<label class="star-btn" data-star="{i}">
                <input class="star-input" type="radio" name="score_{_esc(c['key'])}" value="{i}">
                {_star_icon()}
              </label>"""
            for i in range(1, 6)
        )
        crit_blocks.append(f"""
<div class="crit" data-crit="{_esc(c['key'])}">
  <div class="crit-label">{_esc(c['label'])}</div>
  <div class="crit-hint">{_esc(c['hint'])}</div>
  <div class="stars" data-key="{_esc(c['key'])}">{stars}</div>
  <div class="reason-block" data-reason-for="{_esc(c['key'])}">
    <label for="reason_{_esc(c['key'])}">Bạn chưa hài lòng ở điểm nào? (không bắt buộc)</label>
    <textarea id="reason_{_esc(c['key'])}" maxlength="500" placeholder="Cho chúng tôi biết cụ thể..."></textarea>
  </div>
</div>""")

    form_html = f"""
<div class="card" id="surveyCard">
  <div class="contact-block">
    <div class="contact-field">
      <label for="custName">Họ tên (không bắt buộc)</label>
      <input type="text" id="custName" maxlength="120" placeholder="Nhập họ tên của bạn">
    </div>
    <div class="contact-field">
      <label for="custPhone">Số điện thoại (không bắt buộc)</label>
      <input type="tel" id="custPhone" maxlength="20" placeholder="Nhập số điện thoại của bạn">
    </div>
  </div>
  {''.join(crit_blocks)}
  <div class="comment-block">
    <label for="comment">Góp ý thêm (không bắt buộc)</label>
    <textarea id="comment" maxlength="2000" placeholder="Bạn muốn góp ý điều gì cho chúng tôi?"></textarea>
  </div>
  <button class="submit-btn" id="submitBtn" type="button">Gửi đánh giá</button>
  <div class="err-msg" id="errMsg"></div>
</div>
<p class="footer-note">© GHN — Giao Hàng Nhanh</p>
"""

    script = f"""
<script>
(function(){{
  'use strict';
  var CRITERIA_KEYS = {[c['key'] for c in CRITERIA]!r};
  var scores = {{}};

  document.querySelectorAll('.stars').forEach(function(group){{
    var key = group.getAttribute('data-key');
    var reasonBlock = document.querySelector('.reason-block[data-reason-for="' + key + '"]');
    group.querySelectorAll('.star-btn').forEach(function(btn){{
      btn.addEventListener('click', function(){{
        var val = parseInt(btn.getAttribute('data-star'), 10);
        scores[key] = val;
        btn.querySelector('input').checked = true;
        group.querySelectorAll('.star-btn').forEach(function(b){{
          var v = parseInt(b.getAttribute('data-star'), 10);
          b.querySelector('svg').style.fill = (v <= val) ? '{_ORANGE}' : '#DADDE3';
        }});
        group.closest('.crit').classList.add('rated');
        if (reasonBlock) reasonBlock.classList.toggle('show', val <= 3);
      }});
    }});
  }});

  var errEl = document.getElementById('errMsg');
  document.getElementById('submitBtn').addEventListener('click', function(){{
    var missing = CRITERIA_KEYS.filter(function(k){{ return !scores[k]; }});
    if (missing.length) {{
      errEl.textContent = 'Vui lòng đánh giá đủ ' + CRITERIA_KEYS.length + ' tiêu chí bên trên nhé.';
      errEl.style.display = 'block';
      return;
    }}
    errEl.style.display = 'none';
    var reasons = {{}};
    CRITERIA_KEYS.forEach(function(k){{
      if (scores[k] <= 3) {{
        var el = document.getElementById('reason_' + k);
        var text = el ? el.value.trim() : '';
        if (text) reasons[k] = text;
      }}
    }});
    var btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = 'Đang gửi...';
    fetch('/csat/survey-open/submit', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        scores: scores,
        comment: document.getElementById('comment').value,
        reasons: reasons,
        customer_name: document.getElementById('custName').value,
        phone: document.getElementById('custPhone').value
      }})
    }}).then(function(res){{
      if (!res.ok) return res.json().then(function(e){{ throw new Error(e.detail || 'Có lỗi xảy ra'); }});
      return res.json();
    }}).then(function(){{
      document.getElementById('surveyCard').outerHTML =
        '<div class="state-card"><div class="icon">{_check_icon()}</div>' +
        '<h2>Cảm ơn bạn đã đánh giá!</h2>' +
        '<p>Phản hồi của bạn đã được ghi nhận. Chúc bạn một ngày tốt lành!</p></div>';
    }}).catch(function(err){{
      errEl.textContent = err.message || 'Có lỗi xảy ra, vui lòng thử lại.';
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Gửi đánh giá';
    }});
  }});
}})();
</script>"""

    return _shell("Khảo sát dịch vụ — GHN", hero + form_html + script)


def render_not_found_page():
    body = """
<div class="hero">
  <div class="logo">GHN · Chăm sóc khách hàng</div>
  <h1>Không tìm thấy khảo sát</h1>
</div>
<div class="state-card">
  <h2>Liên kết không hợp lệ hoặc đã hết hạn</h2>
  <p>Vui lòng liên hệ lại với nhân viên chăm sóc khách hàng để nhận liên kết khảo sát mới.</p>
</div>"""
    return _shell("Không tìm thấy khảo sát — GHN", body)
