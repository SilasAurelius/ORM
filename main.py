from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import ValidationError
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Password1@localhost/fitness_center_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Models
class Member(db.Model):
    __tablename__ = "members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(350), nullable=False)
    phone = db.Column(db.String(15))

class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'
    session_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    member = db.relationship('Member', backref=db.backref('workout_sessions', lazy=True))
    service = db.Column(db.String(350), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Integer)

# Schemas
class WorkoutSessionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = WorkoutSession
        load_instance = True
        include_relationships = True 

class MemberSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Member
        load_instance = True

workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)

### Members CRUD
# Get All Members
@app.route('/members', methods=['GET'])
def get_all_members():
    members = Member.query.all()
    return members_schema.jsonify(members)

# Get One Member by ID
@app.route('/members/<int:id>', methods=['GET'])
def get_member(id):
    member = Member.query.get_or_404(id)
    return member_schema.jsonify(member)

# Add Member
@app.route('/members', methods=['POST'])
def add_member():
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_member = Member(name=member_data['name'], email=member_data['email'], phone=member_data['phone'])
    db.session.add(new_member)
    db.session.commit()
    return jsonify({'message': 'New member added successfully'}), 201

# Update Member
@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    member = Member.query.get_or_404(id)
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    member.name = member_data['name']
    member.email = member_data['email']
    member.phone = member_data['phone']
    db.session.commit()
    return jsonify({'message': 'Member details updated successfully'}), 200

# Delete Member
@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": 'Member removed successfully'}), 200  

### Workout Sessions CRUD
# Get All Workout Sessions
@app.route('/workout_sessions', methods=['GET'])
def get_all_workout_sessions():
    workout_sessions = WorkoutSession.query.all()
    serialized_data = workout_sessions_schema.dump(workout_sessions)  # Serialize the data
    return jsonify(serialized_data)  # Convert to JSON response

# Get Workout Sessions by Member ID
@app.route('/members/<int:id>/workout_sessions', methods=['GET'])
def get_workout_sessions_by_member(id):
    member = Member.query.get(id)
    if member is None:
        return jsonify({"message": "Member not found"}), 404
    workout_sessions = WorkoutSession.query.filter_by(member_id=id).all()
    return workout_sessions_schema.jsonify(workout_sessions)

# Add Workout Session
@app.route('/workout_sessions', methods=['POST'])
def add_workout_session():
    try:
        session_data = workout_session_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    date = datetime.datetime.strptime(session_data['date'], '%Y-%m-%d').date()
    
    new_session = WorkoutSession(
        member_id=session_data['member_id'],
        service=session_data['service'],
        date=date,
        duration_minutes=session_data['duration_minutes'],
        calories_burned=session_data['calories_burned']
    )
    db.session.add(new_session)
    db.session.commit()
    return jsonify({'message': 'New workout session added successfully'}), 201

# Update Workout Session
@app.route('/workout_sessions/<int:session_id>', methods=['PUT'])
def update_workout_session(session_id):
    session = WorkoutSession.query.get_or_404(session_id)
    try:
        session_data = workout_session_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    # Handle date formatting
    date = datetime.datetime.strptime(session_data['date'], '%Y-%m-%d').date()
    
    session.service = session_data['service']
    session.date = date
    session.duration_minutes = session_data['duration_minutes']
    session.calories_burned = session_data['calories_burned']
    db.session.commit()
    return jsonify({'message': 'Workout session updated successfully'}), 200

# Delete Workout Session
@app.route('/workout_sessions/<int:session_id>', methods=['DELETE'])
def delete_workout_session(session_id):
    session = WorkoutSession.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": 'Workout session deleted successfully'}), 200  

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
