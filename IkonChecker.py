##########
# TODO: make cookie consent better
# TODO: handle "no remaining reservations"
# TODO: gets stuck on "Continue to confirm" then throws error on for checkbox
##########
import logging
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import random

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class IkonChecker:
    def __init__(self, 
            reservation_url="https://account.ikonpass.com/en/myaccount/add-reservations/", 
            login_url="https://account.ikonpass.com/en/login", 
            driver_location="C:/Program Files/chromedriver/chromedriver.exe",
            log = None
        ):
        """
        reservation_url = the URL access point to the reservation system
        driver_location = filepath to the chrome driver on your computer
        log = python logger to write notes to
        """
        self.reservation_url = reservation_url
        self.login_url = login_url
        self.driver = webdriver.Chrome(driver_location)
        self.driver.maximize_window()
        self.driver.implicitly_wait(2) # wait 2 seconds for any elements not found immediately
        if log == None:
            self.log = logging.getLogger()
        else:
            self.log = log
        self.log_indent = ''

    def handle_requests_test(self, requests):
        for i in range(len(requests)):
            if random.random() < 0.05:
                requests[i]['status'] = None
            else:
                requests[i]['status'] = [(random.random() > 0.5, 'message') for _ in requests[i]['dates']]
        return requests
    
    def handle_requests(self, requests):
        # handles a batch of requests, checks for multiple dates at multiple resorts
        # requests is a list of dicts = [
        # { "resort": "RESORT NAME", "dates": ["Dates", "Desired"]}, ...
        # ]
        # dates in format as requested by self.find_date(), in chron order
        # appends to each dict a status array and returns the requests list
        # status = None if resort not found
        # status = [(bool/None, "msg"), ...] if resort is found. One elm for each date,
        # bool/none as returned by either find_date() or reserve_date()
        if not type(requests) == list:
            raise ValueError("invalid value for 'requests': {}".format(requests))
        
        for i in range(len(requests)):
            self.log_indent = '\t'
            resort = requests[i]["resort"]
            status = []
            if self.select_resort(resort):
                self.log_indent = '\t\t'
                for dt in requests[i]["dates"]:
                    response = self.find_date(dt)
                    if response[0]: # date found and available
                        status.append(self.reserve_date(response[1]))
                    else: # date is invalid or unavailable
                        status.append(response)
                requests[i]["status"] = status
            else:
                requests[i]["status"] = None
        
        self.log_indent = ''
        return requests

                
                
    def log_it(self, level, message):
        # level = "INFO" "ERROR" message must be a string
        if level == "INFO":
            self.log.info(self.log_indent + message)
        elif level == "ERROR":
            self.log.error(self.log_indent + message)

    def click_button(self, button_text):
        xpath = "//button[@class][@data-test='button']/span[text()='{}']".format(button_text)
        try:
            self.driver.find_element_by_xpath(xpath).click()
            return True
        except NoSuchElementException as ex:
            self.log_it("ERROR", "exception: {}".format( ex))
            self.log_it("ERROR", "couldnt find {} button".format(button_text))
            return False

    def close(self):
        self.driver.close()
    
    def get_driver(self):
        return self.driver

    def check_login(self):
        try:
            self.driver.find_element_by_xpath("//div[@class='amp-profile-picture']/img[contains(@alt,'Profile photo')]")
            self.log_it("INFO", "logged in")
            return True
        except NoSuchElementException as ex:
            self.log_it("INFO", "not logged in")
            self.log_it("INFO", "ex: {}".format(ex))
            return False

    def login(self, email, password):
        # logs in with given email and password, assumes logged out
        self.driver.get(self.login_url)
        try:
            self.driver.find_element_by_id("email").send_keys(email)
            self.driver.find_element_by_id("sign-in-password").send_keys(password + Keys.RETURN)
            if self.check_login():
                self.log_it("INFO", "SUCCESSFULLY LOGGED IN")
                return True
            else:
                self.log_it("ERROR", "Unsuccessful log in. Check username and password")
                return False
        except Exception as ex:
            self.log_it("INFO", "already logged in")
            self.log_it("INFO", "exception: {}".format(ex))
            return True

    def cookie_consent(self):
        # assumes logged in, consents to cookies
        try:
            # the website has mutliple copies of the cookie popup
            xpath = "//div[@aria-label='cookieconsent'][not(contains(@class, 'invisible'))]"
            cookie_divs = self.driver.find_elements_by_xpath(xpath)
            cookie_divs.reverse()
            for div in cookie_divs:
                div.find_element_by_xpath(".//a[@aria-label='dismiss cookie message']").click()
        except Exception as ex:
            self.log_it("ERROR","exception: {}".format(ex))
            self.log_it("ERROR", "cookie popup not found")
    
    def select_resort(self, resort_name, resort_xpath=None):
        # assumes logged in, selects to resort to get available dates for
        # assumes resort_name upper case
        self.driver.get(self.reservation_url)
        if resort_xpath == None:
            text_to_upper = "translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')"
            resort_xpath = "//*[contains(@id,'react-autowhatever-resort-picker')]/span/span[{}='{}']".format(text_to_upper, resort_name)
        try:
            self.driver.find_element_by_xpath(resort_xpath).click()
            self.log_it("INFO","found {}".format(resort_name))
        except NoSuchElementException as ex:
            self.log_it("ERROR", "exception: {}".format(ex))
            self.log_it("ERROR", "{} not found".format(resort_name))
            return False
        return self.click_button("Continue")

    def find_date(self, date):
        # assumes driver is logged in, and on resort that is desired
        # will search for date provided to see if it is available
        # date = "<day of week, 3> <month, 3> <day, int> <year, int>"
        # returns a tuple (bool, day_element/string)
            # returns (True,day_element) if date is available, returns (False, status) if date is unavailable
            # returns (None,status) if date is invalid (in the past, already booked, not found)

        # check that calendar is on right month
        month = date.split(" ")[1]
        year = date.split(" ")[3]
        # days from the end of prev month/beginning of next month have "outside" in class
        xpath = "//div[contains(@class, 'DayPicker-Day')][not(contains(@class, 'outside'))]"
        test_date = self.driver.find_element_by_xpath(xpath).get_attribute("aria-label").split(" ")
        test_month = test_date[1]
        test_year = test_date[3]
        diff = months.index(month) - months.index(test_month) + 12*(int(year) - int(test_year))
        if diff < 0:
            self.log_it("ERROR", "{} is in the past".format(date))
            return (None, "past")
        for _ in range(diff):
            # click arrow
            self.driver.find_element_by_xpath("//i[@class='amp-icon icon-chevron-right']").click()
        
        try:
            desired_day = self.driver.find_element_by_xpath("//div[@aria-label='{}']".format(date))
            status = desired_day.get_attribute("class")
            if "unavailable" in status:
                self.log_it("INFO","{} is unavailable :(".format(date))
                return (False, "unavailable")
            elif "past" in status:
                self.log_it("ERROR", "{} is in the past".format(date))
                return (None, "past")
            elif "confirmed" in status:
                self.log_it("INFO","you already reserved {}".format(date))
                return (None, "confirmed")
            else:
                self.log_it("INFO","{} is available".format(date))
                return (True, desired_day)     
        except Exception as ex:
            self.log_it("ERROR", "exception: {}".format(ex))
            self.log_it("ERROR", "day not found")
            return (None, "not found")
    
    def reserve_date(self, desired_day):
        # assumes self.driver is logged in and on calendar view, returns True if date reservation successful
        # returns false otherwise
        desired_day.click()
        self.click_button("Save")
        self.click_button("Continue to Confirm")
        # check box
        try:
            self.driver.find_element_by_xpath("//label[@class='amp-checkbox-input']/input[@type='checkbox']").click()
        except NoSuchElementException as ex:
            self.log_it("ERROR", "exception: {}".format(ex))
            self.log_it("ERROR", "couldnt find checkbox")
            return (False, "reservation failed")
        self.click_button("Confirm Reservations")
        try:
            self.driver.find_element_by_xpath("//i[contains(@class,'amp-icon icon-success')]")
            self.log_it("INFO", "Successfully booked!")
            return (True, "reservation success")
        except NoSuchElementException as ex:
            self.log_it("ERROR", "exception: {}".format(ex))
            self.log_it("ERROR", "Reservation failed")
            return (False, "reservation failed")

resorts = [
    "ALTA SNOWBIRD",
    "ARAPAHOE BASIN",
    "BIG SKY",
    "BRIGHTON",
    "COPPER MOUNTAIN",
    "DEER VALLEY",
    "ELDORA",
    "SOLITUDE MOUNTAIN RESORT",
    "STEAMBOAT",
    "TAOS",
    "WINTER PARK RESORT",
    "BIG BEAR MOUNTAIN RESORT",
    "JUNE MOUNTAIN",
    "MAMMOTH MOUNTAIN",
    "SQUAW VALLEY ALPINE MEADOWS",
    "BOYNE HIGHLANDS RESORT",
    "BOYNE MOUNTAIN RESORT",
    "CRYSTAL MOUNTAIN RESORT",
    "MT. BACHELOR",
    "THE SUMMIT AT SNOQUALMIE",
    "KILLINGTON",
    "LOON MOUNTAIN",
    "SNOWSHOE",
    "STRATTON",
    "SUGARBUSH",
    "SUGARLOAF",
    "SUNDAY RIVER",
    "WINDHAM MOUNTAIN",
    "BLUE MOUNTAIN",
    "TREMBLANT",
    "CYPRESS MOUNTAIN",
    "RED MOUNTAIN",
    "REVELSTOKE",
    "SKI BIG 3",
    "CORONET PEAK, THE REMARKABLES, MT HUTT",
    "MT. BULLER",
    "THREDBO",
    "NISEKO UNITED",
    "VALLE NEVADO",
    "ZERMATT"
]
