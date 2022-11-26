from dotenv import load_dotenv
import os
from datetime import datetime
import wx
import wx.adv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from bs4 import BeautifulSoup

# getting credentials from environment variables
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")

class AppFrame(wx.Frame):
    """
    A Frame
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(AppFrame, self).__init__(*args, **kw)
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
    
    def tidy_split(self, df, column, sep='|', keep=False):
        """
        Split the values of a column and expand so the new DataFrame has one split
        value per row. Filters rows where the column is missing.

        Params
        ------
        df : pandas.DataFrame
            dataframe with the column to split and expand
        column : str
            the column to split and expand
        sep : str
            the string used to split the column's values
        keep : bool
            whether to retain the presplit value as it's own row

        Returns
        -------
        pandas.DataFrame
            Returns a dataframe with the same columns as `df`.
        """
        indexes = list()
        new_values = list()
        df = df.dropna(subset=[column])
        for i, presplit in enumerate(df[column].astype(str)):
            values = presplit.split(sep)
            if keep and len(values) > 1:
                indexes.append(i)
                new_values.append(presplit)
            for value in values:
                indexes.append(i)
                new_values.append(value)
        new_df = df.iloc[indexes, :].copy()
        new_df[column] = new_values
        return new_df

    def load_options(self, start_date, end_date):
        # initialize the Chrome driver
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--headless')
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
        driver.get("https://trivietedu.ileader.vn/Default.aspx?mod=hocvien!danhsach_nghihoc")
        # start date picker
        date_picker = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="tungay"]')))
        date_picker.clear()
        date_picker.send_keys(start_date.strftime("%d/%m/%Y"))
        # end date picker
        date_picker = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="denngay"]')))
        date_picker.clear()
        date_picker.send_keys(end_date.strftime("%d/%m/%Y"))
        button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="formsearch"]/button'))).click()
        html_table = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="dyntable"]/tbody/tr[1]')))
        time.sleep(20)
        soup = BeautifulSoup(driver.page_source, "lxml")
        table = [table for table in soup.find_all('table')][1]
        table_headings = table.find_all('th')
        table_rows = table.find_all('tr')
        res = []
        for tr in table_rows:
            td = tr.find_all('td')
            row = [tr.text.strip() for tr in td]
            if row:
                res.append(row)
        df = pd.DataFrame(res, columns=[th.text.strip() for th in table_headings])
        print(df.columns)
        df = df[['Ngày nghỉ', 'Lớp học', 'Họ Tên*']]
        df = self.tidy_split(df, 'Ngày nghỉ', sep=' ,')
        df = df.groupby(['Lớp học','Ngày nghỉ'])['Họ Tên*'].agg(','.join).reset_index()
        df.index +=1
        driver.get("https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc")
        course_select = Select(WebDriverWait(driver, 1.5).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="idlophoc"]'))))
        return driver, course_select, df
    
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
        driver, course_select, df = self.load_options(self.start_date, self.end_date)
        print(df)
        self.maxPercent = len(df)
        self.showProgress()
        lessons = []
        for index, row in df.iterrows():
            try:
                #print(course_select.all_selected_options[0].text)
                if course_select.all_selected_options[0].text != row['Lớp học']:
                    course_select.select_by_visible_text(row['Lớp học'])
                    time.sleep(1.5)
                    soup = BeautifulSoup(driver.page_source, "lxml")
                print(row['Lớp học'])
                print(row['Ngày nghỉ'])
                baihoc = [baihoc.next_sibling.text for baihoc in soup.find_all('td',string=row['Ngày nghỉ'])]
                if baihoc:
                    print(baihoc[0])
                    lessons.append(baihoc[0])
                    self.progress.Update(index)
                else:
                    lessons.append("")
                    self.progress.Update(index)
            except:
                print(f"can't select {row['Lớp học']}")
                lessons.append("")
                self.progress.Update(index)
                pass
        df['Lesson'] = lessons
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        with pd.ExcelWriter(f"Absentee-{self.start_date}-{self.end_date}.xlsx", engine='xlsxwriter') as writer:
            # Write each dataframe to a different worksheet.
            df.to_excel(writer, sheet_name='Sheet1')
            # Close the Pandas Excel writer and output the Excel file to the buffer
            writer.save()
        driver.quit()
        end_time = datetime.now()
        print('Duration: {}'.format(end_time - start_time))
        
def main():                  
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = AppFrame(None, title="Absentee")
    frm.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()