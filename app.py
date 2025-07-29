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
    from datetime import datetime, timedelta
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
        password = request.form.get('password')
        if password == '23076873@entry':  # Replace with your password
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
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
 
  if not bill:
      total_bill = 0.0
      total_due = 0.0
  else:
      total_bill = bill.bill_amount or 0.0
      total_due = bill.deu_amount or 0.0

  all_people = []
  all_history = []

  # Build people list
  for person in people:
      all_people.append({
          'id': person.id,
          'name': person.name,
          'due': person.due or 0.0
      })

  # Build history list
  for single_history in history:
      all_history.append({
          'name': single_history.name,
          'amount': single_history.amount,
          'bill_type': single_history.bill_type,
          'date': single_history.date
      })

  # Debug output
  print(all_history)
  print(all_people)
  print(total_bill)
  print(total_due)

  # Render the template
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
        
        current_bill = Bill.query.first()
        updated_bill = current_bill.bill_amount + amount
        updated_due = current_bill.deu_amount + amount
        
        if current_bill:
          current_bill.bill_amount = round(updated_bill, 2)
          current_bill.deu_amount = round(updated_due, 2)
        
        persons = Person.query.all()
        person_length = Person.query.count()
        shared_bill = amount / person_length;
        for person in persons:
            person.due = person.due + shared_bill

        new_history = History(name='All', amount=amount, bill_type="Shared-bill", date=date)
        db.session.add(new_history)

        db.session.commit()
        cleanup_old_history()
    except Exception as e:
        print("Error adding bill:", e)
    return redirect('/')
@app.route('/add-person-bill', methods=['POST'])

def add_person_bill():
    amount = float(request.form['amount'])
    person_id = request.form.get('person_id')
    person_name = request.form.get('person_name')
    date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    first_person = Person.query.first()
    current_person = Person.query.get(int(person_id))
    if current_person:
      current_person.due = float(current_person.due + amount)

    current_bill = Bill.query.first()
    updated_bill = current_bill.bill_amount + amount
    updated_due = current_bill.deu_amount + amount
    if current_bill:
      current_bill.bill_amount = updated_bill
      current_bill.deu_amount = updated_due

    new_history = History(name=person_name, amount=amount, bill_type="Personal-bill", date=date)
    db.session.add(new_history)

    db.session.commit()
    return redirect('/')

@app.route('/add-payment', methods=['POST'])
def add_payment():
    amount = float(request.form['amount'])
    person_id = request.form.get('person_id')
    person_name = request.form.get('person_name')
    date = request.form.get('date', datetime.now().strftime('%Y-%m-%d'))

    first_person = Person.query.first()
    current_person = Person.query.get(int(person_id))

    if current_person:
      current_person.due = round(float(current_person.due - amount), 2)

    current_bill = Bill.query.first()
    updated_bill = current_bill.bill_amount - amount
    updated_due = current_bill.deu_amount - amount

    if current_bill:
      current_bill.bill_amount = round(updated_bill, 2)
      current_bill.deu_amount = round(updated_due, 2)

    new_history = History(name=person_name, amount=amount, bill_type="Paid", date=date)
    db.session.add(new_history)

    db.session.commit()
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