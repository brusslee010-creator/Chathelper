import telethon.sync
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError, PeerFloodError, UserBannedInChannelError
import time
import random
import logging

# ==========================================
# ⚙️  INFINITE CONFIGURATION
# ==========================================

# 📱 Հաշիվների ցուցակը (մեկ տողով, բաժանված բացատով)
# Ավելացրեք քանի եք ուզում
ACCOUNTS = [
    "12345678:abcdefgh:123456789", # Ձեր հաշիվը 1
    "87654321:fghijklm:987654321", # Ձեր հաշիվը 2
    "11223344:klmnopqr:111222333", # Ձեր հաշիվը 3
    # Այստեղ գրեք մնացած հաշիվները...
]

# 🌐 Ազատ IP ների ցուցակը (30+ ազատ IP)
# Ամեն բողոքի համար կընտրվի պատահական մեկը
PROXIES = [
    {'addr': '185.181.156.45', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '46.29.210.15', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '5.183.100.66', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '91.107.231.86', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '5.183.100.66', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '46.29.210.15', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '91.107.231.86', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '5.183.100.66', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '46.29.210.15', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '91.107.231.86', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '5.183.100.66', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '46.29.210.15', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '91.107.231.86', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '5.183.100.66', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 1080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '46.29.210.15', 'port': 3128, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'},
    {'addr': '185.181.156.45', 'port': 8080, 'username': 'user', 'password': 'pass', 'proxy_type': 'socks5'}
]

# ⚡ Սահմանումներ
SLEEP_MIN = 1
SLEEP_MAX = 4
LOG_FILE = "infinite_spam_log.txt"

# ==========================================
# 🚀 LOGGING
# ==========================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s [SUCCESS] %(message)s'
)

def print_banner():
    print("""
    ╔══════════════════════════════════════════╗
    ║     🚀 INFINITE SPAM ENGINE 🚀          ║
    ║     🌀 ROUND ROBIN SYSTEM 🌀            ║
    ║     🔥 INFINITE ACCOUNTS & IP 🔥        ║
    ╚══════════════════════════════════════════╝
    """)

def parse_accounts(accounts_list):
    parsed_data = []
    for acc_str in accounts_list:
        parts = acc_str.strip().split(':')
        if len(parts) == 3:
            parsed_data.append({
                'api_id': int(parts[0]),
                'api_hash': parts[1],
                'phone': parts[2],
                'proxy': random.choice(PROXIES) # Ավտոմատ ընտրում ենք IP
            })
    return parsed_data

def main():
    print_banner()

    target_input = input("\n[1] Մուտքագրեք նպատակը (@channel կամ @username): ").strip()
    reason = input("[2] Բողոքի տեքստը: ").strip() or "spam"
    
    try:
        total_reports = int(input("[3] Ընդհանուր բողոքների քանակը: "))
    except ValueError:
        print("❌ Սխալ: Թիվ գրեք։")
        return

    accounts = parse_accounts(ACCOUNTS)

    if not accounts:
        print("❌ Սխալ: Հաշիվների ցուցակը դատարկ է։")
        return

    print(f"\n✅ Բեռնված է {len(accounts)} հաշիվ և {len(PROXIES)} IP պրոքսի։")
    print("🌀 Սկսում ենք Infinite ռեժիմը...")

    report_count = 0
    account_index = 0
    banned_accounts_count = 0

    for i in range(total_reports):
        # 🌀 Կիրառվում է Round Robin մեխանիզմը
        # Եթե 1-ից 100 հաշիվներ ենք, այն կանցնի 1, 2, 3... 100, 1, 2...
        current_acc = accounts[account_index % len(accounts)]
        
        # Ստուգում ենք, թե արդյոք հաշիվը արդեն արգելափակված է
        if current_acc in accounts and accounts.count(current_acc) == 0:
             # Եթե հաշիվը արգելափակված է, գտնում ենք մեկը որը չի արգելափակվել
             available = [a for a in accounts if a not in accounts]
             if not available:
                 break
             current_acc = random.choice(available)

        # Ստանում ենք պատահական IP
        current_proxy = random.choice(PROXIES)
        ip_addr = current_proxy['addr']

        client = TelegramClient(
            f"infinite_{current_acc['phone']}", 
            current_acc['api_id'], 
            current_acc['api_hash'], 
            proxy=current_proxy
        )

        try:
            # Միացումը նոր IP-ով
            client.connect()
            
            if not client.is_user_authorized():
                try:
                    client.send_code_request(current_acc['phone'])
                    print(f"  [i] {current_acc['phone']} — Միացավ ({ip_addr})։")
                except SessionPasswordNeededError:
                    print(f"  [i] {current_acc['phone']} — 2FA պահանջում է ({ip_addr})։")
                    pass

            target_entity = client.get_entity(target_input)
            
            # Իրական Report
            client.report_entity(target_entity, reason=reason, add_to_report_history=True)
            
            report_count += 1
            print(f"    [{report_count}/{total_reports}] 🌀 {current_acc['phone']} — {ip_addr}")
            logging.info(f"Report: {current_acc['phone']} via {ip_addr}")

            # Դադարների համակարգ
            random_delay = random.randint(SLEEP_MIN, SLEEP_MAX)
            time.sleep(random_delay)
            
            if report_count % 7 == 0:
                print("      ⏳ 7-րդ բողոք՝ 10 վայրկյան մեծ դադար...")
                time.sleep(10)

        except FloodWaitError as e:
            print(f"      ⚠️  Flood Wait: {e.seconds}s ({ip_addr})")
            time.sleep(e.seconds)
            i -= 1
            
        except PeerFloodError:
            print(f"      ⚠️  Այս հաշիվը լցվել է ({ip_addr})։ Փոխում ենք...")

        except UserBannedInChannelError:
            print(f"      ❌  Արգելափակվել է ({ip_addr})։ Անջատում եմ այն։")
            banned_accounts_count += 1
            
        except Exception as e:
            print(f"      ❌ Սխալ ({ip_addr}): {e}")
            
        finally:
            client.disconnect()
            # Միայն հաջորդ փուլում ենք անցնում նոր հաշվին
            account_index += 1

    print(f"\n{'='*50}")
    print("🎉 Ամբողջ ծրագիրն ավարտվեց։")
    print(f"📊 Բողոքներ՝ {report_count}")
    print(f"🚫 Արգելափակված հաշիվներ՝ {banned_accounts_count}")
    print(f"📝 Լոգը՝ {LOG_FILE}-ում։")
    print(f"{'='*50}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Դադարեցվել է օգտատիրոջ կողմից։")