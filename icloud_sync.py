import os
import time
from threading import Timer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from icloudpy import ICloudPyService
from datetime import datetime

APPLE_ID = "ryxwaer@gmail.com"
PASSWORD = os.getenv('PASSWORD')

# Local and iCloud folder pathsplu
LOCAL_FOLDER = os.path.expanduser('~/Documents/icloud/')
ICLOUD_FOLDER = 'Logseq'

# create script_path/cookies folder if it doesn't exist
cookies_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cookies')
if not os.path.exists(cookies_path):
    os.makedirs(cookies_path)

# Initialize iCloud service
api = ICloudPyService(APPLE_ID, PASSWORD, cookies_path)
api.drive.params["clientId"] = api.client_id


class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.timer = None
        self.changed_files = set()

    def on_modified(self, event):
        if not event.is_directory:
            path = event.src_path
            if event.src_path.endswith(".part"):
                path = event.src_path[:-5]
            print("to modify:", path)
            self.changed_files.add(path)
            self.start_timer()

    def on_deleted(self, event):
        if not event.is_directory:
            print("to delete:", event.src_path)
            self.changed_files.add(event.src_path)
            self.start_timer()

    def start_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(60, self.sync_to_icloud)
        self.timer.start()

    @staticmethod
    def get_drive_dir(path):
        parts = path.split('/')
        drive_obj = api.drive
        for part in parts:
            drive_obj = drive_obj[part]
        return drive_obj

    @staticmethod
    def create_icloud_file(path, file_path):
        parts = path.split('/')
        drive_obj = api.drive
        for part in parts[:-1]:
            if part in drive_obj.dir():
                drive_obj = drive_obj[part]
                continue
            drive_obj.mkdir(part)
        if parts[-1] in drive_obj.dir():
            drive_obj[parts[-1]].delete()
        time.sleep(1)
        with open(file_path, 'rb') as file:
            drive_obj.upload(file)
        print(f"Uploaded to iCloud on {path}")

    def sync_to_icloud(self):
        while self.changed_files:
            file_path = self.changed_files.pop()
            relative_path = os.path.relpath(file_path, LOCAL_FOLDER)
            icloud_path = os.path.join(ICLOUD_FOLDER, relative_path.replace(os.sep, '/'))

            if not os.path.exists(file_path):
                # If the file was deleted locally, remove it from iCloud
                try:
                    self.get_drive_dir(icloud_path).delete()
                    print(f"Deleted {icloud_path} from iCloud")
                except Exception as e:
                    print(f"Error deleting from iCloud: {e}")
            else:
                # If the file was modified, sync the changes
                self.create_icloud_file(icloud_path, file_path)

    def ensure_icloud_folder_path_exists(self, folder_path):
        # Recursively ensure that the folder path exists
        if folder_path and folder_path not in api.drive:
            parent_folder, folder_name = os.path.split(folder_path)
            self.ensure_icloud_folder_path_exists(parent_folder)
            api.drive[parent_folder].create_folder(folder_name)

    def sync_from_icloud(self):
        if not os.path.exists(LOCAL_FOLDER):
            os.makedirs(LOCAL_FOLDER)
        self.pull_recursively(api.drive[ICLOUD_FOLDER], LOCAL_FOLDER)

    def pull_recursively(self, drive, folder):
        for item in drive.dir():
            item_data = drive[item]
            new_local = os.path.join(folder, item_data.name)

            if item_data.type == 'folder':
                os.makedirs(new_local, exist_ok=True)
                self.pull_recursively(item_data, new_local)

            elif item_data.type == 'file':
                if not os.path.exists(new_local) or \
                        item_data.date_modified > datetime.fromtimestamp(os.path.getmtime(new_local)):
                    download = item_data.open(stream=True)
                    with open(new_local, 'wb') as file:
                        file.write(download.raw.read())


if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")

elif api.requires_2sa:
    import click
    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print("  %s: %s" % (i, device.get('deviceName', "SMS to %s" % device.get('phoneNumber'))))

    device = click.prompt('Which device would you like to use?', default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        exit(1)

    code = click.prompt('Please enter validation code')
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        exit(1)


event_handler = ChangeHandler()
print("starting pull...")
event_handler.sync_from_icloud()
print("pulled successfully")

observer = Observer()
observer.schedule(event_handler, LOCAL_FOLDER, recursive=True)
observer.start()
print("listening for local changes...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
