import firebase_admin
from firebase_admin import credentials, db
from stls_lib import stls

def initialize_firebase(status: str):
    """
    Initializes Firebase Realtime Database based on the given status.
    """
    if status.lower() == "on":
        try:
            service_acc_key_path = "src/private_api/serviceAccountKey.json"
            stls.check_exist_file(service_acc_key_path)
            cred = credentials.Certificate(service_acc_key_path)
            firebase_admin.initialize_app(
                cred,
                {
                    'databaseURL': 'https://smart-traffic-light-syst-5a31b-default-rtdb.asia-southeast1.firebasedatabase.app/'
                }
            )
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error in initializing Firebase: {e} - Check service account file and database URL.")
    elif status.lower() == "off":
        print("Firebase initialization skipped. Status is off.")
    else:
        print(f"Invalid status provided: {status}. Please use 'on' or 'off'.")

def send_data_in_firebase(data, status: str):
    """
    Sends data to the Firebase Realtime Database if the status is "on".
    """
    if status.lower() == "on":
        try:
            ref = db.reference('/zones')  # Path to your Firebase database
            ref.child('z0-z1').set(f"{data[0]}&{data[1]}")  # Update specific fields in '/zones'
            print(f"Data sent to Firebase: {data[0]}&{data[1]}")
        except Exception as e:
            print(f"Error sending data to Firebase: {e}. Check internet connection or database permissions.")
    elif status.lower() == "off":
        print("Data sending skipped. Status is off.")
    else:
        print(f"Invalid status provided: {status}. Please use 'on' or 'off'.")