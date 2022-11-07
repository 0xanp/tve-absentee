import collections
import pandas as pd
import html_to_json
import json
import time 
from dotenv import load_dotenv
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

# getting credentials from environment variables
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")


def html_to_dataframe(driver, table_data):
    course_dict = {}
    # iterate through the table of students with their attendance 
    # each student has a dictionary of dates where each date has a dictionary
    # of specific critera of evaluation: attendance, puncutuality, homework,
    # attitude, and other comments, each criterion sometimes has sub-criteria as 
    # well

    # "student" here represents a row in the table data pulled using selenium
    for student in table_data:
        # each student (row) has a collection of dates (column)
        dates = student.find_elements(By.XPATH,"./td")
        # iterate through each date and construct a dictionary of evaluation critera
        for date in dates:
            try:
                # first "date" is the name of the student
                name = date.find_element(By.XPATH, './b')
                # assign each student their own collection of dates
                course_dict[name.text] = {}
                #print(f"{name.text}")
                print("done getting student name")
            except:
                try:
                    href = date.find_element(By.XPATH,"./div/a").get_attribute('href')
                    driver.execute_script(href)
                    time.sleep(.5)
                    criteria = driver.find_elements(By.CLASS_NAME,"form-group")
                    date = driver.find_element(By.XPATH,'//*[@id="zDiemdanh_style1_ngay"]').get_attribute('value')
                    # then assign each date its own dict as well
                    course_dict[name.text][date] = {}
                    #print(date)
                    print('done getting a date')
                    for criteron in criteria:
                        labels = criteron.find_elements(By.XPATH,"./label")
                        if labels[0].text.strip() == "Chọn lớp" or labels[0].text.strip() == "Ngày":
                            continue
                        elif labels[0].text.strip() == "Nhận xét khác/ Other comments":
                            other_comments = driver.find_element(By.XPATH,'//*[@id="zDiemdanh_style1_comment"]').get_attribute('value')
                            course_dict[name.text][date]['Nhận xét khác/ Other comments'] = other_comments
                            print('done getting other comments')
                            #print("Nhận xét khác/ Other comments:", other_comments)                         
                        else:
                            #print(labels[0].text)
                            criteria_label = labels[0].text
                            course_dict[name.text][date][criteria_label] = {}
                            labels.remove(labels[0])
                            print('done getting a criterion')
                            for label in labels:
                                course_dict[name.text][date][criteria_label][label.text] = label.find_element(By.XPATH,"./input").get_attribute("checked")
                                #print(f'{label.text}: {label.find_element(By.XPATH,"./input").get_attribute("checked")}') 
                                print('done getting a sub-criterion')
                except:
                    pass
                pass
    '''
        df_data.append(table_row)
    df = pd.DataFrame(df_data,columns=header_row)
    df = df.iloc[: , 1:]
    if course_name:
        temp = [course_name for i in range(len(df))]
        df['Course'] = temp
    return df
    '''
    return course_dict

def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    #options.add_argument('--headless')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(chrome_options=options, executable_path=CHROMEDRIVER_PATH)
    # login page
    driver.get("https://trivietedu.ileader.vn/login.aspx")
    # find username/email field and send the username itself to the input field
    driver.find_element("id","user").send_keys(MANAGER_USERNAME)
    # find password input field and insert password as well
    driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
    # click login button
    driver.find_element(By.XPATH,'//*[@id="login"]/button').click()
    # navigate to diem danh
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!diemdanh')
    
    # pulling the main table
#    table_header = WebDriverWait(driver, 10).until(
#                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
    course_dicts = {}
    course_dicts['Test'] = html_to_dataframe(driver, table_data)
    with open('test.json', 'w') as fp:
        json.dump(course_dicts, fp)
    #return driver, course_dicts

load_options()