"""
سكريبت لتحديث روابط صور السيارات دفعة وحدة.

طريقة الاستخدام:
1. عبّي القاموس تحت: رقم السيارة (id) -> رابط الصورة الجديد.
   (خد الأرقام من عمود id بجدول السيارات — أو شغّل السكريبت بدون تعديل
   ليطبعلك أسماء كل السيارات وأرقامها الأول.)
2. شغّل: python update_images.py
"""

import sqlite3

DB_PATH = "car_market.db"

# 👇 عبّي هون: car_id -> رابط الصورة الجديد
new_images = {
    # 1: "https://example.com/toyota-corolla.jpg",
    # 2: "https://example.com/bmw-m5.jpg",
}

def list_cars():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT id, name, brand, year, img FROM cars ORDER BY id")
    print(f"{'ID':<4} {'Name':<25} {'Current Image'}")
    print("-" * 70)
    for row in cur:
        img_status = row["img"] if row["img"] else "(EMPTY)"
        print(f"{row['id']:<4} {row['name']:<25} {img_status[:45]}")
    conn.close()

def apply_updates():
    if not new_images:
        print("ما في صور مضافة بالقاموس new_images بعد. عبّيه وشغّل السكريبت كمان مرة.\n")
        list_cars()
        return

    conn = sqlite3.connect(DB_PATH)
    updated = 0
    for car_id, img_url in new_images.items():
        cur = conn.execute("SELECT id FROM cars WHERE id = ?", (car_id,))
        if cur.fetchone() is None:
            print(f"⚠️  ما في سيارة بالرقم {car_id} — تم التجاوز.")
            continue
        conn.execute("UPDATE cars SET img = ? WHERE id = ?", (img_url, car_id))
        updated += 1
        print(f"✅ تم تحديث صورة السيارة رقم {car_id}")
    conn.commit()
    conn.close()
    print(f"\nخلص! تم تحديث {updated} صورة.")

if __name__ == "__main__":
    apply_updates()
