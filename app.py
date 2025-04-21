from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Expense {self.name} {self.amount}>'

class Settlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    From = db.Column(db.String(100), nullable=False)
    To = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_history = db.Column(db.Boolean, default=False)  # Flag to mark history records

    def __repr__(self):
        return f'<Settlement {self.From} to {self.To}: {self.amount}>'

# Handle missing column issue
def check_and_update_tables():
    # Check if columns exist in tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    expense_columns = [col['name'] for col in inspector.get_columns('expense')]
    settlement_columns = [col['name'] for col in inspector.get_columns('settlement')]
    
    needs_migration = False
    
    # Check if the expense table exists but is missing columns
    if expense_columns and 'created_at' not in expense_columns:
        needs_migration = True
        
    # Check if the settlement table exists but is missing columns
    if settlement_columns and 'created_at' not in settlement_columns:
        needs_migration = True
    
    # Check if settlement table is missing is_history column
    if settlement_columns and 'is_history' not in settlement_columns:
        needs_migration = True
    
    if needs_migration:
        # Drop and recreate tables - WARNING: This will lose existing data
        db.drop_all()
        db.create_all()
        flash('Database structure updated. Previous data has been reset.', 'warning')

# Create all database tables and check for missing columns
with app.app_context():
    if not os.path.exists('instance/expenses.db'):
        # New database, just create tables
        db.create_all()
    else:
        # Existing database, check for missing columns
        check_and_update_tables()

# Helper function to standardize names (lowercase and capitalize first letter)
def standardize_name(name):
    if not name:
        return name
    return name.strip().lower().capitalize()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle expense submission
        name = request.form.get('name')
        amount = request.form.get('amount')
        
        # Validate name (contains only letters)
        if not name or not name.replace(' ', '').isalpha():
            flash('Error: Name must contain only letters', 'error')
            return redirect(url_for('index'))
        
        # Standardize name
        standardized_name = standardize_name(name)
        
        # Validate amount (non-negative float, including 0)
        try:
            amount = float(amount)  # Convert to float
            if amount < 0:
                flash('Error: Amount must be a non-negative number', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('Error: Amount must be a valid number', 'error')
            return redirect(url_for('index'))
        
        # Check if the standardized name already exists
        existing_user = Expense.query.filter(Expense.name.ilike(standardized_name)).first()
        if not existing_user:
            # If no user with this name exists, allow adding a new user
            new_expense = Expense(name=standardized_name, amount=amount)
            db.session.add(new_expense)
            db.session.commit()
            flash(f'New user "{standardized_name}" added with an expense of ₹{amount:.2f}!', 'success')
        else:
            # If the user already exists, allow adding another expense for the same user
            new_expense = Expense(name=existing_user.name, amount=amount)
            db.session.add(new_expense)
            db.session.commit()
            flash(f'Expense of ₹{amount:.2f} added for user "{standardized_name}"!', 'success')
        
        return redirect(url_for('index'))
    
    # Get all expenses from the database
    expenses = Expense.query.order_by(Expense.id.desc()).all()
    settlements = Settlement.query.filter_by(is_history=False).order_by(Settlement.id.desc()).all()
    settlement_history = Settlement.query.filter_by(is_history=True).order_by(Settlement.id.desc()).all()
    
    # Calculate total expenses per person
    expense_totals = {}
    for expense in expenses:
        if expense.name in expense_totals:
            expense_totals[expense.name] += expense.amount
        else:
            expense_totals[expense.name] = expense.amount
    
    return render_template('index.html', 
                           expenses=expenses, 
                           settlements=settlements, 
                           settlement_history=settlement_history,
                           expense_totals=expense_totals)

@app.route('/calculate_settlement', methods=['POST'])
def calculate_settlement():
    # Move current settlements to history
    current_settlements = Settlement.query.filter_by(is_history=False).all()
    for settlement in current_settlements:
        settlement.is_history = True
    
    # Get all expenses
    expenses = Expense.query.all()
    
    # Calculate total expense per person
    expense_per_person = {}
    for expense in expenses:
        if expense.name in expense_per_person:
            expense_per_person[expense.name] += expense.amount
        else:
            expense_per_person[expense.name] = expense.amount
    
    if not expense_per_person:
        flash('No expenses found to settle', 'error')
        return redirect(url_for('index'))
    
    # Calculate total and average
    total_expense = sum(expense_per_person.values())
    
    if len(expense_per_person) == 0:
        flash('Need at least one person with expenses', 'error')
        return redirect(url_for('index'))
    
    average_expense = total_expense / len(expense_per_person)
    
    # Calculate how much each person needs to pay or receive
    balances = {}
    for person, expense in expense_per_person.items():
        balances[person] = expense - average_expense
    
    # Create settlements (who pays whom)
    # Sort balances by amount (descending)
    sorted_balances = sorted(balances.items(), key=lambda x: x[1])
    
    # Create settlements
    i, j = 0, len(sorted_balances) - 1
    while i < j:
        # Get the person who paid the least (negative balance) and the person who paid the most (positive balance)
        debtor = sorted_balances[i][0]
        creditor = sorted_balances[j][0]
        
        # Calculate how much the debtor needs to pay
        debt = min(abs(sorted_balances[i][1]), sorted_balances[j][1])
        
        # Create a settlement
        if debt > 0:  # Only create a settlement if there's actual money to be transferred
            settlement = Settlement(From=debtor, To=creditor, amount=round(debt), is_history=False)
            db.session.add(settlement)
        
        # Update balances
        sorted_balances[i] = (debtor, sorted_balances[i][1] + debt)
        sorted_balances[j] = (creditor, sorted_balances[j][1] - debt)
        
        # Move to the next person if their balance is close to zero
        if abs(sorted_balances[i][1]) < 0.01:
            i += 1
        if abs(sorted_balances[j][1]) < 0.01:
            j -= 1
    
    db.session.commit()
    flash('Settlements calculated successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/clear_all', methods=['POST'])
def clear_all():
    # Clear all data
    Expense.query.delete()
    Settlement.query.delete()
    db.session.commit()
    flash('All data cleared successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    # Find the expense by ID
    expense = Expense.query.get_or_404(expense_id)
    
    # Delete the expense
    db.session.delete(expense)
    db.session.commit()
    
    # Flash success message
    flash(f'Expense by {expense.name} of ₹{expense.amount} deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route('/clear_settlements', methods=['POST'])
def clear_settlements():
    # Clear only current settlements (not history)
    Settlement.query.filter_by(is_history=False).delete()
    db.session.commit()
    flash('Current settlements cleared successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    # Clear only settlement history
    Settlement.query.filter_by(is_history=True).delete()
    db.session.commit()
    flash('Settlement history cleared successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)