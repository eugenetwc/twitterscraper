from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import urlparse
import time
import pandas as pd

class TwitterScraper:
    def __init__(self, keyword, num_tweets=50, location=None):
        self.twitter_url = "https://twitter.com/"
        self.num_tweets = num_tweets
        self.location = location
        self.query_url = f"{self.twitter_url}search?q={keyword}"
        if location:
            self.query_url += f"%20near%3A{location}"

        self.browser = webdriver.Chrome() # change to firefox if you want
        # self. browser = webdriver.Firefox()

        self.browser.get(self.query_url)
        self.tweet_paths = [] # url paths of tweets

    # Function of waiting until the present of the element on the webpage
    # https://selenium-python.readthedocs.io/waits.html
    def waiting_func(self, xpath):
        try:
            WebDriverWait(self.browser, 20).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except (NoSuchElementException, TimeoutException):
            print(f'{xpath} not found')
            exit()

    def query(self):
        # scroll browser to the top
        self.browser.execute_script(f"window.scrollTo(0, 0)")

        while True:
            # wait for tweets to appear
            self.waiting_func('//article[@role = "article"]')

            # get scroll height
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            traffic_path = self.browser.find_elements_by_xpath("//a[contains(@href, \"status\")]")
            # get all url links
            traffic_path = [traffic.get_attribute('href') for traffic in traffic_path]

            if self.location:
                self.check_account_location(traffic_path)

            # stop if there are enough tweets
            if len(self.tweet_paths) >= self.num_tweets:
                break

            self.browser.execute_script(f"window.scrollTo(0, {last_height+500})")
            time.sleep(1)
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if last_height == new_height:
                break

    # checks if account is from location
    def check_account_location(self, tweet_urls):
        # open new tab
        self.browser.execute_script("window.open('');")
        self.browser.switch_to.window(self.browser.window_handles[1])

        for tweet_url in tweet_urls:
            # get only account url in the form of https://twitter.com/accountname
            o = urlparse(tweet_url)
            account_path = "/" + o.path.split("/")[1]
            o = o._replace(path=account_path)
            account_url = o.geturl()

            self.browser.get(account_url)
            # wait for user profile header to appear
            self.waiting_func('//div[@data-testid=\"UserProfileHeader_Items\"]')
            user_header = self.browser.find_element_by_xpath("//div[@data-testid=\"UserProfileHeader_Items\"]")
            if "Singapore" in user_header.text:
                self.tweet_paths.append(tweet_url)

            # stop if there are enough tweets
            if len(self.tweet_paths) >= self.num_tweets:
                break

        # close tab
        self.browser.close()
        self.browser.switch_to.window(self.browser.window_handles[0])

    def to_csv(self):
        df = pd.DataFrame({'tweet_url': self.tweet_paths})
        df.to_csv('results.csv')

if __name__ == "__main__":
    bot = TwitterScraper("china", 50, "Singapore")
    bot.query()
    bot.to_csv()
    print(bot.tweet_paths)
