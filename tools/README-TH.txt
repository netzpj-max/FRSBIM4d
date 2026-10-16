Four Seasons Residences R01

ต้นฉบับเว็บอยู่ใน web/dist/index.html, style.css และ app.js แก้ไขแล้วรีเฟรชได้ทันที ไม่ต้อง build

rebuild_ifc.py ใช้ Python 3 และ standard library อ่าน data/elements.json, levels.json, project.json, drawings.json แล้วสร้าง model/Four-Seasons-Residences_R01.ifc ใหม่ โดยสำรอง IFC เดิมเป็น .ifc.bak ก่อน

คำสั่ง: python tools/rebuild_ifc.py

การแก้ชื่อ/วัสดุ/ราคาในเว็บอยู่ใน backup JSON ไม่ได้เขียนกลับ data/*.json อัตโนมัติ หากปรับ geometry ใน JSON ต้องคำนวณปริมาณ ตรวจสมมติฐาน และตรวจ IFC ใหม่ด้วยตัวอ่านอิสระก่อนใช้งาน
