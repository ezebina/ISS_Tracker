from email.message import EmailMessage
import smtplib
import ssl
import requests
from datetime import datetime
from pytz import utc
from dotenv import load_dotenv
from time import sleep
import os


load_dotenv()

# Constants
MY_LATITUDE = 6.628260
MY_LONGITUDE = 3.375070
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVERS = os.getenv("EMAIL_RECEIVERS")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def iss_tracker():
    """
    Checks if the ISS is within a 5-degree radius of the user's location.
    """
    try:
        response = requests.get(url="http://api.open-notify.org/iss-now.json")
        response.raise_for_status()
        data = response.json()

        iss_latitude = float(data["iss_position"]["latitude"])
        iss_longitude = float(data["iss_position"]["longitude"])

        if (MY_LATITUDE - 5 <= iss_latitude <= MY_LATITUDE + 5 and
            MY_LONGITUDE - 5 <= iss_longitude <= MY_LONGITUDE + 5):
            return True
    except requests.RequestException as e:
        print(f"Error fetching ISS data: {e}")
    return False

def is_night():
    """
    Checks if it's nighttime at the user's location based on sunrise-sunset data.
    """
    try:
        current_time = datetime.now(utc).hour
        parameters = {"lat": MY_LATITUDE, "lon": MY_LONGITUDE, "formatted": 0}
        response = requests.get(url="https://api.sunrise-sunset.org/json", params=parameters)
        response.raise_for_status()
        data = response.json()

        sunset = int(data["results"]["sunset"].split('T')[1].split(":")[0])
        sunrise = int(data["results"]["sunrise"].split('T')[1].split(":")[0])

        if sunset <= current_time or current_time <= sunrise:
            return True
    except requests.RequestException as e:
        print(f"Error fetching sunrise/sunset data: {e}")
    return False

def send_email():
    """
    Sends an email notification if the ISS is overhead and it's nighttime.
    """
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            for name, email in EMAIL_RECEIVERS:
                msg = EmailMessage()
                msg["Subject"] = "ISS Tracker Alert"
                msg["From"] = EMAIL_SENDER
                msg["To"] = email
                msg.set_content(
                    f"Dear {name},\n\n"
                    f"The International Space Station is currently over your location.\n"
                    f"Latitude: {MY_LATITUDE}, Longitude: {MY_LONGITUDE}\n\n"
                    "Look up at the sky to catch a glimpse of it!"
                )
            server.send_message(msg)
            print(f"Email sent successfully to {name} at {email}.")

    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")

def main():
    while True:
        sleep(60)  # Check every minute
        if iss_tracker() and is_night():
            send_email()

if __name__ == "__main__":
    main()
