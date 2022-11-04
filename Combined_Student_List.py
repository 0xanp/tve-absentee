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


def html_to_dataframe(driver, table_header, table_data, course_name=None):
    header_row = []
    df_data = []
    for header in table_header:
        header_row.append(header.text)
    for row in table_data:
        columns = row.find_elements(By.XPATH,"./td") # Use dot in the xpath to find elements with in element.
        table_row = []
        for column in columns:
            try:
                name = column.find_element(By.XPATH, './b')
                #table_row.append(name.text)
                print(f"{name.text}")
            except:
                try:
                    href = column.find_element(By.XPATH,"./div/a").get_attribute('href')
                    driver.execute_script(href)
                    time.sleep(.8)
                    forms = driver.find_elements(By.CLASS_NAME,"form-group")
                    date = driver.find_element(By.XPATH,'//*[@id="zDiemdanh_style1_ngay"]').get_attribute('value')
                    print(date)
                    for form in forms:
                        labels = form.find_elements(By.XPATH,"./label")
                        if labels[0].text.strip() == "Chọn lớp" or labels[0].text.strip() == "Ngày":
                            continue
                        elif labels[0].text.strip() == "Nhận xét khác/ Other comments":
                            other_comments = driver.find_element(By.XPATH,'//*[@id="zDiemdanh_style1_comment"]').get_attribute('value')
                            print("Nhận xét khác/ Other comments:", other_comments)                         
                        else:
                            print(labels[0].text)
                            labels.remove(labels[0])
                            for label in labels:
                                print(f'{label.text}: {label.find_element(By.XPATH,"./input").get_attribute("checked")}') 
                except:
                    pass
                pass
        df_data.append(table_row)
    df = pd.DataFrame(df_data,columns=header_row)
    df = df.iloc[: , 1:]
    if course_name:
        temp = [course_name for i in range(len(df))]
        df['Course'] = temp
    return df

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
    table_header = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
    course_dict = {}
    course_df = html_to_dataframe(driver, table_header, table_data)
    print(course_df)

    return driver, course_df, course_dict

driver, course_df, course_dict = load_options()
placeholder = st.empty()

placeholder.selectbox(
'Class',
(list(course_df['Tên Lớp'])),
disabled=True, 
key='3'
)
big_df = pd.DataFrame()
for course_name, course_students in course_dict.items():
    small_df = course_dict[course_name]
    small_df[course_name] = [course_name for i in len(small_df)]
    big_df = pd.concat([big_df, small_df])
st.table(big_df)