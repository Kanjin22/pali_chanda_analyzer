# run.py (แก้ไข)

from app import create_app, db # นำเข้า create_app และ db

app = create_app() # สร้าง app instance

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # สร้างตารางใน DB ถ้ายังไม่มี
    app.run(debug=True)