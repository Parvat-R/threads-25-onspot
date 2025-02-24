from flask import (
    Flask, render_template, request,
    url_for, redirect, flash,
    get_flashed_messages, session
)
import database as db
import emails
from events import tech_events, non_tech_events, workshops, person, dexters


_tech_events = [i["event_name"] for i in tech_events]
_non_tech_events = [i["event_name"] for i in non_tech_events]
_dexturs = ["Code Trail", "Rapid Relfex"]

events = _tech_events + _non_tech_events + _dexturs


app = Flask(__name__)
app.secret_key = "this i s a secret key"


@app.get("/")
def index():
    return render_template('index.html')


@app.get("/register")
def register():
    if "student_id" in session:
        flash("You are already registered!", "danger")
        return redirect(url_for("myid"))
    for i in workshops:
        i["seats_filled"] = db.get_workshop_registration_count(i["event_name"])
        if i["seats_filled"] >= i["seats"]:
            i["disabled"] = True
    return render_template(
        "register.html",
        workshops=workshops,
        events=events,
        _tech_events=_tech_events,
        _non_tech_events=_non_tech_events,
        _dexturs=_dexturs)


@app.post("/register")
def register_post():
    try:
        name = request.form["name"]
        email = request.form.get("email", "").strip().lower()
        phone = request.form["phone"]
        workshop = request.form.get("workshop", None)
        # Changed to getlist for multiple events
        selected_events = request.form.getlist("events")
        college_name = request.form["college_name"]
        payment_type = request.form["payment_method"]
        transaction_id = request.form.get("transaction_id", None)
        upi_id = request.form.get("upi_id", None)
        paid = request.form.get("paid", None)
        paid = True if paid == "paid" else False

        print("all getails got")

        if db.student_exists(email, phone):
            flash("Error: Email, Phone already exists! Try logging in.", "danger")
            return redirect(url_for("register"))

        student_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "workshop": workshop,
            "events": selected_events,  # Now it's a list
            "college_name": college_name
        }
        _id = db.create_student(student_data)

        if not _id:
            raise Exception("Failed to create student")

        tsid = transaction_id if transaction_id else f'o-{payment_type}-{_id}'

        db.create_payment_entry({
            "email": email,
            "paid": True,
            "transaction_id": tsid,
            "upi_id": upi_id
        })
        payment_data = db.get_payment_by_email(email)
        flash("Registration successful!", "success")
        emails.send_id_mail(student_data, payment_data, f"https://threadscse.co.in/admin/student/{_id}")

    except Exception as e:
        flash(f"Error: Registration failed! {e}", "danger")

    return redirect(url_for("register"))


if __name__ == '__main__':
    app.run(debug=True)
