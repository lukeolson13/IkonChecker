##################
# TODO: make sure dates are unique
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
    return deets['requests']

def get_requests():
    # gather multiple or a single resort with one or more dates at each
    requests = []
    finished = False
    while not finished:
        resort = get_resort_name(IkonChecker.resorts)
        dates = get_dates()
        requests.append({
            "resort": resort,
            "dates": dates
        })
        finished = input("another resort? y/n ") != "y"
    return requests

def get_resort_name(accepted_resorts):
    # prompt user for a resort name until they enter a valid one
    while True:
        name = input("enter resort name: ")
        if name.upper() in accepted_resorts:
            return name.upper()
        else:
            for res in accepted_resorts:
                print(res)
            print(name, "not found, see accepted names above, case insensitive")
            print()

def get_dates():
    # prompt user for dates returns a chron sorted list of dates
    # as strings in format 'Mon Jan 25 2021'
    dates = []
    while True:
        inp_dates = input("enter your desired date in format 'MM/DD/YYYY' (multiple dates separated by spaces): ")
        try:
            for dt in inp_dates.split(' '):
                date = datetime.datetime.strptime(dt, "%m/%d/%Y").date()
                formatted_date = datetime.datetime.strptime(dt, "%m/%d/%Y").strftime("%a %b %d %Y")
                if date < datetime.date.today():
                    print("{} is in the past".format(formatted_date))
                else:
                    dates.append((date, formatted_date))
            if len(dates) > 0:
                dates.sort(key = lambda i: i[0])
                print()
                for dt in dates:
                    print(dt[1])
                if input("accept? y/n ") == "y":
                    return [dt[1] for dt in dates]
        except ValueError as ex:
            print('please use right format')

if not os.path.exists("Logs"):
    os.mkdir("Logs")
if not os.path.exists("Searches"):
    os.mkdir("Searches")

print("whats up")
my_email = input("enter email for ikon account pls: ")
my_password = getpass.getpass()
load = input("load from file? y/n ") == "y"
if load:
    requests = load_from_file()
else:
    requests = get_requests()
    print("social security number?\n")
    time.sleep(1)
    print('naaaaa')

t = time.strftime("%Y%m%d %H%M%S", time.localtime())
logging.basicConfig(filename="Logs/{}.log".format(t), level=logging.INFO)
log = logging.getLogger()

if not load:
    print("Saved search to file 'Searches/{}.json'".format(t))
    with open("Searches/{}.json".format(t), 'w') as f:
        json.dump({"requests": requests}, f)


exit()
ik = IkonChecker.IkonChecker(log=log)

if not ik.check_login():
    if not ik.login(my_email, my_password):
        ik.close()
        exit()
    
ik.cookie_consent()

finished = False
attempt = 1
print(requests)
while not finished:
    t = time.strftime("%Y%m%d %H%M%S", time.localtime())
    log.info("\n\nATEMPT: {} TIME: {}".format(attempt, t))
    requests = ik.handle_requests(requests)
    print(requests)
    for req in requests:
        if req['status'] == None:
            print("invalid resort")
            requests.remove(req) # invalid resort
        else:
            for dt, stat in zip(req['dates'], req['status']):
                if stat[0] or stat[0] == None:
                    print("reserved or invalid {} {}".format(req['resort'], dt))
                    req['dates'].remove(dt)
            if len(req['dates']) == 0:
                # all dates finished
                requests.remove(req)
    finished = len(requests) == 0
    log.info("WAITING...")
    time.sleep(300)
    attempt += 1

ik.close()