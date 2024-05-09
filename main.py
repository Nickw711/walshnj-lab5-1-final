from flask import Flask, request, render_template_string, redirect, url_for, render_template, session
from random import shuffle
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database file path
DATABASE = 'demo.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # This enables name-based access to columns
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        ''')
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''  # Message indicating the result of the operation
    result_message = session.pop('result_message', '')  # Retrieve result message from session
    if request.method == 'POST':
        # Check if it's a delete action
        if request.form.get('action') == 'delete':
            contact_id = request.form.get('contact_id')
            db = get_db()
            db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
            db.commit()
            message = 'Contact deleted successfully.'
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
            if name and phone:
                db = get_db()
                db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                db.commit()
                message = 'Contact added successfully.'
            else:
                message = 'Missing name or phone number.'

    # Always display the contacts table
    db = get_db()
    contacts = db.execute('SELECT * FROM contacts').fetchall()

    # Display the HTML form along with the contacts table
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contacts</title>
        </head>
        <body>
            <h2>Add Contact</h2>
            <form method="POST" action="/">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" required><br>
                <label for="phone">Phone Number:</label><br>
                <input type="text" id="phone" name="phone" required><br><br>
                <input type="submit" value="Submit">
            </form>
            <p>{{ message }}</p>
            <a href="{{ url_for('matching_game') }}">Play Matching Game</a>
            {% if contacts %}
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Phone Number</th>
                        <th>Delete</th>
                    </tr>
                    {% for contact in contacts %}
                        <tr>
                            <td>{{ contact['name'] }}</td>
                            <td>{{ contact['phone'] }}</td>
                            <td>
                                <form method="POST" action="/">
                                    <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="submit" value="Delete">
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No contacts found.</p>
            {% endif %}
            {% if result_message %}
                <p>{{ result_message }}</p>  <!-- Display result message if it exists -->
            {% endif %}
        </body>
        </html>
    ''', message=message, contacts=contacts, result_message=result_message)

@app.route('/matching-game')
def matching_game():
    db = get_db()
    data = db.execute('SELECT * FROM contacts').fetchall()
    shuffled_names = [contact['name'] for contact in data]
    shuffled_numbers = [contact['phone'] for contact in data]
    shuffle(shuffled_names)
    shuffle(shuffled_numbers)
    session['correct_numbers'] = ','.join(shuffled_numbers)
    return render_template('index.html', names=shuffled_names)

@app.route('/check-guess', methods=['POST'])
def check_guess():
    correct_numbers = session.get('correct_numbers').split(',')
    guesses = request.form.getlist('guesses[]')
    if guesses == correct_numbers:
        session['result_message'] = "Congratulations! Your guess is correct."
    else:
        session['result_message'] = "Sorry, your guess is incorrect."
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.secret_key = os.urandom(24)
    init_db()  # Initialize the database and table
    app.run(debug=True, host='0.0.0.0', port=port)
