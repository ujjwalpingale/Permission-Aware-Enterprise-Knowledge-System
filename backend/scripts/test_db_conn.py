import pymysql

passwords = ['', 'root', 'admin', 'password', '123456', '1234', '12345678', 'mysql', 'root123', 'Password123!', 'Password123']

for p in passwords:
    try:
        conn = pymysql.connect(host='localhost', user='root', password=p, port=3306)
        print(f"SUCCESS: Connected to MySQL root with password: '{p}'")
        conn.close()
        break
    except Exception as e:
        print(f"Attempt with password '{p}' failed: {e}")
