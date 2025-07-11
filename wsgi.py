# wsgi.py (หรืออาจจะชื่อ app_cli.py ก็ได้)

from app import create_app # นำเข้า create_app

app = create_app() # Flask CLI จะใช้ app ตัวนี้

# ไม่ต้องมี if __name__ == '__main__': ตรงนี้