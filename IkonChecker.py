##########
# ToDo: Check year on date
# ToDo: do we need weekdays on the date?
##########
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import presence_of_element_located

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

class IkonChecker:
    def __init__(self, reservation_url, login_url, driver_location, log):
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
        self.log = log

    def click_button(self, button_text):
        xpath = "//button[@class][@data-test='button']/span[text()='{}']".format(button_text)
        try:
            self.driver.find_element_by_xpath(xpath).click()
            return True
        except NoSuchElementException as ex:
            self.log.error("exception: {}".format(ex))
            self.log.error("couldnt find {} button".format(button_text))
            return False

    def close(self):
        self.driver.close()

    def check_login(self):
        try:
            self.driver.find_element_by_xpath("//div[@class='amp-profile-picture']/img[contains(@alt,'Profile photo')]")
            self.log.info("logged in")
            return True
        except NoSuchElementException as ex:
            self.log.info("not logged in")
            return False

    def login(self, email, password):
        # logs in with given email and password, assumes logged out
        self.driver.get(self.login_url)
        try:
            self.driver.find_element_by_id("email").send_keys(email)
            self.driver.find_element(By.ID, "sign-in-password").send_keys(password + Keys.RETURN)
            self.log.info("SUCCESSFULLY LOGGED IN")
            return True
        except Exception as ex:
            self.log.info("already logged in")
            self.log.info("exception: {}".format(ex))
            return True

    def cookie_consent(self):
        # assumes logged in, consents to cookies
        try:
            # the website has mutliple copies of the cookie popup
            xpath = "//div[@aria-label='cookieconsent'][not(contains(@class, 'invisible'))]"
            cookie_divs = self.driver.find_elements(By.XPATH, xpath)
            cookie_divs.reverse()
            for div in cookie_divs:
                div.find_element(By.XPATH, ".//a[@aria-label='dismiss cookie message']").click()
        except Exception as ex:
            self.log.error("exception: {}".format(ex))
            self.log.error("cookie popup not found")
    
    def select_resort(self, resort_name):
        # assumes logged in, selects to resort to get available dates for
        self.driver.get(self.reservation_url)
        resort_xpath = "//*[contains(@id,'react-autowhatever-resort-picker')]/span/span[contains(text(),'{}')]".format(resort_name)
        try:
            self.driver.find_element_by_xpath(resort_xpath).click()
            self.log.info("found", resort_name)
        except NoSuchElementException as ex:
            self.log.error("exception: {}".format(ex))
            self.log.error(resort_name, "not found")
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
        # days from the end of prev month/beginning of next month have "outside" in class
        xpath = "//div[contains(@class, 'DayPicker-Day')][not(contains(@class, 'outside'))]"
        test_date = self.driver.find_element(By.XPATH, xpath).get_attribute("aria-label").split(" ")
        test_month = test_date[1]
        diff = months.index(month) - months.index(test_month)
        if diff < 0:
            self.log.error(date, "is in the past")
            return (None, "past")
        for _ in range(diff):
            # click arrow
            self.driver.find_element_by_xpath("//i[@class='amp-icon icon-chevron-right']").click()
        
        try:
            desired_day = self.driver.find_element_by_xpath("//div[@aria-label='{}']".format(date))
            status = desired_day.get_attribute("class")
            if "unavailable" in status:
                self.log.info(date, "is unavailable :(")
                return (False, "unavailable")
            elif "past" in status:
                self.log.error(date, "is in the past")
                return (None, "past")
            elif "confirmed" in status:
                self.log.info(date, "you already reserved this day")
                return (None, "confirmed")
            else:
                self.log.info(date, "is available")
                return (True, desired_day)     
        except Exception as ex:
            self.log.error("exception: {}".format(ex))
            self.log.error("day not found")
            return (None, "not found")
    
    def reserve_date(self, desired_day):
        # assumes self.driver is logged in and on calendar view, returns True if date reservation successful
        # returns false otherwise
        desired_day.click()
        one = self.click_button("Save")
        two = self.click_button("Continue to Confirm")
        # check box
        try:
            self.driver.find_element_by_xpath("//label[@class='amp-checkbox-input']/input[@type='checkbox']").click()
        except NoSuchElementException as ex:
            self.log.error("exception: {}".format(ex))
            self.log.error("couldnt find checkbox")
            return False
        three = self.click_button("Confirm Reservations")
        return one and two and three
