from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize the database instance
db = SQLAlchemy()

# Define the Pet model
class Pet(db.Model):
    __tablename__ = 'pets'  # Use lowercase and no schema prefix like 'SHOGAN'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    species = db.Column(db.String(50))
    breed = db.Column(db.String(50))

    # Relationships
    medicines = db.relationship('Medicine', backref='pet', lazy=True, cascade="all, delete-orphan")
    visits = db.relationship('VetVisit', backref='pet', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('PetNote', backref='pet', lazy=True, cascade="all, delete-orphan")


# Define the Medicine model
class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)  # Foreign key points to 'pets' table
    medicine_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)


# Define the VetVisit model
class VetVisit(db.Model):
    __tablename__ = 'vet_visits'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)  # Foreign key points to 'pets' table
    visit_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500))
    weight = db.Column(db.Float)


# Define the PetNote model
class PetNote(db.Model):
    __tablename__ = 'pet_notes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id'), nullable=False)  # Foreign key points to 'pets' table
    note_date = db.Column(db.Date, nullable=False)
    note_text = db.Column(db.String(500))
