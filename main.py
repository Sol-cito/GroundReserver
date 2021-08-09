from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from typing import *

option = Options()
option.add_argument('--start-maximized')

# start chrome
webdriver = webdriver.Chrome(chrome_options=option)

# get to login page
webdriver.get("https://yeyak.seoul.go.kr/")
webdriver.find_element_by_class_name("state").find_element_by_css_selector("a").click()

# excute login
input_id = webdriver.find_element_by_id("userid")
input_id.send_keys('dataenggu')
input_id = webdriver.find_element_by_id("userpwd")
input_id.send_keys('Solda9010!')

submitBtn = webdriver.find_element_by_class_name("btn_login")
submitBtn.submit()

# move to soccer ground reservation webpage
webdriver.get("https://yeyak.seoul.go.kr/web/search/selectPageListDetailSearchImg.do?code=T100&dCode=T107")

# get every ground item as a list
board = webdriver.find_element_by_class_name("img_board")
items: List[WebElement] = board.find_elements_by_xpath("li")
for ele in items:
    print(ele.text)