from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, current_user, LoginManager, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    pets = db.relationship('Pet', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Pet(db.Model):
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    breed = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def calculate_age(self):
        today = datetime.today().date()
        age = today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        return age

class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)

class VetVisit(db.Model):
    __tablename__ = 'vet_visits'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500))
    weight = db.Column(db.Float)

class PetNote(db.Model):
    __tablename__ = 'pet_notes'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)
    note_date = db.Column(db.Date, nullable=False)
    note_text = db.Column(db.String(500))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', pets=pets)

@app.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet():
    if request.method == 'POST':
        try:
            name = request.form['name']
            birthdate_str = request.form['birthdate']
            breed = request.form.get('breed', '')
        
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
        
            new_pet = Pet(name=name, birthdate=birthdate, breed=breed, user_id=current_user.id)
            db.session.add(new_pet)
            db.session.commit()
        
            return redirect(url_for('list_pets'))
        except KeyError as e:
            return f"Missing required form field: {str(e)}", 400
    
    return render_template('add_pet.html')

@app.route('/pet/<int:pet_id>')
@login_required
def pet_details(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    vetvisit = VetVisit.query.filter_by(pet_id=pet_id).all()
    medicine = Medicine.query.filter_by(pet_id=pet_id).all()
    notes = PetNote.query.filter_by(pet_id=pet_id).all()
    return render_template('pet_details.html', pet=pet, vetvisit=vetvisit, medicine=medicine, notes=notes)

@app.route('/pet/<int:pet_id>/add_visit', methods=['GET', 'POST'])
@login_required
def add_visit(pet_id):
    if request.method == 'POST':
        visit_date = request.form['visit_date']
        weight = request.form['weight']
        notes = request.form['notes']
        new_visit = VetVisit(pet_id=pet_id, visit_date=datetime.strptime(visit_date, '%Y-%m-%d').date(), weight=float(weight), notes=notes)
        db.session.add(new_visit)
        db.session.commit()
        return redirect(url_for('pet_details', pet_id=pet_id))
    return render_template('add_visit.html')

@app.route('/pets', methods=['GET'])
@login_required
def list_pets():
    pets = Pet.query.filter_by(user_id=current_user.id).all()
    return render_template('list_pets.html', pets=pets)

@app.route('/pets/<int:pet_id>', methods=['GET'])
@login_required
def view_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    return render_template('view_pet.html', pet=pet)

@app.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if request.method == 'POST':
        pet.name = request.form['name']
        pet.birthdate = datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
        pet.breed = request.form['breed']
        
        db.session.commit()
        return redirect(url_for('list_pets'))
    
    return render_template('edit_pet.html', pet=pet)

@app.route('/delete_pet/<int:pet_id>', methods=['GET'])
@login_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    db.session.delete(pet)
    db.session.commit()
    return redirect(url_for('list_pets'))

@app.route('/delete_visit/<int:pet_id>/<int:visit_id>', methods=['GET'])
@login_required
def delete_visit(pet_id, visit_id):
    # Fetch the pet and the specific medication
    pet = Pet.query.get_or_404(pet_id)
    visit = VetVisit.query.get_or_404(visit_id)

    # Ensure the medication belongs to the correct p
    # Delete the medication
    db.session.delete(visit)
    db.session.commit()

    return redirect(url_for('pet_details', pet_id=pet_id))

@app.route('/delete_med/<int:pet_id>/<int:med_id>', methods=['GET'])
@login_required
def delete_med(pet_id, med_id):
    # Fetch the pet and the specific medication
    pet = Pet.query.get_or_404(pet_id)
    med = Medicine.query.get_or_404(med_id)

    # Ensure the medication belongs to the correct p
    # Delete the medication
    db.session.delete(med)
    db.session.commit()

    return redirect(url_for('pet_details', pet_id=pet_id))

@app.route('/delete_note/<int:pet_id>/<int:note_id>', methods=['GET'])
@login_required
def delete_note(pet_id, note_id):
    # Fetch the pet and the specific medication
    pet = Pet.query.get_or_404(pet_id)
    note = PetNote.query.get_or_404(note_id)

    # Ensure the medication belongs to the correct p
    # Delete the medication
    db.session.delete(note)
    db.session.commit()

    return redirect(url_for('pet_details', pet_id=pet_id))

@app.route('/add_details/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def add_details(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    
    if request.method == 'POST':
        detail_type = request.form['detail_type']
        
        if detail_type == 'vet_visit':
            visit_date = request.form['visit_date']
            notes = request.form['notes']
            weight = request.form['weight']
            new_visit = VetVisit(pet_id=pet_id, visit_date=datetime.strptime(visit_date, '%Y-%m-%d').date(), notes=notes, weight=float(weight))
            db.session.add(new_visit)
            db.session.commit()
        
        elif detail_type == 'medicine':
            name = request.form['medicine_name']
            dosage = request.form['dosage']
            frequency = request.form['frequency']
            start_date = request.form['start_date']
            end_date = request.form.get('end_date')
            new_medicine = Medicine(pet_id=pet_id, medicine_name=name, dosage=dosage, frequency=frequency, start_date=datetime.strptime(start_date, '%Y-%m-%d').date(), end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None)
            db.session.add(new_medicine)
            db.session.commit()
        
        elif detail_type == 'note':
            note_text = request.form['note_text']
            new_note = PetNote(pet_id=pet_id, note_date=datetime.strptime(request.form['note_date'], '%Y-%m-%d').date(), note_text=note_text)
            db.session.add(new_note)
            db.session.commit()
        
        return redirect(url_for('pet_details', pet_id=pet_id))
    
    return render_template('add_details.html', pet=pet)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid username or password", 401
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists", 400
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
