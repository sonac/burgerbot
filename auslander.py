import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

auslander_url = "https://otv.verwalt-berlin.de/ams/TerminBuchen/wizardng?sprachauswahl=de"

def clickdropdown(id, value):
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, str(id))))
    time.sleep(1)
    select = Select(driver.find_element_by_id(str(id)))
    select.select_by_value(str(value))


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(chrome_options=chrome_options)

def check_for_termin():
  driver.get(auslander_url)

  time.sleep(10)

  driver.find_element_by_id("xi-cb-1").click()
  driver.find_element_by_id("applicationForm:managedForm:proceed").click()

  clickdropdown('xi-sel-400', '361')
  clickdropdown('xi-sel-422', '1')
  clickdropdown('xi-sel-427', '2')

  time.sleep(3)
  driver.find_element_by_xpath('//*[@id="xi-div-30"]/div[2]').click()
  time.sleep(3)
  driver.find_element_by_xpath('//*[@id="inner-361-0-2"]/div/div[1]').click()
  time.sleep(3)
  driver.find_element_by_xpath(
      '//*[@id="SERVICEWAHL_DE361-0-2-3-305244"]').click()

  WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
      (By.ID, 'applicationForm:managedForm:proceed')))
  driver.find_element_by_id("applicationForm:managedForm:proceed").click()

  WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
      (By.XPATH, '//*[@id="header"]/div[1]/a')))
  time.sleep(10)

  html = driver.page_source
  soup = BeautifulSoup(html, 'html.parser')

  for tag in soup.find_all("li", attrs={"class": "errorMessage"}):
      # print(tag)
      # print(tag.getText())
      if not "aktuell keine Termine" in tag.getText():  
        time.sleep(2)
        driver.close()
        return True

  # To-do: search automatically again if none Termine.
  # To-do: if Termine, get them from website and send them to Telegram

  time.sleep(2)
  driver.close()
  return False

if __name__ == '__main__':
  check_for_termin()