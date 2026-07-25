import re
from functools import wraps
import os
import hashlib
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
DB_NAME = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "car_market.db")
PER_PAGE = 12  # ✅ عدد السيارات في كل صفحة


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ====================================================
# Decorators
# ====================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "error")
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash("Access denied. Admins only.", "error")
            return redirect(url_for('cars'))
        return f(*args, **kwargs)
    return decorated_function


# ====================================================
# Auth
# ====================================================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('cars'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please fill in all fields", "error")
            return render_template('login.html')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user:
            stored_hash = user['password_hash']
            salt = user['salt']
            new_hash = hashlib.pbkdf2_hmac(
                'sha256', password.encode(), bytes.fromhex(salt), 100000
            ).hex()
            if new_hash == stored_hash:
                session['user_id'] = user['id']
                session['fullname'] = user['fullname']
                session['is_admin'] = bool(user['is_admin'])
                return redirect(url_for('cars'))
            else:
                flash("Incorrect password", "error")
        else:
            flash("User not found", "error")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not fullname or not email or not password:
            flash("Please fill in all fields", "error")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template('register.html')

        salt = os.urandom(16).hex()
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), bytes.fromhex(salt), 100000
        ).hex()

        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO users (fullname, email, password_hash, salt, is_admin) VALUES (?, ?, ?, ?, 0)',
                (fullname, email, password_hash, salt)
            )
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists", "error")

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']

    if request.method == 'POST':
        new_fullname = request.form.get('fullname', '').strip()

        if not new_fullname:
            flash("Name cannot be empty", "error")
            return redirect(url_for('profile'))

        if len(new_fullname) < 2:
            flash("Name must be at least 2 characters", "error")
            return redirect(url_for('profile'))

        conn = get_db()
        conn.execute(
            'UPDATE users SET fullname = ? WHERE id = ?',
            (new_fullname, user_id)
        )
        conn.commit()
        conn.close()

        # تحديث الاسم في الـ session فوراً
        session['fullname'] = new_fullname
        flash("Name updated successfully! ✅", "success")
        return redirect(url_for('profile'))

    # GET — جلب بيانات المستخدم الحالية
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?',
                        (user_id,)).fetchone()
    conn.close()

    return render_template('profile.html', user=user)


# ====================================================
# Cars + Pagination
# ====================================================

@app.route('/cars')
@login_required
def cars():
    search_query = request.args.get('q', '').strip() or None
    min_price = request.args.get('min_price') or None
    max_price = request.args.get('max_price') or None
    year = request.args.get('year') or None
    color = request.args.get('color') or None
    brand = request.args.get('brand') or None
    fuel_type = request.args.get('fuel_type') or None
    sort_by = request.args.get('sort_by') or None
    # ✅ رقم الصفحة الحالية
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    conn = get_db()

    brands = [r['brand'] for r in conn.execute(
        'SELECT DISTINCT brand     FROM cars ORDER BY brand').fetchall()]
    years = [r['year'] for r in conn.execute(
        'SELECT DISTINCT year      FROM cars ORDER BY year DESC').fetchall()]
    colors = [r['color'] for r in conn.execute(
        'SELECT DISTINCT color     FROM cars ORDER BY color').fetchall()]
    fuel_types = [r['fuel_type'] for r in conn.execute(
        'SELECT DISTINCT fuel_type FROM cars ORDER BY fuel_type').fetchall()]

    query = 'SELECT * FROM cars WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (name LIKE ? OR brand LIKE ?)'
        params += [f'%{search_query}%', f'%{search_query}%']

    try:
        if min_price:
            query += ' AND price >= ?'
            params.append(int(min_price))
        if max_price:
            query += ' AND price <= ?'
            params.append(int(max_price))
    except ValueError:
        pass

    if year and year != 'any':
        query += ' AND year = ?'
        params.append(int(year))

    if color and color != 'any':
        query += ' AND color = ?'
        params.append(color)

    if brand and brand != 'any':
        query += ' AND brand = ?'
        params.append(brand)

    if fuel_type and fuel_type != 'any':
        query += ' AND fuel_type = ?'
        params.append(fuel_type)

    sort_mapping = {
        'price_asc':  'price ASC',
        'price_desc': 'price DESC',
        'year_asc':   'year ASC',
        'year_desc':  'year DESC',
        'name_asc':   'name ASC',
        'name_desc':  'name DESC',
    }
    order_clause = sort_mapping.get(sort_by, 'id ASC')
    query += f' ORDER BY {order_clause}'

    # ✅ Pagination: نحسب العدد الكلي أولاً
    count_query = query.replace('SELECT *', 'SELECT COUNT(*)', 1)
    total_cars = conn.execute(count_query, params).fetchone()[0]
    total_pages = max(1, (total_cars + PER_PAGE - 1) // PER_PAGE)

    # نتأكد الصفحة ما تتجاوز الحد
    if page > total_pages:
        page = total_pages

    # ✅ LIMIT و OFFSET للـ Pagination
    query += f' LIMIT {PER_PAGE} OFFSET {(page - 1) * PER_PAGE}'
    cars_list = conn.execute(query, params).fetchall()
    wishlist_ids = _get_user_wishlist(conn, session['user_id'])
    conn.close()

    filters = {
        'min_price': min_price,
        'max_price': max_price,
        'year':      year,
        'color':     color,
        'brand':     brand,
        'fuel_type': fuel_type,
        'sort_by':   sort_by,
    }

    return render_template(
        'cars.html',
        cars=cars_list,
        search_word=search_query,
        filters=filters,
        brands=brands,
        years=years,
        colors=colors,
        fuel_types=fuel_types,
        wishlist_ids=wishlist_ids,
        page=page,
        total_pages=total_pages,
        total_cars=total_cars,
    )


@app.route('/car/<int:car_id>')
@login_required
def car_details(car_id):
    conn = get_db()
    car = conn.execute('SELECT * FROM cars WHERE id = ?', (car_id,)).fetchone()

    if car is None:
        conn.close()
        flash("Car not found!", "error")
        return redirect(url_for('cars'))

    wishlist_ids = _get_user_wishlist(conn, session['user_id'])

    # ✅ جلب كل التقييمات مع اسم المستخدم
    reviews = conn.execute("""
        SELECT reviews.rating, reviews.comment, reviews.created_at, users.fullname
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE reviews.car_id = ?
        ORDER BY reviews.created_at DESC
    """, (car_id,)).fetchall()

    # ✅ هل المستخدم الحالي قيّم هذه السيارة؟
    user_review = conn.execute(
        'SELECT * FROM reviews WHERE car_id = ? AND user_id = ?',
        (car_id, session['user_id'])
    ).fetchone()

    # ✅ المعدل الإجمالي
    avg_result = conn.execute(
        'SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE car_id = ?',
        (car_id,)
    ).fetchone()
    avg_rating = round(avg_result['avg_rating'],
                       1) if avg_result['avg_rating'] else None
    review_count = avg_result['count']

    conn.close()

    return render_template(
        'details.html',
        car=car,
        wishlist_ids=wishlist_ids,
        reviews=reviews,
        user_review=user_review,
        avg_rating=avg_rating,
        review_count=review_count,
    )


@app.route('/car/<int:car_id>/review', methods=['POST'])
@login_required
def add_review(car_id):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash("Please select a rating between 1 and 5", "error")
        return redirect(url_for('car_details', car_id=car_id))

    conn = get_db()
    existing = conn.execute(
        'SELECT 1 FROM reviews WHERE car_id = ? AND user_id = ?',
        (car_id, session['user_id'])
    ).fetchone()

    if existing:
        conn.execute(
            'UPDATE reviews SET rating=?, comment=?, created_at=datetime("now") WHERE car_id=? AND user_id=?',
            (rating, comment, car_id, session['user_id'])
        )
        flash("Your review has been updated! ✅", "success")
    else:
        conn.execute(
            'INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
            (car_id, session['user_id'], rating, comment)
        )
        flash("Review added! Thank you ⭐", "success")

    conn.commit()
    conn.close()
    return redirect(url_for('car_details', car_id=car_id))


@app.route('/car/<int:car_id>/delete_review')
@login_required
def delete_review(car_id):
    conn = get_db()
    conn.execute(
        'DELETE FROM reviews WHERE car_id = ? AND user_id = ?',
        (car_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    flash("Review deleted.", "info")
    return redirect(url_for('car_details', car_id=car_id))


# ====================================================
# Wishlist
# ====================================================

def _get_user_wishlist(conn, user_id):
    rows = conn.execute(
        'SELECT car_id FROM wishlists WHERE user_id = ?', (user_id,)
    ).fetchall()
    return [r['car_id'] for r in rows]


@app.route('/toggle_wishlist/<int:car_id>')
@login_required
def toggle_wishlist(car_id):
    user_id = session['user_id']
    conn = get_db()

    existing = conn.execute(
        'SELECT 1 FROM wishlists WHERE user_id = ? AND car_id = ?',
        (user_id, car_id)
    ).fetchone()

    if existing:
        conn.execute(
            'DELETE FROM wishlists WHERE user_id = ? AND car_id = ?', (user_id, car_id))
        flash("Removed from wishlist 💔", "info")
    else:
        conn.execute(
            'INSERT INTO wishlists (user_id, car_id) VALUES (?, ?)', (user_id, car_id))
        flash("Added to wishlist ❤️", "success")

    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('cars'))


@app.route('/api/toggle_wishlist/<int:car_id>', methods=['POST'])
@login_required
def api_toggle_wishlist(car_id):
    user_id = session['user_id']
    conn = get_db()

    existing = conn.execute(
        'SELECT 1 FROM wishlists WHERE user_id = ? AND car_id = ?',
        (user_id, car_id)
    ).fetchone()

    if existing:
        conn.execute(
            'DELETE FROM wishlists WHERE user_id = ? AND car_id = ?', (user_id, car_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'removed', 'car_id': car_id})
    else:
        conn.execute(
            'INSERT INTO wishlists (user_id, car_id) VALUES (?, ?)', (user_id, car_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'added', 'car_id': car_id})


@app.route('/wishlist')
@login_required
def wishlist():
    conn = get_db()
    wishlist_ids = _get_user_wishlist(conn, session['user_id'])

    if wishlist_ids:
        placeholders = ','.join('?' * len(wishlist_ids))
        cars_list = conn.execute(
            f'SELECT * FROM cars WHERE id IN ({placeholders})', wishlist_ids
        ).fetchall()
    else:
        cars_list = []

    conn.close()
    return render_template('wishlist.html', cars=cars_list, wishlist_ids=wishlist_ids)


# ====================================================
# Compare
# ====================================================

@app.route('/compare')
@login_required
def compare():
    car_ids = request.args.getlist('car_id')[:2]
    cars_to_compare = []

    if car_ids:
        conn = get_db()
        for cid in car_ids:
            car = conn.execute(
                'SELECT * FROM cars WHERE id = ?', (cid,)).fetchone()
            if car:
                cars_to_compare.append(car)
        conn.close()

    return render_template('compare.html', cars=cars_to_compare)


# ====================================================
# Admin
# ====================================================

@app.route('/admin')
@admin_required
def admin_panel():
    conn = get_db()
    cars = conn.execute('SELECT * FROM cars ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', cars=cars)


@app.route('/admin/add_car', methods=['POST'])
@admin_required
def add_car():
    name = request.form.get('name', '').strip()
    brand = request.form.get('brand', '').strip()
    price = request.form.get('price', '0')
    year = request.form.get('year', '2020')
    color = request.form.get('color', '').strip()
    fuel_type = request.form.get('fuel_type', '').strip()
    img = request.form.get('img', '').strip()
    # ✅ حقل description الجديد
    description = request.form.get('description', '').strip()

    if not all([name, brand, price, year, color, fuel_type, img]):
        flash("Please fill in all fields", "error")
        return redirect(url_for('admin_panel'))

    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO cars (name, brand, price, year, color, fuel_type, img, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (name, brand, int(price), int(year),
             color, fuel_type, img, description)
        )
        conn.commit()
        conn.close()
        flash("Car added successfully!", "success")
    except (ValueError, sqlite3.Error) as e:
        flash(f"Error adding car: {e}", "error")

    return redirect(url_for('admin_panel'))


@app.route('/admin/edit_car/<int:car_id>', methods=['POST'])
@admin_required
def edit_car(car_id):
    name = request.form.get('name', '').strip()
    brand = request.form.get('brand', '').strip()
    price = request.form.get('price', '0')
    year = request.form.get('year', '2020')
    color = request.form.get('color', '').strip()
    fuel_type = request.form.get('fuel_type', '').strip()
    img = request.form.get('img', '').strip()
    # ✅ حقل description الجديد
    description = request.form.get('description', '').strip()

    try:
        conn = get_db()
        conn.execute(
            'UPDATE cars SET name=?, brand=?, price=?, year=?, color=?, fuel_type=?, img=?, description=? WHERE id=?',
            (name, brand, int(price), int(year), color,
             fuel_type, img, description, car_id)
        )
        conn.commit()
        conn.close()
        flash("Car updated successfully!", "success")
    except (ValueError, sqlite3.Error) as e:
        flash(f"Error updating car: {e}", "error")

    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_car/<int:car_id>')
@admin_required
def delete_car(car_id):
    conn = get_db()
    conn.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    flash("Car deleted successfully!", "success")
    return redirect(url_for('admin_panel'))


# ====================================================
# Chatbot
# ====================================================

def _chatbot_fallback_reply(rows, budget, is_arabic):
    if not rows:
        if is_arabic:
            return "لا أستطيع إيجاد سيارة مناسبة داخل هذه الميزانية في الموقع حالياً."
        return "I couldn't find a car within this budget in our current list."

    best, others = rows[0], rows[1:]

    if is_arabic:
        reply = (f"أنسب خيار أراه لك هو: {best['name']} بسعر حوالي {best['price']}$، "
                 f"موديل {best['year']}, لون {best['color']}, ونوع الوقود {best['fuel_type']}.")
        if budget:
            reply += f" هذا الاختيار ضمن ميزانيتك تقريباً ({budget}$)."
        if others:
            reply += " كبدائل: " + "، ".join(r['name'] for r in others) + "."
    else:
        reply = (f"The car I recommend is: {best['name']} at about {best['price']}$, "
                 f"year {best['year']}, color {best['color']}, fuel type {best['fuel_type']}.")
        if budget:
            reply += f" This fits your budget (~{budget}$)."
        if others:
            reply += " Other options: " + \
                ", ".join(r['name'] for r in others) + "."

    return reply


@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()

    if not message:
        return jsonify({'reply': "Please type your question about cars or your budget."})

    is_arabic = any('\u0600' <= ch <= '\u06FF' for ch in message)
    lower_msg = message.lower()

    cleaned = message.replace(',', '').replace('$', '')
    numbers = re.findall(r'\d+', cleaned)
    budget = None
    try:
        if numbers:
            budget = int(numbers[0])
    except (ValueError, IndexError):
        budget = None

    # لا فلتر — Gemini نفسه بيتحكم بالردود

    conn = get_db()
    if budget:
        rows = conn.execute(
            "SELECT * FROM cars WHERE price <= ? ORDER BY year DESC, price DESC LIMIT 15",
            (budget,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM cars ORDER BY year DESC, price DESC LIMIT 15"
        ).fetchall()
    conn.close()

    cars_context = [
        f"- {r['name']} | {r['brand']} | {r['price']}$ | {r['year']} | {r['color']} | {r['fuel_type']}"
        for r in rows
    ]
    cars_text = "\n".join(
        cars_context) if cars_context else "No cars in this range."

    use_gemini = GEMINI_AVAILABLE and os.environ.get('GEMINI_API_KEY')
    reply = None

    if use_gemini:
        try:
            genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')

            lang_instruction = "Answer in Arabic only." if is_arabic else "Answer in English only."
            prompt = (
                f"You are the car advisor for this car market website. "
                f"You ONLY help users choose a car or recommend by budget from our inventory. "
                f"If the question is not about cars or budget, say you can only help with car recommendations.\n"
                f"Our current inventory (name | brand | price $ | year | color | fuel_type):\n{cars_text}\n"
                f"Use only the cars listed above. Be concise and helpful. {lang_instruction}\n\n"
                f"User: {message}"
            )

            response = model.generate_content(prompt)
            reply = (response.text or '').strip()
            if not reply:
                reply = _chatbot_fallback_reply(rows, budget, is_arabic)
        except Exception:
            reply = _chatbot_fallback_reply(rows, budget, is_arabic)

    if reply is None:
        reply = _chatbot_fallback_reply(rows, budget, is_arabic)

    return jsonify({'reply': reply})


# ====================================================
if __name__ == '__main__':
    app.run(debug=False)
