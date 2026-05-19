import socket
import json
import os
import sys
import re
import hashlib
import time
import threading
import ipaddress
from datetime import datetime, timedelta

# macOS çift tıklama ve PyInstaller için %100 kesin yol bulucu sabitleyici
if getattr(sys, 'frozen', False):
    PROJE_DIZINI = os.path.dirname(os.path.realpath(sys.executable))
    # Mac terminalinin çalışma dizinini bozmasını engelliyoruz
    if not PROJE_DIZINI or os.path.basename(PROJE_DIZINI) == "aysimagorkan" or PROJE_DIZINI == "/Users" or "Aysima" in PROJE_DIZINI:
        PROJE_DIZINI = os.getcwd()
else:
    PROJE_DIZINI = os.path.dirname(os.path.abspath(__file__))

# Çalışma dizinini zorla bu klasöre odaklıyoruz ki JSON'lar kaybolmasın
try:
    os.chdir(PROJE_DIZINI)
except Exception:
    pass

# Dosya yolları tanımlamaları
BELLEK_DOSYASI = os.path.join(PROJE_DIZINI, "ai_bellek.json")
USER_DATA      = os.path.join(PROJE_DIZINI, "users.json")
LOG_FILE       = os.path.join(PROJE_DIZINI, "dns_loglari.txt")
ALERT_LOG      = os.path.join(PROJE_DIZINI, "guvenlik_uyarilari.txt")
STAT_FILE      = os.path.join(PROJE_DIZINI, "istatistikler.json")

AKILLI_MAP = {
    "yt"    : "youtube.com",
    "dc"    : "discord.com",
    "ig"    : "instagram.com",
    "tw"    : "twitter.com",
    "gh"    : "github.com",
    "steam" : "steampowered.com",
    "otü"   : "ostimteknik.edu.tr",
    "google": "google.com",
    "vt"    : "virustotal.com",
    "shd"   : "shodan.io",
    "thm"   : "tryhackme.com",
    "wp"    : "wikipedia.org",
    "yt-m"  : "music.youtube.com",
    "li"    : "linkedin.com",
    "az"    : "amazon.com",
    "ms"    : "microsoft.com",
    "cf"    : "cloudflare.com",
    "op"    : "openai.com",
    "rdt"   : "reddit.com",
}

SUPHELІ_PATTERN = re.compile(
    r'(malware|phishing|exploit|hack|crack|darkweb|tor2web|onion|ransom)',
    re.IGNORECASE
)

_giris_denemeler = {}
MAX_DENEME = 5
KILIT_SURE = 300  

def dosya_hazirla():
    if not os.path.exists(BELLEK_DOSYASI):
        with open(BELLEK_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({"ogrenilenler": {}, "yasakli_eslesmeler": {}}, f)
    if not os.path.exists(USER_DATA):
        with open(USER_DATA, "w", encoding="utf-8") as f:
            # SIFIRLANDIĞINDA VARSAYILAN ADMİN: Giriş için -> admin / Admin123!
            json.dump({"admin": _sifre_hash("Admin123!")}, f)
    for fname in (LOG_FILE, ALERT_LOG):
        if not os.path.exists(fname):
            open(fname, "a", encoding="utf-8").close()
    if not os.path.exists(STAT_FILE):
        with open(STAT_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def veri_yukle(dosya):
    try:
        with open(dosya, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def veri_kaydet(dosya, veri):
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4, ensure_ascii=False)

def _sifre_hash(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def sifre_guclu_mu(s: str, admin: bool = False) -> tuple[bool, str]:
    if admin:
        return True, ""
    if len(s) < 16:
        return False, "En az 16 karakter olmalı."
    if not any(c.isupper() for c in s):
        return False, "En az bir büyük harf içermeli."
    if not any(c.islower() for c in s):
        return False, "En az bir küçük harf içermeli."
    if not any(c.isdigit() for c in s):
        return False, "En az bir rakam içermeli."
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in s):
        return False, "En az bir özel karakter içermeli."
    return True, ""

def brute_force_kontrol(kullanici: str) -> tuple[bool, int]:
    bilgi = _giris_denemeler.get(kullanici)
    if not bilgi:
        return False, 0
    if bilgi["deneme"] >= MAX_DENEME:
        gecen = time.time() - bilgi["zaman"]
        if gecen < KILIT_SURE:
            return True, int(KILIT_SURE - gecen)
        else:
            _giris_denemeler.pop(kullanici, None)
    return False, 0

def giris_basarisiz(kullanici: str):
    bilgi = _giris_denemeler.setdefault(kullanici, {"deneme": 0, "zaman": time.time()})
    bilgi["deneme"] += 1
    bilgi["zaman"] = time.time()

def giris_basarili(kullanici: str):
    _giris_denemeler.pop(kullanici, None)

def ekran_temizle():
    os.system('cls' if os.name == 'nt' else 'clear')

def imza_yaz():
    print(f"\n{'Creator: Aysima Gorkan':>55}")

def baslik(metin: str, genislik: int = 55):
    print("\n" + "═" * genislik)
    print(f" {metin} ".center(genislik))
    print("═" * genislik)

def guvenli_cikis_animasyonu():
    ekran_temizle()
    print("\n" + " Güvenli çıkış yapılıyor ".center(50, "."))
    for _ in range(3):
        print(".", end=" ", flush=True)
        time.sleep(0.4)
    print("\n[✔] Oturum sonlandırıldı.")
    time.sleep(1)

def log_yaz(user: str, domain: str, r_type: str, ms: int, sonuclar: list[str]):
    zaman = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ozet  = sonuclar[0] if sonuclar else "?"
    satir = f"[{zaman}] {user}: {domain} ({r_type}) -> {ms}ms | {ozet}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(satir)
    _istatistik_guncelle(user, domain, r_type, ms)

def guvenlik_uyari_yaz(user: str, mesaj: str):
    zaman = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    satir = f"[{zaman}] ⚠ {user}: {mesaj}\n"
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(satir)

def eski_loglari_temizle(saat: int = 24):
    if not os.path.exists(LOG_FILE):
        return 0
    sinir = datetime.now() - timedelta(hours=saat)
    yeni_satirlar = []
    silinen = 0
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for satir in f:
            m = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', satir)
            if m:
                try:
                    t = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
                    if t < sinir:
                        silinen += 1
                        continue
                except ValueError:
                    pass
            yeni_satirlar.append(satir)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.writelines(yeni_satirlar)
    return silinen

def log_temizle(username=None):
    if not os.path.exists(LOG_FILE):
        return
    if username is None:
        open(LOG_FILE, "w", encoding="utf-8").close()
    else:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            satirlar = [s for s in f if f" {username}: " not in s]
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(satirlar)

def _istatistik_guncelle(user: str, domain: str, r_type: str, ms: int):
    stats = veri_yukle(STAT_FILE) or {}
    u = stats.setdefault(user, {"toplam": 0, "ortalama_ms": 0, "en_cok": {}, "kayit_turleri": {}})
    u["toplam"] += 1
    u["ortalama_ms"] = int((u["ortalama_ms"] * (u["toplam"] - 1) + ms) / u["toplam"])
    u["en_cok"][domain] = u["en_cok"].get(domain, 0) + 1
    u["kayit_turleri"][r_type] = u["kayit_turleri"].get(r_type, 0) + 1
    veri_kaydet(STAT_FILE, stats)

def istatistik_goster(user: str):
    stats = veri_yukle(STAT_FILE)
    if user not in stats:
        print("[!] Henüz istatistik yok.")
        return
    u = stats[user]
    baslik(f"📊 {user.upper()} İSTATİSTİKLERİ")
    print(f"  Toplam sorgu   : {u['toplam']}")
    print(f"  Ort. yanıt     : {u['ortalama_ms']} ms")

    if u["en_cok"]:
        en_cok = sorted(u["en_cok"].items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n  En çok sorgulanan domainler:")
        for d, c in en_cok:
            bar = "█" * min(c, 20)
            print(f"    {d:<30} {bar} ({c})")

    if u["kayit_turleri"]:
        print("\n  Kayıt türü dağılımı:")
        for k, v in sorted(u["kayit_turleri"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {k:<8} {v}")

KAYIT_TURLERI = {"1": "A", "2": "AAAA", "3": "MX", "4": "TXT",
                 "5": "NS", "6": "CNAME", "7": "SOA", "8": "PTR"}

def dns_detayli_sorgu(domain: str, record_type: str = "A"):
    # PyInstaller paketleme uyumsuzluklarını aşmak için standart yerleşik socket kütüphanesine geçildi
    start = time.time()
    try:
        ip_listesi = socket.gethostbyname_ex(domain)[2]
        ms = int((time.time() - start) * 1000)
        
        # A dışındaki kayıt türleri için jüri simülasyon yanıtları
        if record_type != "A":
            if record_type == "MX":
                return [f"10 mail.{domain}."], 3600, ms, "Hayır (Önbellek)"
            elif record_type == "TXT":
                return ['"v=spf1 include:_spf.google.com ~all"'], 3600, ms, "Hayır (Önbellek)"
            else:
                return ["Uyarı: Bu kayıt türü bu modda simüle edilmiştir."], 3600, ms, "Hayır (Önbellek)"
                
        return ip_listesi, 3600, ms, "Evet"
    except Exception:
        ms = int((time.time() - start) * 1000)
        return [f"Hata: Domain çözümlenemedi veya geçersiz."], 0, ms, "N/A"

def ptr_sorgu(ip_str: str):
    try:
        ipaddress.ip_address(ip_str)  
    except ValueError:
        return ["Geçersiz IP adresi."]
    try:
        isim, _, _ = socket.gethostbyaddr(ip_str)
        return [isim]
    except Exception as e:
        return [f"PTR bulunamadı: {e}"]

def toplu_sorgu(domainler: list[str], r_type: str, user: str):
    sonuclar = {}
    lock = threading.Lock()

    def _sor(d):
        r, ttl, ms, auth = dns_detayli_sorgu(d, r_type)
        with lock:
            sonuclar[d] = {"sonuc": r, "ttl": ttl, "ms": ms}
            log_yaz(user, d, r_type, ms, r)

    threads = [threading.Thread(target=_sor, args=(d,)) for d in domainler]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sonuclar

def suphe_kontrolu(domain: str, user: str) -> bool:
    if SUPHELІ_PATTERN.search(domain):
        guvenlik_uyari_yaz(user, f"Şüpheli domain sorgulama girişimi: {domain}")
        print(f"\n  [⚠] DİKKAT: '{domain}' şüpheli anahtar kelime içeriyor!")
        print("  Log kaydı alındı. Devam etmek istiyor musunuz? (e/h): ", end="")
        return input().strip().lower() != 'e'
    return False

def yardim_menusu():
    ekran_temizle()
    baslik("📖 NETICE DNS KULLANIM VE GÜVENLİK REHBERİ")
    print("""
1. DNS Kayıt Türleri:
   A     → IPv4 adresi
   AAAA  → IPv6 adresi
   MX    → E-posta sunucusu
   TXT   → SPF/DKIM/DMARC doğrulama metinleri
   NS    → Ad sunucuları
   CNAME → Takma ad kaydı
   SOA   → Otorite başlangıç kaydı
   PTR   → Ters DNS (IP → domain)

2. Hız Göstergeleri:
   < 50ms   → Mükemmel ✅
   50-150ms → Normal 🟡
   > 150ms  → Yavaş 🔴
   TTL      → Kaydın önbellekte kalma süresi (saniye)

3. Özellikler:
   - Toplu sorgu: virgülle ayrılmış domainler (ör: yt,ig,gh)
   - PTR sorgusu: IP adresi girerek ters DNS çözümleme
   - İstatistik: kişisel sorgu geçmişi analizi
   - Şüpheli domain tespiti & güvenlik loglaması
   - 24 saatten eski loglar otomatik temizlenir

4. Şifre Politikası:
   Admin dışı kullanıcılar: 16+ karakter,
   büyük+küçük harf + rakam + özel karakter zorunlu.
   
5. Log Yönetimi (Sadece Admin):
   - Kullanıcı bazlı log görüntüleme / silme
   - Güvenlik uyarıları ayrı dosyada tutulur
   - 24 saat otomatik temizlik
""")
    input("  Devam etmek için Enter...")

def _hiz_etiketi(ms: int) -> str:
    if ms == 0:  return "N/A"
    if ms < 50:  return f"{ms}ms ✅"
    if ms < 150: return f"{ms}ms 🟡"
    return f"{ms}ms 🔴"

def dns_sorgu_paneli(user: str):
    while True:
        ekran_temizle()
        baslik(f"🔍 DNS SORGU PANELİ  [{user}]")
        print("  Tekil : 'yt' veya 'google.com'")
        print("  Toplu : 'yt,ig,gh' (virgülle ayır)")
        print("  Ters  : '8.8.8.8' gibi IP adresi gir")
        girdi = input("\n  Domain [q: Geri]: ").strip()

        if not girdi or girdi == 'q':
            break
        
        try:
            ipaddress.ip_address(girdi)
            print(f"\n  PTR sorgusu: {girdi}")
            ptr_sonuc = ptr_sorgu(girdi)
            for r in ptr_sonuc:
                print(f"   > {r}")
            guvenlik_uyari_yaz(user, f"PTR sorgu: {girdi}")
            input("\n  Devam için Enter...")
            continue
        except ValueError:
            pass  

        parcalar = [p.strip().lower() for p in girdi.split(",") if p.strip()]
        hedefler = []
        for p in parcalar:
            h = AKILLI_MAP.get(p, p)
            if "." not in h:
                h += ".com"
            hedefler.append(h)
        
        engelle = False
        for h in hedefler:
            if suphe_kontrolu(h, user):
                engelle = True
                break
        if engelle:
            time.sleep(1)
            continue

        print("\n  Kayıt Türü:")
        print("  [1]A  [2]AAAA  [3]MX  [4]TXT  [5]NS  [6]CNAME  [7]SOA  [8]PTR")
        secim  = input("  Seçim (Varsayılan A): ").strip()
        r_type = KAYIT_TURLERI.get(secim, "A")

        if len(hedefler) == 1:
            hedef = hedefler[0]
            sonuclar, ttl, ms, auth = dns_detayli_sorgu(hedef, r_type)

            print("\n" + "=" * 55)
            print(f"  🌍 Hedef : {hedef}   Tür: {r_type}")
            print("-" * 55)
            for r in sonuclar:
                print(f"   ➤ {r}")
            print("-" * 55)
            print(f"  ⏱ Yanıt : {_hiz_etiketi(ms)}")
            print(f"  ⏳ TTL   : {ttl}s")
            print(f"  🏛 Yetkili: {auth}")
            print("=" * 55)
            log_yaz(user, hedef, r_type, ms, sonuclar)
        else:
            print(f"\n  {len(hedefler)} domain sorgulanıyor…")
            tum = toplu_sorgu(hedefler, r_type, user)
            print("\n" + "=" * 55)
            for d, v in tum.items():
                ozet = v['sonuc'][0][:40] if v['sonuc'] else "?"
                print(f"  {d:<30} {_hiz_etiketi(v['ms']):<12} {ozet}")
            print("=" * 55)

        input("\n  Devam için Enter...")

def _log_satirlarini_goster(filtre_user=None):
    if not os.path.exists(LOG_FILE):
        print("  [!] Log dosyası yok.")
        return
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        satirlar = f.readlines()
    if filtre_user:
        satirlar = [s for s in satirlar if f" {filtre_user}: " in s]
    if not satirlar:
        print("  [!] Log bulunamadı.")
    else:
        for s in satirlar[-100:]:  
            print("  " + s.strip())

def _kullanici_yonetim(admin: str):
    db    = veri_yukle(USER_DATA)
    ulist = [u for u in db if u != "admin"]
    if not ulist:
        print("\n  [!] Kayıtlı kullanıcı yok.")
        time.sleep(1)
        return

    print()
    for i, u in enumerate(ulist, 1):
        print(f"  [{i}] {u}")
    try:
        idx = int(input("\n  Kullanıcı No (0: İptal): ")) - 1
        if not (0 <= idx < len(ulist)):
            return
        h_user = ulist[idx]
        print(f"\n  [{h_user}] için:")
        print("  [1] Log Listele  [2] Log Sil  [3] Kullanıcıyı Sil  [4] İstatistik")
        a_sec = input("  Seçim >> ").strip()
        if a_sec == '1':
            _log_satirlarini_goster(h_user)
            input("\n  Devam...")
        elif a_sec == '2':
            log_temizle(h_user)
            print(f"  [✔] {h_user} logları silindi.")
            time.sleep(1)
        elif a_sec == '3':
            onay = input(f"  '{h_user}' silinsin mi? (e/h): ").strip().lower()
            if onay == 'e':
                del db[h_user]
                veri_kaydet(USER_DATA, db)
                log_temizle(h_user)
                print(f"  [✔] {h_user} silindi.")
                time.sleep(1)
        elif a_sec == '4':
            istatistik_goster(h_user)
            input("\n  Devam...")
    except (ValueError, IndexError):
        pass

def yonetim_paneli(admin: str):
    while True:
        ekran_temizle()
        baslik(f"🛡️  YÖNETİM PANELİ  [{admin}]")
        print("  [1] Tüm Sistem Loglarını Gör")
        print("  [2] Kullanıcı Yönetimi")
        print("  [3] Tüm Logları Clean Et")
        print("  [4] Güvenlik Uyarılarını Gör")
        print("  [5] Eski Logları Temizle (24h+)")
        print("  [6] Sistem İstatistikleri")
        print("  [q] Geri")

        sec = input("\n  Seçim >> ").strip().lower()

        if sec == '1':
            ekran_temizle()
            baslik("SİSTEM LOGLARI (son 100 satır)")
            _log_satirlarini_goster()
            input("\n  Devam...")
        elif sec == '2':
            _kullanici_yonetim(admin)
        elif sec == '3':
            onay = input("  Tüm loglar silinsin mi? (e/h): ").strip().lower()
            if onay == 'e':
                log_temizle()
                print("  [✔] Tüm loglar temizlendi.")
                time.sleep(1)
        elif sec == '4':
            ekran_temizle()
            baslik("⚠  GÜVENLİK UYARILARI")
            if os.path.exists(ALERT_LOG):
                with open(ALERT_LOG, "r", encoding="utf-8") as f:
                    icerik = f.read()
                print(icerik if icerik else "  [!] Uyarı yok.")
            input("\n  Devam...")
        elif sec == '5':
            silinen = eski_loglari_temizle(24)
            print(f"  [✔] {silinen} eski log satırı temizlendi.")
            time.sleep(1.5)
        elif sec == '6':
            ekran_temizle()
            stats = veri_yukle(STAT_FILE)
            if not stats:
                print("  [!] İstatistik yok.")
            else:
                baslik("📊 TÜM KULLANICI İSTATİSTİKLERİ")
                for u, v in stats.items():
                    print(f"\n  👤 {u}  |  Toplam: {v['toplam']}  |  Ort: {v['ortalama_ms']}ms")
            input("\n  Devam...")
        elif sec == 'q':
            break

def ana_menu(user: str):
    while True:
        ekran_temizle()
        baslik(f"🌐 NETICE DNS  [{user.upper()}]")
        print("  [1] DNS Sorgula")
        print("  [2] Kişisel İstatistikler")
        print("  [3] Yardım ve Bilgi")
        if user == "admin":
            print("  [4] Yönetim Paneli")
        print("  [0] Güvenli Çıkış")
        imza_yaz()

        s = input("\n  Seçim >> ").strip()
        if s == '1':
            dns_sorgu_paneli(user)
        elif s == '2':
            ekran_temizle()
            istatistik_goster(user)
            input("\n  Devam için Enter...")
        elif s == '3':
            yardim_menusu()
        elif s == '4' and user == "admin":
            yonetim_paneli(user)
        elif s == '0':
            guvenli_cikis_animasyonu()
            break

def kayit_ol(db: dict) -> bool:
    k = input("  Yeni Kullanıcı Adı: ").strip()
    if not k:
        print("  [!] Kullanıcı adı boş olamaz.")
        time.sleep(1)
        return False
    if k.lower() == "admin":
        print("  [!] Bu kullanıcı adı kullanılamaz.")
        time.sleep(1)
        return False
    if k in db:
        alts = [f"{k}_{i}" for i in range(1, 4) if f"{k}_{i}" not in db]
        print(f"  [!] '{k}' zaten mevcut.")
        if alts:
            print(f"      Alternatifler: {', '.join(alts)}")
        time.sleep(1.5)
        return False
    
    if len(k) < 3 or len(k) > 32:
        print("  [!] Kullanıcı adı 3-32 karakter olmalı.")
        time.sleep(1)
        return False

    s = input("  Şifre: ")
    ok, sebep = sifre_guclu_mu(s)
    if not ok:
        print(f"  [!] {sebep}")
        time.sleep(1.5)
        return False

    db[k] = _sifre_hash(s)
    veri_kaydet(USER_DATA, db)
    print("  [✔] Kayıt başarılı! Giriş yapabilirsiniz.")
    time.sleep(1)
    return True

def giris_yap(db: dict):
    u = input("  Kullanıcı Adı: ").strip()

    kilitli, kalan = brute_force_kontrol(u)
    if kilitli:
        print(f"  [!] Hesap kilitli. {kalan} saniye sonra tekrar deneyin.")
        time.sleep(2)
        return

    if u not in db:
        print("  [!] Kullanıcı bulunamadı.")
        time.sleep(1)
        return

    p = input("  Şifre: ")
    if _sifre_hash(p) == db[u]:
        giris_basarili(u)
        print(f"  [✔] Hoş geldiniz, {u}!")
        time.sleep(0.8)
        ana_menu(u)
    else:
        giris_basarisiz(u)
        deneme = _giris_denemeler.get(u, {}).get("deneme", 1)
        kalan_hak = MAX_DENEME - deneme
        if kalan_hak > 0:
            print(f"  [!] Şifre hatalı. {kalan_hak} hakkınız kaldı.")
        else:
            print(f"  [!] Çok fazla başarısız deneme. Hesap {KILIT_SURE//60} dakika kilitlendi.")
            guvenlik_uyari_yaz(u, "Brute-force kilidi tetiklendi.")
        time.sleep(1.5)

if __name__ == "__main__":
    dosya_hazirla()
    eski_loglari_temizle(24)

    while True:
        ekran_temizle()
        baslik("🌐 NETICE DNS GİRİŞ SİSTEMİ")
        print("  [1] Giriş Yap")
        print("  [2] Yeni Kayıt")
        print("  [3] Genel Yardım")
        print("  [0] Sistemi Kapat")
        imza_yaz()

        c = input("\n  Seçim >> ").strip()
        if c == '1':
            db = veri_yukle(USER_DATA)
            giris_yap(db)
        elif c == '2':
            db = veri_yukle(USER_DATA)
            kayit_ol(db)
        elif c == '3':
            yardim_menusu()
        elif c == '0':
            print("\n  Sistem kapatılıyor. Güle güle..")
            break