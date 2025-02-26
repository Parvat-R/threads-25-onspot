import csv
import database as db

def get_paper_ppt_emails():
    res = db.students_collection.find(
        {"events": "Paper Presentation - Innovate & Present"}
    )
    return [i["email"] for i in res]

def check_paid(emails: list):
    res = {}
    for i in emails:
        ores = db.payment_and_otp_collection.find_one({"email": i})
        if ores:
            res[i] = ores
    
    return res

def save_to_csv(data_dict, filename="payment_data.csv"):
    # Check if dictionary is empty
    if not data_dict:
        print("No data to save!")
        return
    
    # Get the keys from the first entry to use as CSV headers
    # Assumes all dictionary entries have the same schema
    first_entry = next(iter(data_dict.values()))
    fieldnames = ["email"] + list(first_entry.keys())
    
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write each row
            for email, data in data_dict.items():
                row_data = {"email": email}
                row_data.update(data)
                writer.writerow(row_data)
                
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

# Get the payment data
dict_data = check_paid(get_paper_ppt_emails())

# Save to CSV
save_to_csv(dict_data)