from flask import Flask, render_template, request, session, url_for, redirect
from models import db, Person, Bill, History
from datetime import datetime, timedelta
from sqlalchemy.sql import func

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.before_request
def create_tables():
    db.create_all()
    if not Bill.query.first():
        db.session.add(Bill(bill_amount=0, deu_amount=0))
        db.session.commit()

def cleanup_old_history():
    cutoff = datetime.now() - timedelta(days=30)
    for h in History.query.all():
        try:
            if datetime.strptime(h.date, "%Y-%m-%d") < cutoff:
                db.session.delete(h)
        except ValueError:
            continue
    db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == '1997':
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error="Invalid password")
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    people = Person.query.all()
    history = History.query.all()
    bill = Bill.query.first()

    total_bill = bill.bill_amount if bill else 0.0
    total_due = bill.deu_amount if bill else 0.0

    all_people = [{'id': p.id, 'name': p.name, 'due': p.due or 0.0} for p in people]
    all_history = [
        {
            'name': h.name,
            'amount': h.amount,
            'bill_type': h.bill_type,
            'date': h.date
        } for h in history
    ]

    return render_template(
        'index.html',
        total_bill=total_bill,
        total_due=total_due,
        all_people=all_people,
        all_history=all_history
    )

@app.route('/add-shared-bill', methods=['POST'])
def add_bill():
    try:
        amount = float(request.form['amount'])
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

        bill = Bill.query.first()
        bill.bill_amount = round(bill.bill_amount + amount, 2)
        bill.deu_amount = round(bill.deu_amount + amount, 2)

        persons = Person.query.all()
        if persons:
            share = amount / len(persons)
            for p in persons:
                p.due += share

        db.session.add(History(name='All', amount=amount, bill_type="Shared-bill", date=date))
        db.session.commit()
        cleanup_old_history()
    except Exception as e:
        print("Error adding shared bill:", e)
    return redirect('/')

@app.route('/add-person-bill', methods=['POST'])
def add_person_bill():
    try:
        amount = float(request.form['amount'])
        person_id = int(request.form['person_id'])
        person_name = request.form['person_name']
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

        person = Person.query.get(person_id)
        bill = Bill.query.first()

        if person and bill:
            person.due += amount
            bill.bill_amount += amount
            bill.deu_amount += amount
            db.session.add(History(name=person_name, amount=amount, bill_type="Personal-bill", date=date))
            db.session.commit()
    except Exception as e:
        print("Error adding personal bill:", e)
    return redirect('/')

@app.route('/add-payment', methods=['POST'])
def add_payment():
    try:
        amount = float(request.form['amount'])
        person_id = int(request.form['person_id'])
        person_name = request.form['person_name']
        date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

        person = Person.query.get(person_id)
        bill = Bill.query.first()

        if person and bill:
            person.due = round(person.due - amount, 2)
            bill.bill_amount = round(bill.bill_amount - amount, 2)
            bill.deu_amount = round(bill.deu_amount - amount, 2)

            db.session.add(History(name=person_name, amount=amount, bill_type="Paid", date=date))
            db.session.commit()
    except Exception as e:
        print("Error adding payment:", e)
    return redirect('/')

@app.route('/add-person', methods=['POST'])
def add_person():
    name = request.form.get('name')
    if name:
        db.session.add(Person(name=name, due=0))
        db.session.commit()
    return redirect('/')

@app.route('/remove-person', methods=['POST'])
def remove_person():
    person_id = request.form.get('person_id')
    if person_id:
        person = Person.query.get(int(person_id))
        if person:
            db.session.delete(person)
            db.session.commit()
    return redirect('/')

@app.route('/reset-data', methods=['POST'])
def reset_data():
    History.query.delete()
    Person.query.delete()
    Bill.query.delete()
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
