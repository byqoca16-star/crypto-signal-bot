import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

TOKEN = "8610857727:AAFlZGlgBfm6mPIj8YFlHxVXYkaswdxEgg8"
CHAT_ID = "8411309690"

def send_message(text, disable_notification=False):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Telegram API-yə səssiz göndərmək üçün 'disable_notification' əlavə edirik
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID, 
        'text': text,
        'disable_notification': str(disable_notification).lower()
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            print("Mesaj uğurla göndərildi!")
    except Exception as e:
        print(f"Xəta baş verdi: {e}")

def get_market_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            coins = json.loads(response.read().decode('utf-8'))
            return coins
    except Exception as e:
        print(f"Bazar məlumatları alınarkən xəta: {e}")
        return None

if __name__ == "__main__":
    send_message("🦩 Kripto Flamingo - Ağıllı İzləyici işə düşdü! Gecə rejimi və güclü siqnallar aktivdir.")
    
    while True:
        coins = get_market_prices()
        
        if coins:
            # Cari saatı yoxlayırıq (Gecə 00:00 - 08:00 arası)
            current_hour = datetime.now().hour
            is_night = 0 <= current_hour < 8
            
            message = "🌐 **Bazarın Top 10 Kriptovalyutası:**\n"
            strong_signals = []
            
            for coin in coins:
                name = coin['name']
                symbol = coin['symbol'].upper()
                price = coin['current_price']
                change = coin['price_change_percentage_24h']
                
                if change is not None:
                    emoji = "🟢" if change >= 0 else "🔴"
                    message += f"\n{emoji} {name} ({symbol}): ${price:,.2f} USD ({change:.2f}%)"
                    
                    # GÜCLÜ ALIŞ VƏ SATIŞ ŞƏRTLƏRİ (Məsələn: 24 saatda 4%-dən çox dəyişərsə)
                    if change <= -4.0:
                        strong_signals.append(f"🚨 **GÜCLÜ ALIŞ FÜRSƏTİ (Enmə)!**\n{name} ({symbol}) kəskin düşüb: ${price:,.2f} ({change:.2f}%)")
                    elif change >= 4.0:
                        strong_signals.append(f"🚨 **DİQQƏT - GÜCLÜ QALXMA!**\n{name} ({symbol}) kəskin qalxıb: ${price:,.2f} ({change:.2f}%)")
                else:
                    message += f"\n⚪ {name} ({symbol}): ${price:,.2f} USD"
            
            # 1. Əgər gecə vaxtıdırsa (00:00 - 08:00), ümumi siyahı SƏSSİZ şəkildə atılır. Gündüzdürsə səsli.
            send_message(message, disable_notification=is_night)
            
            # 2. Əgər güclü alış və ya satış siqnalı VARSADA, gecə olmasından asılı olmayaraq HƏMİŞƏ SƏSLİ (diqqət çəkən) xəbərdarlıq atırıq!
            for signal in strong_signals:
                send_message(signal, disable_notification=False)
                
        else:
            send_message("⚠️ Xəta: Bazar məlumatlarını oxumaq mümkün olmadı.", disable_notification=False)
        
        # Bazarı yormamaq və qadağa yeməmək üçün 5 dəqiqə (300 saniyə) gözləyirik
        print("Növbəti yoxlamaya qədər 5 dəqiqə gözlənilir...")
        time.sleep(300)
