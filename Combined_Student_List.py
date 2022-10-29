import streamlit as st
import pandas as pd
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

st.set_page_config(
    page_title="Tri Viet Education",
    page_icon=":pager:",
    layout="wide",
    initial_sidebar_state="expanded",
)

def html_to_dataframe(table_header, table_data, course_name=None):
    header_row = []
    df_data = []
    for header in table_header:
        header_row.append(header.text)
    for row in table_data:
        columns = row.find_elements(By.XPATH,"./td") # Use dot in the xpath to find elements with in element.
        table_row = []
        for column in columns:
            table_row.append(column.text)
        df_data.append(table_row)
    df = pd.DataFrame(df_data,columns=header_row)
    df = df.iloc[: , 1:]
    if course_name:
        temp = [course_name for i in range(len(df))]
        df['Course'] = temp
    return df

@st.cache(allow_output_mutation=True)
def load_options():
    # initialize the Chrome driver
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.binary_location = GOOGLE_CHROME_BIN
    options.add_argument('--headless')
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
    # navigate to lop hoc
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc')
    # pulling the main table
    table_header = WebDriverWait(driver, 2).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 2).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
    course_dict = {}
    course_df = html_to_dataframe(table_header, table_data)
    for i in range(1,len(course_df)+1):
        siso_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, f'//*[@id="showlist"]/tr[{i}]/td[5]/a[1]')))
        driver.execute_script("arguments[0].click();", siso_button)
        table_header = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="static"]/thead/tr/th')))
        table_data = WebDriverWait(driver, 3).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="ctl10_container"]/tr')))
        course_dict[str(course_df.iloc[i-1]['Tên Lớp'])] = html_to_dataframe(table_header, table_data)
        # navigate to lop hoc
        driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc')

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