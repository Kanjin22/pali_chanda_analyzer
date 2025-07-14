# app/cli.py
import click
from .extensions import db
from .models import User

def register_commands(app):
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("password")
    def create_admin(username, password):
        """
        สร้างผู้ดูแลระบบใหม่ หรืออัปเดตรหัสผ่านของผู้ดูแลระบบที่มีอยู่
        (ตั้งค่า is_admin เป็น True)
        ตัวอย่าง: flask create-admin admin_pali supersecretpassword123
        """
        user = User.query.filter_by(username=username).first()
        if user:
            click.echo(f"ผู้ใช้ '{username}' มีอยู่แล้ว, กำลังอัปเดตรหัสผ่านและสิทธิ์แอดมิน...")
            user.set_password(password)
            user.is_admin = True 
        else:
            click.echo(f"กำลังสร้างผู้ใช้ใหม่ '{username}' พร้อมสิทธิ์แอดมิน...")
            user = User(username=username, is_admin=True) 
            user.set_password(password)
            db.session.add(user)
        
        try:
            db.session.commit()
            click.echo(f"ผู้ใช้ '{username}' ถูกสร้าง/อัปเดตพร้อมสิทธิ์แอดมินเรียบร้อยแล้ว")
        except Exception as e:
            db.session.rollback()
            click.echo(f"เกิดข้อผิดพลาดในการสร้าง/อัปเดตผู้ใช้: {e}")

    @app.cli.command("seed-chanda-data")
    def seed_chanda_data_command():
        """
        เติมข้อมูลฉันท์พื้นฐานและรูปแบบย่อยของอุปชาติลงในฐานข้อมูล
        ตัวอย่าง: flask seed-chanda-data
        """
        from . import models 
        click.echo("กำลังเติมข้อมูลฉันท์...")
        
        indavajira = models.Chanda.query.filter_by(name='อินทรวิเชียรฉันท์ ๑๑').first()
        if not indavajira:
            indavajira = models.Chanda(name='อินทรวิเชียรฉันท์ ๑๑', pattern='––U––UU–U––', syllable_count=11, description_short='อินทรวิเชียรฉันท์ ๑๑ มีคณะ ต ต ช ครุลอย ๒')
            db.session.add(indavajira)

        upendavajira = models.Chanda.query.filter_by(name='อุเปนทรวิเชียรฉันท์ ๑๑').first()
        if not upendavajira:
            upendavajira = models.Chanda(name='อุเปนทรวิเชียรฉันท์ ๑๑', pattern='U–U––UU–U––', syllable_count=11, description_short='อุเปนทรวิเชียรฉันท์ ๑๑ มีคณะ ช ต ช ครุลอย ๒')
            db.session.add(upendavajira)

        upajati_chanda = models.Chanda.query.filter_by(name='อุปชาติฉันท์ ๑๑').first()
        if not upajati_chanda:
            upajati_chanda = models.Chanda(name='อุปชาติฉันท์ ๑๑', pattern=None, syllable_count=11, is_mixed_chanda=True, description_short='อุปชาติฉันท์ ๑๑ เป็นฉันท์ผสมระหว่างอินทรวิเชียรและอุเปนทรวิเชียรใน ๔ บาทของคาถา')
            db.session.add(upajati_chanda)
        
        try:
            db.session.commit() 
            click.echo("Chanda หลักถูกบันทึกแล้ว.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"เกิดข้อผิดพลาดในการบันทึก Chanda หลัก: {e}")
            return 

        upajati_sub_types_data = [
            {"name": "ชาลา", "sequence_pattern": "อิอิอิอุ"},
            {"name": "สาลา", "sequence_pattern": "อิอิอุอิ"},
            {"name": "รามา", "sequence_pattern": "อิอิอุอุ"},
            {"name": "วาณี", "sequence_pattern": "อิอุอิอิ"},
            {"name": "ภัททา", "sequence_pattern": "อิอุอิอุ"},
            {"name": "มายา", "sequence_pattern": "อิอุอุอิ"},
            {"name": "พุทธิ", "sequence_pattern": "อิอุอุอุ"},
            {"name": "กิตติ", "sequence_pattern": "อุอิอิอิ"},
            {"name": "อัททา", "sequence_pattern": "อุอิอิอุ"},
            {"name": "หังสี", "sequence_pattern": "อุอิอุอิ"},
            {"name": "อิทธิ", "sequence_pattern": "อุอิอุอุ"},
            {"name": "มาลา", "sequence_pattern": "อุอุอิอิ"},
            {"name": "เปมา", "sequence_pattern": "อุอุอิอุ"},
            {"name": "พาลา", "sequence_pattern": "อุอุอุอิ"},
        ]

        for data in upajati_sub_types_data:
            sub_type = models.UpajatiSubType.query.filter_by(sequence_pattern=data['sequence_pattern']).first()
            if not sub_type:
                sub_type = models.UpajatiSubType(
                    name=data['name'],
                    sequence_pattern=data['sequence_pattern'],
                    chanda_id=upajati_chanda.id
                )
                db.session.add(sub_type)
        
        try:
            db.session.commit()
            click.echo("UpajatiSubType data ถูกบันทึกแล้ว.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"เกิดข้อผิดพลาดในการบันทึก UpajatiSubType: {e}")