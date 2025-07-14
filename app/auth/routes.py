# app/auth/routes.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User 
from app.extensions import db 

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # ถ้าล็อกอินอยู่แล้ว
        if current_user.is_administrator():
            return redirect(url_for('admin.index')) # ถ้าเป็นแอดมิน ไปหน้า admin.index
        else:
            return redirect(url_for('main.index')) # ถ้าผู้ใช้ทั่วไป ไปหน้าหลัก
        

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=request.form.get('remember_me'))
        
        next_page = request.args.get('next') # ดึง 'next' parameter ถ้ามี (มาจาก login_required)
        
        if next_page: 
            return redirect(next_page) # ถ้ามีหน้าที่ต้องการไปก่อนหน้านี้ ให้ไปที่นั่น
        elif user.is_administrator(): 
            return redirect(url_for('admin.index')) # ถ้าเป็นแอดมิน ให้ไปหน้าผู้ดูแลระบบ (index)
        else: 
            return redirect(url_for('main.index')) # ถ้าผู้ใช้ทั่วไป ให้ไปหน้าหลัก

    return render_template('auth/login.html', title='เข้าสู่ระบบ')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('main.index'))

# ... (routes อื่นๆ ใน auth blueprint เช่น register ถ้ามี) ...