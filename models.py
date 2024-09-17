from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='farmer', lazy=True)
    orders = db.relationship('Order', backref='buyer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key linking product to the farmer (user who created the product)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    feedback = db.relationship('Feedback', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),
            'stock': self.stock,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    total_price = db.Column(db.Numeric, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key linking order to the buyer (user who placed the order)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', backref='order', lazy=True, uselist=False)
    logistics = db.relationship('Logistics', backref='order', lazy=True, uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'total_price': str(self.total_price),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric, nullable=False)

    # Foreign keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'quantity': self.quantity,
            'price': str(self.price),
            'product_id': self.product_id,
            'order_id': self.order_id
        }

    def __repr__(self):
        return f'<OrderItem {self.id}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key linking to the order
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': str(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'payment_date': self.payment_date.isoformat(),
            'order_id': self.order_id
        }

    def __repr__(self):
        return f'<Payment {self.id}>'

class Logistics(db.Model):
    __tablename__ = 'logistics'
    id = db.Column(db.Integer, primary_key=True)
    service_provider = db.Column(db.String(100), nullable=False)
    tracking_number = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_transit')
    estimated_delivery_date = db.Column(db.DateTime, nullable=True)
    actual_delivery_date = db.Column(db.DateTime, nullable=True)

    # Foreign key linking to the order
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'service_provider': self.service_provider,
            'tracking_number': self.tracking_number,
            'status': self.status,
            'estimated_delivery_date': self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'order_id': self.order_id
        }

    def __repr__(self):
        return f'<Logistics {self.tracking_number}>'

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys linking feedback to product and user
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat(),
            'product_id': self.product_id,
            'user_id': self.user_id
        }

    def __repr__(self):
        return f'<Feedback {self.id}>'
