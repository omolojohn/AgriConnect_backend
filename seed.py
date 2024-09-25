from app import app, db
from models import User, Product, Order, OrderItem, Payment, Logistics, Feedback
from datetime import datetime

# Create a function to seed the database
def seed_db():
    with app.app_context():
        # Drop all tables and create them again
        db.drop_all()
        db.create_all()

        # Create users
        user1 = User(username='John Omolo', email='farmer1@example.com', role='farmer')
        user1.set_password('password1')
        user2 = User(username='Caroline Akoth', email='buyer1@example.com', role='buyer')
        user2.set_password('password2')
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Create products (linked to user1, the farmer)
        product1 = Product(name='Tomatoes', description='Fresh organic tomatoes', price=10.00, stock=100, user_id=user1.id)
        product2 = Product(name='Potatoes', description='High-quality potatoes', price=20.00, stock=50, user_id=user1.id)
        
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()

        # Create an order (linked to user2, the buyer)
        order1 = Order(total_price=30.00, status='pending', user_id=user2.id)
        db.session.add(order1)
        db.session.commit()

        # Create order items (linked to order1)
        order_item1 = OrderItem(quantity=2, price=20.00, product_id=product1.id, order_id=order1.id)
        order_item2 = OrderItem(quantity=1, price=10.00, product_id=product2.id, order_id=order1.id)
        
        db.session.add(order_item1)
        db.session.add(order_item2)
        db.session.commit()

        # Create a payment (linked to order1)
        payment1 = Payment(amount=30.00, payment_method='M-Pesa', status='completed', order_id=order1.id)
        db.session.add(payment1)
        db.session.commit()

        # Create logistics (linked to order1)
        logistics1 = Logistics(service_provider='FastDelivery', tracking_number='123456', status='shipped', order_id=order1.id)
        db.session.add(logistics1)
        db.session.commit()

        # Create feedback (linked to product1 and user2)
        feedback1 = Feedback(rating=5, comment='Great product!', product_id=product1.id, user_id=user2.id)
        db.session.add(feedback1)
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_db()
