from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:1234@localhost:3306/drs"
app.config["SECRET_KEY"] = "abcd"
app.config["JWT_SECRET_KEY"] = "efgh"
app.config["JWT_TOKEN_LOCATION"] = ["headers"]

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    booked_slot = db.relationship("BookedSlot", backref="user", lazy=True)

    def __init__(self, username, password, email):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password)

    def __repr__(self):
        return "<User %r>" % self.username


class DiningPlace(db.Model):
    __tablename__ = "dining_place"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    phone_no = db.Column(db.String(10))
    website = db.Column(db.String(120))
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    booked_slots = db.relationship("BookedSlot", backref="dining_places")


class BookedSlot(db.Model):
    __tablename__ = "booked_slot"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    dining_place_id = db.Column(db.Integer, db.ForeignKey("dining_place.id"))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)


@app.route("/")
def home():
    return "Hello world"


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    print("Received data:", username, password)

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(
            {
                "status": "Login successful",
                "status_code": 200,
                "user_id": user.id,
                "access_token": access_token,
            }
        )
    else:
        return jsonify(
            {
                "status": "Incorrect username/password provided. Please retry",
                "status_code": 401,
            }
        )


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    email = data["email"]

    print("Received data:", username, password, email)

    user = User(username, password, email)
    db.session.add(user)
    db.session.commit()

    return jsonify(
        {
            "status": "Account successfully created",
            "status_code": 200,
            "user_id": user.id,
        }
    )


@app.route("/api/dining-place/create", methods=["POST"])
def create_dining_place():
    data = request.get_json()
    name = data["name"]
    address = data["address"]
    phone_no = data["phone_no"]
    website = data["website"]
    open_time = data["operational_hours"]["open_time"]
    close_time = data["operational_hours"]["close_time"]

    dining_place = DiningPlace(
        name=name,
        address=address,
        phone_no=phone_no,
        website=website,
        open_time=open_time,
        close_time=close_time,
    )
    db.session.add(dining_place)
    db.session.commit()

    return jsonify(
        {
            "message": f"{dining_place.name} added successfully",
            "place_id": dining_place.id,
            "status_code": 200,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
