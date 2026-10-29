import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import hmac
import hashlib
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- RENDER PULSUZ WEB SERVICE ÜÇÜN MİNİ SERVER ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kripto Flamingo Bot is active!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()
# --------------------------------------------------

TOKEN = "8610857727:AAFlZGlgBfm6mPIj8YFlHxVXYkaswdxEgg8"
CHAT_ID = "8411309690"

# Binance API açarları (hələlik boş saxlaya bilərsən)
BINANCE_API_KEY = "BURAYA_API_KEY_YAZACAQSAN"
BINANCE_SECRET_KEY = "BURAYA_SECRET_KEY_YAZACAQSAN"

# Şəxsi bulud qovluğu
CLOUD_DIR = "CloudStorage"
if not os.path.exists(CLOUD_DIR):
    os.makedirs(CLOUD_DIR)

def send_message(text, disable_notification=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID, 
        'text': text,
        'disable_notification': str(disable_notification).lower()
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            pass
    except Exception as e:
        print(f"Mesaj göndərilərkən xəta: {e}")

def get_market_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Bazar məlumatları alınarkən xəta: {e}")
        return None

def get_binance_balance():
    if not BINANCE_API_KEY or BINANCE_API_KEY == "BURAYA_API_KEY_YAZACAQSAN":
        return None
    url = "https://api.binance.com/api/v3/account"
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = hmac.new(
        BINANCE_SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    full_url = f"{url}?{query_string}&signature={signature}"
    req = urllib.request.Request(full_url, headers={
        'X-MBX-APIKEY': BINANCE_API_KEY,
        'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req) as response:
            account_data = json.loads(response.read().decode('utf-8'))
            balances = [b for b in account_data['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            return balances
    except Exception as e:
        print(f"Balans oxunarkən xəta: {e}")
        return None

def check_telegram_files(last_update_id):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=5"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data['ok'] and data['result']:
                for update in data['result']:
                    last_update_id = update['update_id']
                    message = update.get('message', {})
                    
                    file_info = None
                    file_name = "file"
                    
                    if 'document' in message:
                        doc = message['document']
                        file_info = doc
                        file_name = doc.get('file_name', 'document')
                    elif 'photo' in message:
                        photo = message['photo'][-1]
                        file_info = photo
                        file_name = f"photo_{int(time.time())}.jpg"
                    
                    if file_info:
                        file_id = file_info['file_id']
                        file_path_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
                        req_file = urllib.request.Request(file_path_url)
                        with urllib.request.urlopen(req_file) as f_resp:
                            f_data = json.loads(f_resp.read().decode('utf-8'))
                            if f_data['ok']:
                                file_path = f_data['result']['file_path']
                                download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                                
                                local_file_path = os.path.join(CLOUD_DIR, file_name)
                                urllib.request.urlretrieve(download_url, local_file_path)
                                
                                print(f"Fayl uğurla endirildi: {local_file_path}")
                                send_message(f"✅ Fayl şəxsi buluda uğurla yükləndi: {file_name}")
    except Exception as e:
        pass
    return last_update_id

if __name__ == "__main__":
    # Mini serveri arxa planda işə salırıq ki, Render pulsuz qəbul etsin
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    send_message("🦩 Kripto Flamingo & Şəxsi Bulud işə düşdü! 🚀")
    last_update_id = 0
    last_market_check = 0
    
    while True:
        current_time = time.time()
        
        # Hər 5 dəqiqədən bir kripto bazarını yoxlayırıq
        if current_time - last_market_check >= 300:
            coins = get_market_prices()
            if coins:
                current_hour = datetime.now().hour
                is_night = 0 <= current_hour < 8
                
                message = "🌐 **Kripto Flamingo - Canlı Bazar & Analiz:**\n"
                strong_signals = []
                
                for coin in coins:
                    name = coin['name']
                    symbol = coin['symbol'].upper()
                    price = coin['current_price']
                    change_24h = coin['price_change_percentage_24h'] or 0
                    
                    emoji = "🟢" if change_24h >= 0 else "🔴"
                    message += f"\n{emoji} {name} ({symbol}): ${price:,.2f} USD (24s: {change_24h:.2f}%)"
                    
                    if change_24h <= -5.0:
                        strong_signals.append(f"🚨 **GÜCLÜ ALIŞ FÜRSƏTİ (Dərin Enmə)!**\n{name} ({symbol}) kəskin düşüb: ${price:,.2f} ({change_24h:.2f}%)")
                    elif change_24h >= 5.0:
                        strong_signals.append(f"🚨 **DİQQƏT - GÜCLÜ QALXMA (Zirvə Testi)!**\n{name} ({symbol}) kəskin qalxıb: ${price:,.2f} ({change_24h:.2f}%)")
                
                balances = get_binance_balance()
                if balances:
                    message += "\n\n💰 **Binance Balansınız:**"
                    for b in balances:
                        asset = b['asset']
                        free = float(b['free'])
                        if free > 0:
                            message += f"\n{asset}: {free}"
                
                send_message(message, disable_notification=is_night)
                for signal in strong_signals:
                    send_message(signal, disable_notification=False)
            else:
                send_message("⚠️ Xəta: Bazar məlumatlarını oxumaq mümkün olmadı.", disable_notification=False)
            
            last_market_check = current_time
        
        # Hər saniyə telefonla göndərilən faylları yoxlayırıq
        last_update_id = check_telegram_files(last_update_id)
        
        time.sleep(2)
