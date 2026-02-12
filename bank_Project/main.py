from flask import Flask, request, jsonify, redirect, render_template
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)

# Database Configuration
# REPLACE 'root', 'password', 'localhost', 'bank_db' with your actual MySQL credentials
# If running in Docker and MySQL is on host, use 'host.docker.internal' instead of 'localhost'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ui/customers')
def ui_customers():
    return render_template('customers.html')

@app.route('/ui/accounts')
def ui_accounts():
    return render_template('accounts.html')

@app.route('/ui/transactions')
def ui_transactions():
    return render_template('transactions.html')

@app.route('/swagger-ui')
def swagger_ui_redirect():
    return redirect('/apidocs')

# --- Models ---
class Customer(db.Model):
    __tablename__ = 'customers'
    customer_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    
    # Relationship to accounts
    accounts = db.relationship('Account', backref='customer', lazy=True)

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number
        }

class Account(db.Model):
    __tablename__ = 'accounts'
    account_number = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50), db.ForeignKey('customers.customer_id'), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    
    # Relationship to transactions
    transactions = db.relationship('Transaction', backref='account', lazy=True)

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            return True
        return False

    def to_dict(self):
        return {
            "account_number": self.account_number,
            "customer_id": self.customer_id,
            "account_type": self.account_type,
            "balance": self.balance
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(db.String(50), primary_key=True)
    account_number = db.Column(db.String(50), db.ForeignKey('accounts.account_number'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(50), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self):
        return {
            "transaction_id": self.transaction_id,
            "account_number": self.account_number,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "date": self.date
        }

# --- Routes ---

@app.route('/customers', methods=['POST'])
def create_customer():
    """
    Create a new customer
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            customer_id:
              type: string
            name:
              type: string
            email:
              type: string
            phone_number:
              type: string
    responses:
      201:
        description: Customer created successfully
      400:
        description: Customer ID already exists
    """
    data = request.get_json()
    c_id = data.get('customer_id')
    
    if Customer.query.get(c_id):
        return jsonify({"error": "Customer ID already exists!"}), 400
        
    customer = Customer(
        customer_id=c_id, 
        name=data.get('name'), 
        email=data.get('email'), 
        phone_number=data.get('phone_number')
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({"message": "Customer created successfully!", "customer": customer.to_dict()}), 201

@app.route('/customers', methods=['GET'])
def get_customers():
    """
    List all customers
    ---
    responses:
      200:
        description: List of customers
    """
    customers = Customer.query.all()
    return jsonify([c.to_dict() for c in customers])

@app.route('/accounts', methods=['POST'])
def create_account():
    """
    Create a new account
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            account_number:
              type: string
            customer_id:
              type: string
            account_type:
              type: string
              enum: [Savings, Current]
            balance:
              type: number
    responses:
      201:
        description: Account created successfully
      400:
        description: Error creating account
    """
    data = request.get_json()
    a_num = data.get('account_number')
    c_id = data.get('customer_id')
    
    if not Customer.query.get(c_id):
        return jsonify({"error": "Customer ID not found!"}), 400
    if Account.query.get(a_num):
        return jsonify({"error": "Account Number already exists!"}), 400
        
    account = Account(
        account_number=a_num, 
        customer_id=c_id, 
        account_type=data.get('account_type'), 
        balance=data.get('balance', 0.0)
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Account created successfully!", "account": account.to_dict()}), 201

@app.route('/accounts', methods=['GET'])
def get_accounts():
    """
    List all accounts
    ---
    responses:
      200:
        description: List of accounts
    """
    accounts = Account.query.all()
    return jsonify([a.to_dict() for a in accounts])

@app.route('/transactions', methods=['POST'])
def perform_transaction():
    """
    Perform a transaction (Deposit/Withdraw)
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            transaction_id:
              type: string
            account_number:
              type: string
            transaction_type:
              type: string
              enum: [Deposit, Withdraw]
            amount:
              type: number
    responses:
      201:
        description: Transaction successful
      400:
        description: Transaction failed
    """
    data = request.get_json()
    t_id = data.get('transaction_id')
    a_num = data.get('account_number')
    t_type = data.get('transaction_type')
    amount = data.get('amount')
    
    account = Account.query.get(a_num)
    if not account:
        return jsonify({"error": "Account not found!"}), 400
        
    success = False
    if t_type == 'Deposit':
        success = account.deposit(amount)
    elif t_type == 'Withdraw':
        success = account.withdraw(amount)
    else:
        return jsonify({"error": "Invalid transaction type"}), 400
        
    if success:
        if Transaction.query.get(t_id):
             return jsonify({"error": "Transaction ID already exists"}), 400

        transaction = Transaction(
            transaction_id=t_id, 
            account_number=a_num, 
            transaction_type=t_type, 
            amount=amount
        )
        db.session.add(transaction)
        db.session.commit() # Commits both the balance change and the new transaction
        
        return jsonify({
            "message": "Transaction successful",
            "new_balance": account.balance,
            "transaction": transaction.to_dict()
        }), 201
    else:
        return jsonify({"error": "Transaction failed (Insufficient funds or invalid amount)"}), 400

@app.route('/transactions', methods=['GET'])
def get_transactions():
    """
    List all transactions
    ---
    responses:
      200:
        description: List of transactions
    """
    transactions = Transaction.query.all()
    return jsonify([t.to_dict() for t in transactions])

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
