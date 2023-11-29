# icloud_sync
script to sync Logseq folder between iCloud and my linux PC

On startup it will pull all newly created or changed files from the iCloud drive to local storage `~/Documents/icloud`.
After files are changed locally or new files are created it will start the timer which will push all the changes to the icloud drive after no other change is made within the one minute time period.

### instalation
```
pip install -r requirements.txt
export PASSWORD=password
python icloud_sync.py
```
then login with 2fa

session will be saved in the cookies

### autostart
Copy icloud_sync.desktop into/home/ryxwaer/.config/autostart/

change password and path to the executable
