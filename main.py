import secrets
import base64

from flask import Flask, render_template, request, redirect, url_for, session
import pymysql

app = Flask(__name__, template_folder="./")

app.secret_key = secrets.token_hex(16)

# Конфігурація бази даних
db = pymysql.connect(host='localhost', user='root', password='', db='cafe_db', charset='utf8mb4')
cursor = db.cursor()

@app.route('/demo')
def demo():

    return render_template('exportToHTML/main.py.html')

@app.route('/')
def index():
    # Отримання списку готелів з бази даних

    return render_template('index.html')

@app.route('/shake')
def shake():

    return render_template('pages/shake.html')

@app.route('/about')
def about():

    return render_template('pages/about.html')

@app.route('/order')
def order():

    cursor.execute("SELECT * FROM orders where User_ID = %s and Status_ID < %s", (session['username'],3))
    order = cursor.fetchone()
    cursor.execute("""SELECT ordered_items.ID, ordered_items.Order_ID, product.Name, ordered_items.Quantity, ordered_items.PricePerUnit 
    FROM ordered_items 
    join product on ordered_items.Item = product.ID
    where Order_ID = %s
                   """, (order[0],))
    order_items = cursor.fetchall()
    print(order_items)
    cursor.execute("SELECT * FROM order_status")
    order_statuses = cursor.fetchall()
    cursor.execute("SELECT * FROM delivery")
    deliveries = cursor.fetchall()
    cursor.execute("SELECT * FROM payment")
    payments = cursor.fetchall()
    return render_template('pages/order.html',payments=payments, order=order, order_items=order_items, order_statuses=order_statuses, deliveries=deliveries)


@app.route('/add_to_order',methods=['GET','POST'])
def add_to_order():

    return redirect(url_for('order'))

@app.route('/delete_from_order',methods=['GET','POST'])
def delete_from_order():
    if request.method == 'POST':
        item = request.form['item']
        order_id = request.form['order_id']
        cursor.execute("DELETE FROM ordered_items WHERE Item = %s and Order_ID = %s", (item, order_id))
        db.commit()

        return redirect(url_for('order'))

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    # Get the selected payment method, delivery method, and delivery address from the form
    payment_method = request.form.get('payment_method')
    delivery_method = request.form.get('delivery_method')
    delivery_address = request.form.get('delivery_address')
    order_id = request.form['id_order']

    cursor.execute("SELECT * FROM ordered_items where Order_ID = %s", (order_id,))
    order_items = cursor.fetchall()
    # Calculate the total order price based on the items in the order_items list
    total_price = 0
    for item in order_items:
        total_price += item[3] * item[4]

    # Update the order status to "2" in the database
    cursor.execute("UPDATE orders SET Status_ID = %s WHERE ID = %s", (2, order_id))
    cursor.execute("UPDATE orders SET Delivery_ID = %s WHERE ID = %s", (payment_method, order_id))
    cursor.execute("UPDATE orders SET Payment_ID = %s WHERE ID = %s", (delivery_method, order_id))
    cursor.execute("UPDATE orders SET TotalAmount = %s WHERE ID = %s", (total_price, order_id))

    db.commit()

    # Redirect the user back to the order page
    return redirect(url_for('profile'))


@app.route('/profile')
def profile():

    cursor.execute("SELECT * FROM users WHERE ID = %s", (session['username'],))
    user = cursor.fetchone()

    cursor.execute("""
        SELECT orders.ID, orders.Date, orders.TotalAmount, order_status.Name FROM orders 
        JOIN order_status ON orders.Status_ID = order_status.ID
        WHERE User_ID = %s
    """, (session['username'],))
    orders = cursor.fetchall()

    orders_with_items = []
    for order in orders:
        cursor.execute("""
            SELECT ordered_items.Order_ID, ordered_items.Item, product.Name, ordered_items.Quantity
            FROM ordered_items
            JOIN orders ON ordered_items.Order_ID = orders.ID
            JOIN product ON ordered_items.Item = product.ID
            WHERE ordered_items.Order_ID = %s
        """, (order[0],))
        order_items = cursor.fetchall()
        orders_with_items.append((order, order_items))

    return render_template('pages/profile.html', user=user, orders_with_items=orders_with_items)



@app.route('/manager')
def manager():
    cursor.execute("SELECT * FROM orders")
    orders  = cursor.fetchone()

    return render_template('pages/manager.html', orders=orders)

@app.route('/product')
def product():

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    encoded_product = []
    for product in products:
        photo_data = base64.b64encode(product[4]).decode('utf-8')

        encoded_product.append((product[0], product[1], product[2], product[3],photo_data, product[5]))

    return render_template('pages/products.html', categories=categories, products=encoded_product)

@app.route('/product/<int:product_id>')
def product_item(product_id):

    cursor.execute("SELECT * FROM product where ID = %s", (product_id,))
    product_s = cursor.fetchone()
    photo_data = base64.b64encode(product_s[4]).decode('utf-8')
    product = []
    product.append(product_s[0])
    product.append(product_s[1])
    product.append(product_s[2])
    product.append(product_s[3])
    product.append(photo_data)
    product.append(product_s[5])
    return render_template('pages/product_item.html', product=product)

# Сторінка авторизації
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Перевірка введених даних з базою даних
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        if user:
            # Авторизація успішна, збереження ідентифікатора користувача у сесії
            session['username'] = user[0]
            return redirect(url_for('index'))
        else:
            # Авторизація невдала, повідомлення про помилку
            error = 'Невірний електронний лист або пароль.'
            return render_template('templates/login.html', error=error)
    else:
        return render_template('templates/login_form.html')


# Сторінка реєстрації
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        country = request.form['country']
        language = request.form['language']

        # Перевірка, чи користувач з вказаним електронним листом вже існує
        cursor.execute("SELECT * FROM users WHERE email = %s", email)
        existing_user = cursor.fetchone()

        if existing_user:
            # Користувач вже існує, повідомлення про помилку
            error = 'Користувач з таким електронним листом уже існує.'
            return render_template('templates/register_form.html', error=error)
        else:
            # Додавання нового користувача до бази даних
            cursor.execute("INSERT INTO users (name, email, password, country, language) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, password, country, language))
            db.commit()

            return redirect(url_for('login'))
    else:
        return render_template('templates/register_form.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':

        session.pop('username', None)
        session.pop('user_id', None)

    return redirect('/')



if __name__ == '__main__':
    app.run(debug=True)
