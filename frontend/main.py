from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, template_folder='templates', static_folder='static')

# Serve main HTML pages
@app.route('/')
def home():
    return render_template('index.html', page_title='Home')

# Use a single route for product details with both formats supported
@app.route('/products/<product_id>')
@app.route('/products/<product_id>.html')
def product_detail(product_id):
    return render_template('product_detail.html', page_title='Product Details', product_id=product_id)

@app.route('/login')
def login_page():
    return render_template('login.html', page_title='Login')

@app.route('/register')
def register_page():
    return render_template('register.html', page_title='Register')

@app.route('/cart')
def cart_page():
    return render_template('cart.html', page_title='Shopping Cart')

@app.route('/profile')
def profile_page():
    return render_template('profile.html', page_title='User Profile')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html', page_title='Checkout')

@app.route('/orders')
def orders_page():
    return render_template('orders.html', page_title='Order History')

@app.route('/admin')
def admin_page():
    return render_template('admin_products.html', page_title='Admin Dashboard')

# Serve static files (CSS, JS)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
