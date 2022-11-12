import json
from dotenv import load_dotenv
import os
from datetime import datetime
import wx
import wx.adv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# getting credentials from environment variables
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")

class HelloFrame(wx.Frame):
    """
    A Frame
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(HelloFrame, self).__init__(*args, **kw)
        self.SetBackgroundColour('#ffffff')
        self.maxPercent = 100
        self.percent = 0
        self.ok_button = wx.Button(self, wx.ID_OK, label='Ok')
        self.startdatepicker = wx.adv.CalendarCtrl(self, 1, wx.DateTime.Now())
        self.enddatepicker = wx.adv.CalendarCtrl(self, 2, wx.DateTime.Now())
        self.start_date = self.startdatepicker.PyGetDate().date()
        self.end_date = self.enddatepicker.PyGetDate().date()
        vertical_container = wx.BoxSizer(wx.VERTICAL)
        vertical_container.AddSpacer(10)
        vertical_container.AddSpacer(10)
        vertical_container.Add(self.startdatepicker, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        vertical_container.Add(self.enddatepicker, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        vertical_container.AddSpacer(10)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.ok_button, 0)

        vertical_container.Add(button_sizer, 0, wx.LEFT | wx.RIGHT, 15)
        vertical_container.AddSpacer(20)
        self.SetSizerAndFit(vertical_container)
        self.Bind(wx.adv.EVT_CALENDAR_SEL_CHANGED, self.OnStartDateChanged, self.startdatepicker)
        self.Bind(wx.adv.EVT_CALENDAR_SEL_CHANGED, self.OnEndDateChanged, self.enddatepicker)
        self.Bind(wx.EVT_BUTTON, self.OnOkClick, self.ok_button)

    def html_to_dataframe(self, driver, table_data):
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
                    name = date.find_element(By.XPATH, './b').text
                    # assign each student their own collection of dates
                    course_dict[name] = []
                    print(f"{name}")
                    #print("done getting student name")
                except:
                    try:
                        absent_dates = date.find_elements(By.XPATH,"./div/a/i")
                        for absent_date in absent_dates:
                            if absent_date.get_attribute("class") == "fa fa-check-circle fa-red":
                                absent_date = datetime.strptime(absent_date.get_attribute("id").split("_")[-1],"%d-%m-%Y")
                                if absent_date.date() >= self.start_date and absent_date.date() <= self.end_date:
                                    course_dict[name].append(absent_date.strftime("%d/%m/%Y"))
                                    print(absent_date.strftime('%A'),absent_date.strftime("%d/%m/%Y"))
                    except:
                        pass
                    pass
        return course_dict

    def load_options(self):
        # initialize the Chrome driver
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        #options.add_argument('--headless')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))
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
        course_select = Select(WebDriverWait(driver, 1.5).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="cp_lophoc"]'))))
        return driver, course_select
    
    def showProgress(self):
        self.progress = wx.ProgressDialog("Pulling Absentee Data in progress...", "Please wait!", maximum=self.maxPercent, parent=self, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)

    def destoryProgress(self):
        self.progress.Destroy()

    def OnStartDateChanged(self, evt):
        self.start_date = evt.PyGetDate().date()
        #print(self.start_date, type(self.start_date))

    def OnEndDateChanged(self, evt):
        self.end_date = evt.PyGetDate().date()
        #print(self.end_date, type(self.end_date))

    def OnOkClick(self, evt):
        start_time = datetime.now()
        driver, course_select = self.load_options()
        percent = 0
        course_dicts = {}
        self.maxPercent = len(course_select.options)
        self.showProgress()
        for course in course_select.options:
            try:
                print("Getting Absentee data for",course.text)
                course_select.select_by_visible_text(course.text)
                time.sleep(25)
                table_data = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
                course_dicts[course.text] = self.html_to_dataframe(driver, table_data)
                percent += 1
                self.progress.Update(percent)
            except:
                percent += 1
                self.progress.Update(percent)
                pass
            break
        print(course_dicts)
        df = pd.DataFrame()
        courses = []
        names = []
        dates = []
        for course in course_dicts:
            for student in course_dicts[course]:
                if len(course_dicts[course][student]) != 0:
                        courses.append(course)
                        names.append(student)
                        dates.append(course_dicts[course][student])
        df["Course Name"] = courses
        df["Student"] = names
        df["Absent Date"] = dates
        with open(f"{self.start_date}-{self.end_date}.json", "w") as outfile:
            json.dump(course_dicts, outfile)
        end_time = datetime.now()
        print('Duration: {}'.format(end_time - start_time))
        

def main():
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = HelloFrame(None, title="Absentee")
    frm.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()