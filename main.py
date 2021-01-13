##################
# ToDo: validate inputs
##################
from selenium import webdriver
from IkonChecker import IkonChecker
import time
import json
import logging
import getpass

def load_from_file():
    deets = None
    while True:
        path = input("gimme a file path to a json file\n")
        with open(path) as f:
            deets = json.load(f)
            break
    return deets["email"], deets['password'], deets['resort'], deets['date']

print("whats up")
my_email = input("enter email pls: ")
my_password = getpass.getpass()
if input("load from file? y/n ") == "y":
    my_resort, my_desired_date = load_from_file()
else:
    my_resort = input("desired resort (spell very carefully)\n")
    my_desired_date = input("desired date in format: Mon Jan 15 2021\n")
    print("social security number?\n")
    time.sleep(1)
    print('naaaaa')

t = time.strftime("%Y%m%d %H%M%S", time.localtime())
logging.basicConfig(filename="Logs/{}.log".format(t), level=logging.INFO)
log = logging.getLogger()

reservation_url = "https://account.ikonpass.com/en/myaccount/add-reservations/"
driver_location = "C:/Program Files/chromedriver/chromedriver.exe"
login_url = "https://account.ikonpass.com/en/login"

ik = IkonChecker(reservation_url, login_url, driver_location, log)

if not ik.check_login():
    ik.login(my_email, my_password)
    
ik.cookie_consent()

reserved = False
attempt = 1
while not reserved:
    if not ik.check_login():
        ik.login(my_email, my_password)
    log.info("ATTEMPT: {}. TIME: {}".format(attempt, time.strftime("%H:%M:%S", time.localtime())))
    ik.select_resort(my_resort)
    response = ik.find_date(my_desired_date)
    if response[0]:
        reserved = ik.reserve_date(response[1])
    elif response[0] == None:
        reserved = True
    log.info("WAITING...\n\n")
    time.sleep(300)
    attempt += 1

ik.close()