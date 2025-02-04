import mechanize
from http.cookiejar import CookieJar
import time
from urllib.parse import quote

from lxml import html
from lxml.html import html5parser as etree
from pyquery import PyQuery as pq

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc  # cài đặt: pip install undetected-chromedriver
# ...existing import, ví dụ mechanize, CookieJar, ...

class CFDownloader:
    def __init__(self) -> None:
        self.__cookieJar = CookieJar()
        self.__browser = mechanize.Browser()
        self.__browser.set_handle_robots(False)
        self.__browser.set_cookiejar(self.__cookieJar)
        self.__browser.addheaders = [
            ('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')
        ]
        
        # Khởi tạo undetected_chromedriver với các tùy chọn
        chrome_options = uc.ChromeOptions()
        # Nếu cần chạy headless, bỏ comment dòng dưới đây
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36")
        self.__driver = uc.Chrome(options=chrome_options)

    def retryMechanize(self, url, timeout):
        try:
            self.__browser.open(url, timeout=timeout)
        except mechanize.URLError:
            print("Error occurred, retrying after 30 seconds...")
            time.sleep(30)
            self.__browser.open(url, timeout=timeout)

        html = self.__browser.response().read().decode('utf-8', errors='ignore')
        self.__driver.get(url)
        try:
            WebDriverWait(self.__driver, 60).until(
                lambda driver: "Your browser is being checked" not in driver.page_source and
                                "Please wait" not in driver.page_source and
                                driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            print("Timeout while waiting for Cloudflare check to pass:", e)
        return self.__driver.page_source

            

    def login(self, handle, password):
        loginUrl = "https://mirror.codeforces.com/enter"
        print("Navigating to login page via Selenium...")
        self.__driver.get(loginUrl)
        try:
            # Chờ đến khi xuất hiện trường đăng nhập (handle/email)
            WebDriverWait(self.__driver, 30).until(
                lambda d: d.find_element(By.NAME, "handleOrEmail")
            )
        except Exception as e:
            print("Error waiting for login fields:", e)
            return

        try:
            # Tìm các trường đăng nhập và điền thông tin
            handle_input = self.__driver.find_element(By.NAME, "handleOrEmail")
            password_input = self.__driver.find_element(By.NAME, "password")
            handle_input.clear()
            handle_input.send_keys(handle)
            password_input.clear()
            password_input.send_keys(password)
            # Nhấn nút đăng nhập (tìm nút bằng input[type=submit])
            login_button = self.__driver.find_element(By.XPATH, "//input[@type='submit']")
            time.sleep(3)
            print("Login attempted via Selenium. Check browser state for success.")
            login_button.click()
            # Nếu cần, bạn có thể chuyển cookie từ Selenium sang mechanize sau đăng nhập
            for cookie in self.__driver.get_cookies():
                cookie_str = f"{cookie['name']}={cookie['value']}"
                self.__browser.addheaders.append(("Cookie", cookie_str))
        except Exception as e:
            print("Login process encountered an error:", e)
    
    def getSourceCode(self, groupId, contestId, submissionId):
        url = f"https://mirror.codeforces.com/group/{groupId}/contest/{contestId}/submission/{submissionId}"
        html_content = self.retryMechanize(url, 10)
        # Nếu html_content rỗng, thử dùng Selenium page_source
        if not html_content or "program-source-text" not in html_content:
            print("Mechanize cant get source code, trying to extract from Selenium...")
            html_content = self.__driver.page_source

        try:
            # Sử dụng PyQuery trực tiếp từ html_content
            doc = pq(html_content)
            code_text = doc("#program-source-text").text()
            if not code_text:
                print("Not found code in page, trying to extract from HTML...")
            return code_text
        except Exception as e:
            print("Error parsing source code:", e)
            return ""
    
