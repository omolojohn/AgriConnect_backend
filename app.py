import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, Product, Order, OrderItem, Payment, Logistics, Feedback
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
from functools import wraps
import cloudinary, cloudinary.uploader, cloudinary.api
import requests
from requests.auth import HTTPBasicAuth
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

# Configure SQLite database URI , cloudinary and JWT
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://agriconnect_user:XRhihomCxxeX0PlsGUpeZfwM05MwMRDO@dpg-crle93m8ii6s73d9qrag-a.oregon-postgres.render.com/agriconnect'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '217ef16e1e9a07be79a7a4d9e3f20d027a3a274ad4dc215d582aca4d7a1a15d2'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)
app.config['CLOUDINARY_URL'] = 'cloudinary://456584813683358:N70vCZCBhr1dSsTVw_TFch6Euwt@dqfbde8ib'

# M-Pesa Configuration
app.config['MPESA_CONSUMER_KEY'] = 'SPzneIGYRgzWGO5B9CXINWjWa3nx9YE0sOisQFshwEIXEHqF'
app.config['MPESA_CONSUMER_SECRET'] = 'agaKNaGcKWf3DLgJGGRVmuDCewsNWejGVd5mMws1UwACij8DYHaNeGKnwv6AcAKT'
app.config['MPESA_SHORTCODE'] = 'N/A'
app.config['MPESA_LIPA_SHORTCODE'] = 'N/A'
app.config['MPESA_PASSKEY'] = 'N/A'
app.config['MPESA_ENVIRONMENT'] = 'sandbox'


cloudinary.config(
    cloud_name="dqfbde8ib",
    api_key="456584813683358",
    api_secret="-N70vCZCBhr1dSsTVw_TFch6Euw"
)

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# Utility Functions
def get_mpesa_token():
    base_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials' \
        if app.config['MPESA_ENVIRONMENT'] == 'sandbox' \
        else 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    consumer_key = app.config['MPESA_CONSUMER_KEY']
    consumer_secret = app.config['MPESA_CONSUMER_SECRET']
    
    response = requests.get(base_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception('Error getting M-Pesa token: {}'.format(response.text))

def lipa_na_mpesa_online(amount, phone_number, account_number):
    token = get_mpesa_token()
    base_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest' \
        if app.config['MPESA_ENVIRONMENT'] == 'sandbox' \
        else 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "BusinessShortCode": app.config['MPESA_LIPA_SHORTCODE'],
        "Password": generate_password(),
        "Timestamp": generate_timestamp(),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": app.config['MPESA_SHORTCODE'],
        "PhoneNumber": phone_number,
        "CallBackURL": "https://agriconnect-backend-2qop.onrender.com/callback",
        "AccountNumber": account_number,
        "TransactionDesc": "Payment for goods"
    }
    
    response = requests.post(base_url, json=payload, headers=headers)
    return response.json()

def generate_password():
    short_code = app.config['MPESA_LIPA_SHORTCODE']
    passkey = app.config['MPESA_PASSKEY']
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{short_code}{passkey}{timestamp}'.encode()).decode('utf-8')
    return password

def generate_timestamp():
    return datetime.now().strftime('%Y%m%d%H%M%S')


# Role-based access decorator
def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if user and user.role == role:

                return fn(*args, **kwargs)
            else:
                return jsonify({'message': 'Unauthorized access, insufficient permissions!'}), 403
        return decorator
    return wrapper

@app.route('/')
def index():
    return jsonify({"content": "Welcome to the fresh produce market, where farmers meet buyers!"})

# User registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data.get('role')
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

# User login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

# Get all users (Admin only)
@app.route('/users', methods=['GET'])
@role_required('admin')
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    users_query = User.query
    paginated_users = paginate_query(users_query, page, per_page)
    return jsonify({
        'users': [user.to_dict() for user in paginated_users.items],
        'total': paginated_users.total,
        'page': paginated_users.page,
        'pages': paginated_users.pages
    })

# Get a user by ID
@app.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.query.get(id)
    if user:
        return jsonify(user.to_dict())
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/users/<int:id>', methods=['PUT'])
@role_required('admin')
def update_user(id):
    data = request.get_json()
    user = User.query.get(id)
    if user:
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        db.session.commit()
        return jsonify(user.to_dict()), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/users/<int:id>', methods=['PATCH'])
@role_required('admin')
def patch_user(id):
    data = request.get_json()
    user = User.query.get(id)
    if user:
        if 'username' in data:
            user.username = data['username']
        if 'email' in data:
            user.email = data['email']
        if 'password_hash' in data:
            user.password_hash = data['password_hash']
        if 'role' in data:
            user.role = data['role']
        db.session.commit()
        return jsonify(user.to_dict()), 200
    else:
        return jsonify({'message': 'User not found'}), 404


# Delete a user (Admin only)
@app.route('/users/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_user(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404


# CRUD operation for products (Admin or Seller only)
@app.route('/products', methods=['POST'])
@role_required('admin')  # Only admin can create products
def create_product():
    data = request.get_json()
    image = request.files.get('image')
    if image:
        upload_result = cloudinary.upload(image)
        image_url = upload_result['url']
    else:
        image_url = data.get('image_url', '')

    new_product = Product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        stock=data['stock'],
        user_id=data['user_id'],
        image_url=image_url
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

@app.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    products = Product.query.paginate(page, per_page, False)
    products = Product.query.all()
    return jsonify({
        'total': products.total,
        'pages': products.pages,
        'current_page': products.pages,
        'products':[product.to_dict() for product in products]
        })

@app.route('/products/<int:id>', methods=['GET'])
@jwt_required()
def get_product(id):
    product = Product.query.get(id)
    if product:
        return jsonify(product.to_dict())
    else:
        return jsonify({'message': 'Product not found'}), 404

@app.route('/products/<int:id>', methods=['PUT'])
@role_required('admin')  # Only admin can update products
def update_product(id):
    data = request.get_json()
    product = Product.query.get(id)
    if product:
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.stock = data.get('stock', product.stock)
        db.session.commit()
        return jsonify(product.to_dict())
    else:
        return jsonify({'message': 'Product not found'}), 404

@app.route('/products/<int:id>', methods=['DELETE'])
@role_required('admin')  # Only admin can delete products
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted'}), 200
    else:
        return jsonify({'message': 'Product not found'}), 404

# CRUD operations for orders (Users and Admins)
@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    data = request.get_json()
    new_order = Order(
        total_price=data['total_price'],
        status=data['status'],
        user_id=data['user_id']
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.to_dict()), 201

@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    orders_query = Order.query
    paginated_orders = paginate_query(orders_query, page, per_page)
    return jsonify({
        'orders': [order.to_dict() for order in paginated_orders.items],
        'total': paginated_orders.total,
        'page': paginated_orders.page,
        'pages': paginated_orders.pages
    })

@app.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
def get_order(id):
    order = Order.query.get(id)
    if order:
        return jsonify(order.to_dict())
    else:
        return jsonify({'message': 'Order not found'}), 404

@app.route('/orders/<int:id>', methods=['PUT'])
@role_required('admin')  # Only admin can update orders
def update_order(id):
    data = request.get_json()
    order = Order.query.get(id)
    if order:
        order.total_price = data.get('total_price', order.total_price)
        order.status = data.get('status', order.status)
        db.session.commit()
        return jsonify(order.to_dict())
    else:
        return jsonify({'message': 'Order not found'}), 404

@app.route('/orders/<int:id>', methods=['DELETE'])
@role_required('admin')  # Only admin can delete orders
def delete_order(id):
    order = Order.query.get(id)
    if order:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order deleted'}), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

# CRUD operations for OrderItems (Users and Admins)
@app.route('/order-items', methods=['POST'])
@jwt_required()
def create_order_item():
    data = request.get_json()
    new_order_item = OrderItem(
        quantity=data['quantity'],
        price=data['price'],
        product_id=data['product_id'],
        order_id=data['order_id']
    )
    db.session.add(new_order_item)
    db.session.commit()
    return jsonify(new_order_item.to_dict()), 201

@app.route('/order-items', methods=['GET'])
@jwt_required()
def get_order_items():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    order_items_query = OrderItem.query
    paginated_order_items = paginate_query(order_items_query, page, per_page)
    return jsonify({
        'order_items': [order_item.to_dict() for order_item in paginated_order_items.items],
        'total': paginated_order_items.total,
        'page': paginated_order_items.page,
        'pages': paginated_order_items.pages
    })

@app.route('/order-items/<int:id>', methods=['GET'])
@jwt_required()
def get_order_item(id):
    order_item = OrderItem.query.get(id)
    if order_item:
        return jsonify(order_item.to_dict())
    else:
        return jsonify({'message': 'Order Item not found'}), 404

@app.route('/order-items/<int:id>', methods=['PUT'])
@role_required('admin')  # Only admin can update order items
def update_order_item(id):
    data = request.get_json()
    order_item = OrderItem.query.get(id)
    if order_item:
        order_item.quantity = data.get('quantity', order_item.quantity)
        order_item.price = data.get('price', order_item.price)
        db.session.commit()
        return jsonify(order_item.to_dict())
    else:
        return jsonify({'message': 'Order Item not found'}), 404

@app.route('/order-items/<int:id>', methods=['DELETE'])
@role_required('admin')  # Only admin can delete order items
def delete_order_item(id):
    order_item = OrderItem.query.get(id)
    if order_item:
        db.session.delete(order_item)
        db.session.commit()
        return jsonify({'message': 'Order Item deleted'}), 200
    else:
        return jsonify({'message': 'Order Item not found'}), 404

# CRUD operations for Payments (Users and Admins)
@app.route('/payments', methods=['POST'])
@jwt_required()
def create_payment():
    data = request.get_json()
    new_payment = Payment(
        amount=data['amount'],
        payment_method=data['payment_method'],
        status=data['status'],
        order_id=data['order_id']
    )
    db.session.add(new_payment)
    db.session.commit()
    return jsonify(new_payment.to_dict()), 201

@app.route('/payments', methods=['GET'])
@jwt_required()
def get_payments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    payments_query = Payment.query
    paginated_payments = paginate_query(payments_query, page, per_page)
    return jsonify({
        'payments': [payment.to_dict() for payment in paginated_payments.items],
        'total': paginated_payments.total,
        'page': paginated_payments.page,
        'pages': paginated_payments.pages
    })

@app.route('/payments/<int:id>', methods=['GET'])
@jwt_required()
def get_payment(id):
    payment = Payment.query.get(id)
    if payment:
        return jsonify(payment.to_dict())
    else:
        return jsonify({'message': 'Payment not found'}), 404

@app.route('/payments/<int:id>', methods=['PUT'])
@role_required('admin')  # Only admin can update payments
def update_payment(id):
    data = request.get_json()
    payment = Payment.query.get(id)
    if payment:
        payment.amount = data.get('amount', payment.amount)
        payment.payment_method = data.get('payment_method', payment.payment_method)
        payment.status = data.get('status', payment.status)
        db.session.commit()
        return jsonify(payment.to_dict())
    else:
        return jsonify({'message': 'Payment not found'}), 404

@app.route('/payments/<int:id>', methods=['DELETE'])
@role_required('admin')  # Only admin can delete payments
def delete_payment(id):
    payment = Payment.query.get(id)
    if payment:
        db.session.delete(payment)
        db.session.commit()
        return jsonify({'message': 'Payment deleted'}), 200
    else:
        return jsonify({'message': 'Payment not found'}), 404

# CRUD operations for Logistics (Admin only)
@app.route('/logistics', methods=['POST'])
@role_required('admin')
def create_logistics():
    data = request.get_json()
    new_logistics = Logistics(
        company=data['company'],
        tracking_number=data['tracking_number'],
        status=data['status'],
        order_id=data['order_id']
    )
    db.session.add(new_logistics)
    db.session.commit()
    return jsonify(new_logistics.to_dict()), 201

@app.route('/logistics', methods=['GET'])
@role_required('admin')
def get_logistics():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    logistics_query = Logistics.query
    paginated_logistics = paginate_query(logistics_query, page, per_page)
    return jsonify({
        'logistics': [logistic.to_dict() for logistic in paginated_logistics.items],
        'total': paginated_logistics.total,
        'page': paginated_logistics.page,
        'pages': paginated_logistics.pages
    })

@app.route('/logistics/<int:id>', methods=['GET'])
@role_required('admin')
def get_logistic(id):
    logistic = Logistics.query.get(id)
    if logistic:
        return jsonify(logistic.to_dict())
    else:
        return jsonify({'message': 'Logistics record not found'}), 404

@app.route('/logistics/<int:id>', methods=['PUT'])
@role_required('admin')
def update_logistic(id):
    data = request.get_json()
    logistic = Logistics.query.get(id)
    if logistic:
        logistic.company = data.get('company', logistic.company)
        logistic.tracking_number = data.get('tracking_number', logistic.tracking_number)
        logistic.status = data.get('status', logistic.status)
        db.session.commit()
        return jsonify(logistic.to_dict())
    else:
        return jsonify({'message': 'Logistics record not found'}), 404

@app.route('/logistics/<int:id>', methods=['DELETE'])
@role_required('admin')
def delete_logistic(id):
    logistic = Logistics.query.get(id)
    if logistic:
        db.session.delete(logistic)
        db.session.commit()
        return jsonify({'message': 'Logistics record deleted'}), 200
    else:
        return jsonify({'message': 'Logistics record not found'}), 404

# CRUD operations for Feedback (Users and Admins)
@app.route('/feedback', methods=['POST'])
@jwt_required()
def create_feedback():
    data = request.get_json()
    new_feedback = Feedback(
        rating=data['rating'],
        comment=data['comment'],
        user_id=data['user_id'],
        product_id=data['product_id']
    )
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify(new_feedback.to_dict()), 201

@app.route('/feedback', methods=['GET'])
@jwt_required()
def get_feedback():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    feedback_query = Feedback.query
    paginated_feedback = paginate_query(feedback_query, page, per_page)
    return jsonify({
        'feedback': [fb.to_dict() for fb in paginated_feedback.items],
        'total': paginated_feedback.total,
        'page': paginated_feedback.page,
        'pages': paginated_feedback.pages
    })

@app.route('/feedback/<int:id>', methods=['GET'])
@jwt_required()
def get_feedback_by_id(id):
    feedback = Feedback.query.get(id)
    if feedback:
        return jsonify(feedback.to_dict())
    else:
        return jsonify({'message': 'Feedback not found'}), 404

@app.route('/feedback/<int:id>', methods=['PUT'])
@role_required('admin')  # Only admin can update feedback
def update_feedback(id):
    data = request.get_json()
    feedback = Feedback.query.get(id)
    if feedback:
        feedback.rating = data.get('rating', feedback.rating)
        feedback.comment = data.get('comment', feedback.comment)
        db.session.commit()
        return jsonify(feedback.to_dict())
    else:
        return jsonify({'message': 'Feedback not found'}), 404

@app.route('/feedback/<int:id>', methods=['DELETE'])
@role_required('admin')  # Only admin can delete feedback
def delete_feedback(id):
    feedback = Feedback.query.get(id)
    if feedback:
        db.session.delete(feedback)
        db.session.commit()
        return jsonify({'message': 'Feedback deleted'}), 200
    else:
        return jsonify({'message': 'Feedback not found'}), 404

# M-Pesa Integration Routes
@app.route('/pay', methods=['POST'])
@jwt_required()
def pay():
    data = request.get_json()
    amount = data['amount']
    phone_number = data['phone_number']
    account_number = data.get('account_number', '')

    response = lipa_na_mpesa_online(amount, phone_number, account_number)
    return jsonify(response), 200

@app.route('/callback', methods=['POST'])
def callback():
    data = request.get_json()
    # Process the payment result here
    return jsonify({'message': 'Callback received'}), 200


if __name__ == '__main__':
    app.run(port=5555, debug=True)
