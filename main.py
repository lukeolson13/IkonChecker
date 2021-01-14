##################
# TODO: multiple searches at once
# TODO: save search to file
# TODO: handle "not requiring reservations" or "external reservations"
# TODO: partial resort names
##################
import IkonChecker
import time
import json
import os
import logging
import getpass
import datetime 

def load_from_file():
    deets = None
    while True:
        path = input("gimme a file path to a json file\n")
        with open(path) as f:
            deets = json.load(f)
            break
    return deets['resort'], deets['date']

def get_resort_name(accepted_resorts):
    # prompt user for a resort name until they enter a valid one
    while True:
        name = input("enter resort name: ")
        if name.upper() in accepted_resorts:
            return name.upper()
        else:
            print(name, "not found, see accepted names below, case insensitive")
            for res in accepted_resorts:
                print(res)
            print()

def get_date():
    # prompt user for date until they enter a valid one
    while True:
        dt = input("enter your desired date in format 'MM/DD/YYYY': ")
        try:
            date = datetime.datetime.strptime(dt, "%m/%d/%Y").date()
            formatted_date = datetime.datetime.strptime(dt, "%m/%d/%Y").strftime("%a %b %d %Y")
            if date < datetime.date.today():
                print("in the past")
            elif input(formatted_date+" y/n? ") == 'y':
                return formatted_date
        except ValueError as ex:
            print('please use right format')

if not os.path.exists("Logs"):
    os.mkdir("Logs")

print("whats up")
my_email = input("enter email for ikon account pls: ")
my_password = getpass.getpass()
if input("load from file? y/n ") == "y":
    my_resort, my_desired_date = load_from_file()
else:
    my_resort = get_resort_name(IkonChecker.resorts)
    my_desired_date = get_date()
    print("social security number?\n")
    time.sleep(1)
    print('naaaaa')

t = time.strftime("%Y%m%d %H%M%S", time.localtime())
logging.basicConfig(filename="Logs/{}.log".format(t), level=logging.INFO)
log = logging.getLogger()

ik = IkonChecker.IkonChecker(log=log)

if not ik.check_login():
    if not ik.login(my_email, my_password):
        ik.close()
        exit()
    
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
        if not reserved:
            log.info("WAITING...\n\n")
            time.sleep(300)
            attempt += 1
    elif response[0] == None:
        reserved = True
    

ik.close()