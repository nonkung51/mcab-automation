import json
import os
from supabase import create_client, Client
import uuid
import resend
from dotenv import load_dotenv

load_dotenv(".env.local")

resend.api_key = os.environ["RESEND_API_KEY"]
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")

SUPABASE_BUCKET = "mychildartbook"
JSON_FILE = "order_batches.json"

# Create a Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_image_to_supabase(file_path):
    file_name = os.path.basename(file_path)
    file_ext = "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    uploaded_file_path = f"images/customer-upload/{file_name}"

    with open(file_path, "rb") as file:
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            uploaded_file_path, file
        )
        if response.status_code == 200:
            return uploaded_file_path
        else:
            raise Exception(f"Failed to upload image: {response}")


def insert_order_to_supabase(payload):
    response = supabase.table("book_orders").insert(payload).execute()

    order_data = (
        supabase.from_("book_orders")
        .select("child_images, child_name, order_seq_number")
        .eq("id", response.data[0]["id"])
        .single()
        .execute()
    )

    child_image = order_data.data["child_images"][0]
    storage_output_url = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
        child_image, 15 * 24 * 60 * 60
    )

    if response:
        params: resend.Emails.SendParams = {
            "from": "factory2 <factory2@mychildartbook.com>",
            "to": [
                "non@mychildartbook.com",
                "jean@mychildartbook.com",
                "bow@mychildartbook.com",
            ],
            "subject": f"form for {str(order_data.data['order_seq_number']).zfill(4)} {order_data.data['child_name']} is filled",
            "html": f"""<div><p>children's pic (น้อง{order_data.data['child_name']}): <a href="{storage_output_url['signedURL']}">here</a></p><img src="{storage_output_url['signedURL']}" alt="Image" style="width: 500px;" /><div>""",
        }

        email = resend.Emails.send(params)
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
        "child_images": [child_image_url],
        "stripe_session_id": "promptpay",
        "receiver_name": receiver_name,
        "receiver_facebook": receiver_facebook,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
        "consent_for_promoting": consent_for_promoting,
    }

    return payload


def process_json(file_path):
    with open(file_path, "r", encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)
        for row in data:
            try:
                payload = prepare_payload(row)
                insert_order_to_supabase(payload)
            except Exception as e:
                print(f"Error processing row: {e}")


if __name__ == "__main__":
    process_json(JSON_FILE)
