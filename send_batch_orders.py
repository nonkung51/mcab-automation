import csv
import os
from supabase import create_client, Client
import uuid
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

SUPABASE_BUCKET = "mychildartbook"
CSV_FILE = "order_batches.csv"

# Create a Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_supabase(file_path):
    file_name = os.path.basename(file_path)
    file_ext = "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    uploaded_file_path = f"images/customer-upload/{file_name}"
    
    with open(file_path, 'rb') as file:
      response = supabase.storage.from_(SUPABASE_BUCKET).upload(uploaded_file_path, file)
      if response.status_code == 200:
          return uploaded_file_path
      else:
          raise Exception(f"Failed to upload image: {response}")


def insert_order_to_supabase(payload):
    response = supabase.table("order").insert(payload).execute()
    
    if response.status_code == 201:
        print("Order inserted successfully.")
    else:
        raise Exception(f"Failed to insert order: {response}")

def prepare_payload(row):
    email = row["email"]
    child_name = row["childName"]
    gender = row["gender"]
    book_template = row["bookTemplate"]
    child_image_path = row["childImage"]
    receiver_name = row["receiverName"]
    receiver_facebook = row["receiverFacebook"]
    receiver_phone = row["receiverPhone"]
    receiver_address = row["receiverAddress"]
    consent_for_promoting = row["consentForPromoting"]

    # Upload the image and get the URL
    child_image_url = upload_image_to_supabase(child_image_path)

    # Prepare the payload
    payload = {
        "email": email,
        "child_name": child_name,
        "status": "form filled",
        "gender": gender,
        "book_template": book_template,
        "child_image": [child_image_url],
        "stripe_session_id": "promptpay",
        "receiver_name": receiver_name,
        "receiver_facebook": receiver_facebook,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
        "consent_for_promoting": consent_for_promoting.lower() == "yes",
    }

    return payload

def process_csv(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                payload = prepare_payload(row)
                insert_order_to_supabase(payload)
            except Exception as e:
                print(f"Error processing row: {e}")

if __name__ == "__main__":
    pass
