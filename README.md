# Group Expense Tracker

A simple yet powerful web application for tracking and settling group expenses. Perfect for roommates, trips, events, or any situation where multiple people share expenses.

## Features

- **Add Expenses**: Record expenses with name and amount
- **Track Spending**: Keep a detailed record of who paid for what
- **Calculate Settlements**: Automatically determine the most efficient way for everyone to settle up
- **Settlement History**: View past settlements for reference
- **Responsive Design**: Works on desktop and mobile devices
- **Simple Interface**: Intuitive and easy to use

## Screenshots

*[Add screenshots of your application here]*

## Technology Stack

- **Backend**: Python with Flask framework
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **UI Design**: Custom CSS with responsive design

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/group-expense-tracker.git
   cd group-expense-tracker
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install flask flask-sqlalchemy
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## How to Use

### Adding Expenses

1. Enter the name of the person who paid
2. Enter the amount paid
3. Click "ADD EXPENSE"

### Calculating Settlements

1. After adding all expenses, click "CALCULATE SETTLEMENT"
2. The application will automatically calculate the optimal settlement plan
3. Settlements will show who needs to pay whom and how much

### Managing Data

- **Clear All Data**: Deletes all expenses and settlements
- **Delete Individual Expenses**: Remove specific expenses using the delete button
- **Clear Settlements**: Remove only the current settlement calculations
- **Clear History**: Remove the settlement history

## Settlement Algorithm

The application uses an algorithm that minimizes the number of transactions needed to settle the expenses:

1. Calculates the total expense per person
2. Determines the average amount each person should have paid
3. Calculates how much each person needs to pay or receive
4. Creates settlement transactions from those who paid less to those who paid more

## Data Management

- All data is stored locally in an SQLite database (`expenses.db`)
- Database migrations are handled automatically to ensure proper structure
- Names are standardized to avoid duplicates (case-insensitive)

## Development Notes

### Database Schema

**Expense Model**
- `id`: Primary key
- `name`: Name of the person who paid
- `amount`: Amount paid
- `created_at`: Timestamp of when the expense was added

**Settlement Model**
- `id`: Primary key
- `payer`: Person who needs to pay
- `receiver`: Person who receives the payment
- `amount`: Amount to be paid
- `created_at`: Timestamp of when the settlement was calculated
- `is_history`: Boolean flag to mark history records

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- Add user authentication
- Support for multiple groups/events
- Add categories for expenses
- Generate reports and visualizations
- Enable expense splitting by custom ratios
- Add payment verification system
- Export data to CSV/PDF
