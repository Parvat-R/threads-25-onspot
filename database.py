import os
import json
import uuid
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient, errors
from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator, validator
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load MongoDB URI from .env
load_dotenv()
# uri = "mongodb+srv://threads25cse:aAlBJxpockulLRWh@threads-1.nlete.mongodb.net/?retryWrites=true&w=majority&appName=threads-1"
uri = "mongodb://localhost:27017/"
MONGO_URI = os.environ.get("MONGO_URI", uri)
print(MONGO_URI)

# Connect to MongoDB with error handling
try:
    client = MongoClient(uri, maxPoolSize=100, minPoolSize=10)
    db = client.get_database("symposium_db")
    students_collection = db.students
    payment_and_otp_collection = db.payment_and_otp
    login_otp_collection = db.login_otp  # New collection for login OTPs
    admin_collection = db.admins
    token_recieve_collection = db.token_recieve

    # Ensure indexes for students collection
    students_collection.create_index("email", unique=True)
    students_collection.create_index("phone", unique=True)

    # Ensure indexes for payment_and_otp collection
    payment_and_otp_collection.create_index("email", unique=True)
    payment_and_otp_collection.create_index(
        "transaction_id", unique=True, sparse=True)

    # Ensure indexes for login_otp collection
    login_otp_collection.create_index("email", unique=True)
    login_otp_collection.create_index(
        # OTP expires after 5 minutes
        [("created_at", 1)], expireAfterSeconds=300)

    # Ensure indexes for admin collection
    admin_collection.create_index("username", unique=True)

    token_recieve_collection.create_index("email", unique=True)

    print("[✅] Connected to MongoDB")


except errors.ConnectionFailure as e:
    print(f"[❌] MongoDB Connection Failed: {e}")
    students_collection = None
    payment_and_otp_collection = None
    login_otp_collection = None

# Pydantic Models for Data Validation


class StudentModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    workshop: str | None
    events: list[str]  # Changed from bool to list of strings
    college_name: str


class PaymentModel(BaseModel):
    email: EmailStr
    paid: bool = False
    transaction_id: str | None = None
    upi_id: str | None = None


class LoginOtpModel(BaseModel):
    email: EmailStr
    verified: bool = False
    otp: str = Field(..., min_length=6, max_length=6)


class AdminModel(BaseModel):
    username: str
    password: str


class BotVerifiedPaymentModel(BaseModel):
    email: EmailStr
    verified: bool


class TokenRecieveModel(BaseModel):
    email: EmailStr
    token_recieved: bool


def create_login_otp(email: str, otp: str):
    """Create or update login OTP for a user"""
    if login_otp_collection == None:
        return None

    login_otp_data = {
        "email": email,
        "otp": str(otp),
    }

    login_otp = LoginOtpModel(**login_otp_data)

    # Upsert the OTP (create or update)
    result = login_otp_collection.update_one(
        {"email": email},
        {"$set": login_otp.model_dump()},
        upsert=True
    )

    return bool(result.modified_count or result.upserted_id)


def verify_login_otp(email: str, otp: str) -> bool:
    """Verify login OTP and handle attempts"""
    if login_otp_collection == None:
        return False

    # Get the OTP document
    otp_doc = login_otp_collection.find_one({
        "email": email
    })

    if not otp_doc:
        print(
            f"ERROR:: email='{email}' not fount in the collection 'login_otp_collection'")
        return False

    # str - changed to int type.
    return str(otp_doc.get("otp")) == str(otp)


def get_login_otp_status(email: str):
    """Get current login OTP status"""
    if login_otp_collection == None:
        return None

    otp_doc = login_otp_collection.find_one({"email": email})
    return bson_to_json(otp_doc) if otp_doc else None



def is_otp_valid(email: str):
    """Check if there's a valid OTP for the email"""
    if login_otp_collection == None:
        return False

    otp_doc = login_otp_collection.find_one({
        "email": email
    })

    return bool(otp_doc)


# Convert BSON to JSON
def bson_to_json(data):
    if data and "_id" in data:
        data["_id"] = str(data["_id"])
    return json.loads(json.dumps(data)) if data else None

# Student Collection Functions


def create_student(student_data: dict):
    if students_collection == None:
        return None

    # Ensure events is a list
    if isinstance(student_data.get('events'), bool):
        student_data['events'] = []
    elif not isinstance(student_data.get('events'), list):
        student_data['events'] = [student_data.get(
            'events')] if student_data.get('events') else []

    student = StudentModel(**student_data)
    inserted_id = students_collection.insert_one(
        student.model_dump()).inserted_id
    return str(inserted_id)


def get_student_by_id(student_id: str):

    if students_collection == None:
        return None
    student = students_collection.find_one({"_id": ObjectId(student_id)})
    return bson_to_json(student)


def get_student_by_phone(phone: str):
    if students_collection == None:
        return None
    student = students_collection.find_one({"phone": phone})
    return bson_to_json(student)


def edit_student(student_id: str, update_data: dict):
    if students_collection == None:
        return None

    # Ensure events is a list
    if 'events' in update_data:
        if isinstance(update_data['events'], bool):
            update_data['events'] = []
        elif not isinstance(update_data['events'], list):
            update_data['events'] = [update_data['events']
                                     ] if update_data['events'] else []

    print(students_collection.update_one(
        {"email": update_data["email"]}, {"$set": update_data}).modified_count)
    return get_student_by_id(student_id)


def student_exists(email: str = None, phone: str = None):
    if students_collection == None:
        return False
    query = {"$or": []}
    if email:
        query["$or"].append({"email": email})
    if phone:
        query["$or"].append({"phone": phone})
    return students_collection.find_one(query) is not None if query["$or"] else False


def get_all_students():
    if students_collection == None:
        return []
    students = list(students_collection.find())
    return [bson_to_json(student) for student in students]


def get_student_by_email(email: str):
    if students_collection == None:
        return None
    student = students_collection.find_one({"email": email})
    return bson_to_json(student)

# Payment and OTP Collection Functions


def create_payment_entry(payment_data: dict):
    if payment_and_otp_collection == None:
        return None

    payment = PaymentModel(**payment_data)
    inserted_id = payment_and_otp_collection.insert_one(
        payment.model_dump()).inserted_id
    return str(inserted_id)


def get_payment_by_email(email: str):
    if payment_and_otp_collection == None:
        return None
    payment = payment_and_otp_collection.find_one({"email": email})
    return bson_to_json(payment)


def update_payment_status(email: str, transaction_id: str, upi_id: str):
    if payment_and_otp_collection == None:
        return None

    update_data = {
        "paid": False,
        "transaction_id": transaction_id,
        "upi_id": upi_id
    }
    payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": update_data}
    )
    return get_payment_by_email(email)


def update_otp(email: str, new_otp: str):
    # update the otp in the login and otp collection
    if login_otp_collection == None:
        return False
    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"otp": new_otp}}
    )
    return True


def verify_email(email: str, otp: str):
    # change the verified status in the login and otp collection
    if login_otp_collection == None:
        print("ERROR:: 'login_otp_collection' COLLECTION NOT FOUND")
        return False

    if not verify_login_otp(email, otp):
        return False

    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"verified": True}}
    )
    return True


def email_is_verified(email: str):
    # check the verification from the LoginAndOtp class
    if login_otp_collection == None:
        return False
    otp_doc = login_otp_collection.find_one({"email": email})
    if not otp_doc:
        create_login_otp(email, "123456")
    otp_doc = login_otp_collection.find_one({"email": email})
    return otp_doc.get("verified")


def get_all_payments():
    if payment_and_otp_collection == None:
        return []
    payments = list(payment_and_otp_collection.find())
    return [bson_to_json(payment) for payment in payments]


def admin_exists(username):
    if admin_collection == None:
        return False
    admin = admin_collection.find_one({"username": username})
    return admin is not None


def match_admin_password(username, password):
    if admin_collection == None:
        return False
    admin = admin_collection.find_one({"username": username})
    if admin is None:
        return False
    return admin["password"] == password


def unverify_email(email: str):
    # make the user unverified in the login and otp class
    if login_otp_collection == None:
        return False
    login_otp_collection.update_one(
        {"email": email},
        {"$set": {"verified": False}}
    )
    return True


def create_admin(username, password):
    if admin_collection == None:
        return False
    admin = AdminModel(username=username, password=password)
    inserted_id = admin_collection.insert_one(admin.model_dump()).inserted_id
    return str(inserted_id)



def edit_payment(email: str, payment_data: dict):
    email = email.lower()
    if payment_and_otp_collection == None:
        return None

    # Remove _id if present
    if "_id" in payment_data:
        del payment_data["_id"]

    # check if the email belongs to sona tech domain:
    # it: @sonatech.ac.in
    if email.endswith("cse@sonatech.ac.in") or email.endswith("csd@sonatech.ac.in") or email.endswith("aiml@sonatech.ac.in"):
        payment_data['transaction_id'] = f"sona-{str(ObjectId())}"
        payment_data['upi_id'] = None

    # Convert to Pydantic model for validation
    if not isinstance(payment_data, PaymentModel):
        payment_data = PaymentModel(**payment_data)
        payment_data = payment_data.model_dump()

    res = payment_and_otp_collection.update_one(
        {"email": email},
        {"$set": payment_data}
    )

    print(f"Matched: {res.matched_count}, Modified: {res.modified_count}")
    return res.modified_count > 0


def get_workshop_registration_count(workshop_name: str):
    if students_collection == None:
        return 0
    count = students_collection.count_documents({"workshop": workshop_name})
    print(count)
    return count

# create_admin("admin", "admin")
def count_total_students():
    if students_collection == None:
        return 0
    return students_collection.count_documents({})


def count_students_by_event(event_name):
    # Count students participating in a specific event
    count = students_collection.count_documents({"events": event_name})
    return count

def count_students_by_workshop(workshop):
    # Count students participating in a specific event
    count = students_collection.count_documents({"workshop": workshop})
    return count

def count_students_by_paid():
    # Count students participating in a specific event
    count = payment_and_otp_collection.count_documents({"paid": True})
    return count


def count_not_paid_students():
    # Count students with transaction_id starting with "not-paid-"
    not_paid_count = db.payment_and_otp.count_documents({"transaction_id": {"$regex": "^not-paid-"}})
    print(f"Number of students with transaction IDs starting with 'not-paid-': {not_paid_count}")



def new_token_recieve(email: str):
    if token_recieve_collection == None:
        return None
    return token_recieve_collection.insert_one({"email": email, "token_recieve": True, "created_at": datetime.now()})


def update_to_true(email: str):
    if token_recieve_collection == None:
        return None
    return token_recieve_collection.update_one({"email": email}, {"$set": {"token_recieve": True}})


def update_to_false(email: str):
    if token_recieve_collection == None:
        return None
    return token_recieve_collection.update_one({"email": email}, {"$set": {"token_recieve": False}})


def get_token_recieve(email: str):
    if token_recieve_collection == None:
        return None
    return token_recieve_collection.find_one({"email": email})


print("total students: ", count_total_students())


from events import tech_events, non_tech_events, workshops, person, dexters


_tech_events = [i["event_name"] for i in tech_events]
_non_tech_events = [i["event_name"] for i in non_tech_events]
_dexturs = ["Code Trail", "Rapid Relfex"]

events = _tech_events + _non_tech_events + _dexturs

for i in events:
    print(f"{i}: {count_students_by_event(i)}")

_workshops = ["Game Development (Unity)", "Intellifusion", "Web Development (Full Stack)", "Cybersecurity"]


# # count_not_paid_students()
# # print("Students who got verified: ", count_students_by_paid())
for i in _workshops:
    print(count_students_by_workshop(i))
