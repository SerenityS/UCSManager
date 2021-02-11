import json
import os
import re
import requests
import sys

from bs4 import BeautifulSoup

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5 import uic

from qt_material import apply_stylesheet


def initLoginSession():
    # Make New Login Session Globally
    global sess
    sess = requests.Session()
    sess.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Whale/2.8.107.16 Safari/537.36"
    }


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


form = resource_path('UCSManager.ui')
form_class = uic.loadUiType(form)[0]


class MyWindow(QMainWindow, form_class):
    ucs_api_url = "http://www.piugame.com/piu.ucs/ucs.share/ucs.share.ajax.php"

    ucs_no = 0
    final_ucs_list_arr = []
    total_ucs_no_arr = []

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(501, 1010)
        self.setWindowIcon(QIcon(resource_path('icon.png')))
        initLoginSession()

        self.idBox.returnPressed.connect(self.focusEvent)
        self.pwBox.returnPressed.connect(self.loginButton.click)
        self.ucsListBox.returnPressed.connect(self.ucsListAddButton.click)

        self.loginButton.clicked.connect(self.Login)
        self.ucsListAddButton.clicked.connect(self.addUCSFromList)
        self.searchButton.clicked.connect(self.searchUcsList)
        self.resultAddButton.clicked.connect(self.addUCSFromSearchBox)
        self.deleteButton.clicked.connect(self.deleteUCS)
        self.clearButton.clicked.connect(self.clearUCS)
        self.registerButton.clicked.connect(self.registerUCS)

        self.ucsListAddButton.setDisabled(True)
        self.searchButton.setDisabled(True)
        self.resultAddButton.setDisabled(True)
        self.deleteButton.setDisabled(True)
        self.clearButton.setDisabled(True)
        self.registerButton.setDisabled(True)

        self.idBox.setFocus()

    def focusEvent(self):
        if self.pwBox.text():
            self.loginButton.click()
        else:
            self.pwBox.setFocus()

    def addUCS(self, ucs_id):
        if ucs_id != '':
            ADD_REQ_DATA = {
                'ucs_id': ucs_id,
                'work_type': "AddtoUCSSLOT",
            }
            get_add = sess.get(self.ucs_api_url, params=ADD_REQ_DATA)
            rst = json.loads(get_add.text)
            rst = rst['unpack_data']['msg']
            if rst == "SOURCE ERROR":
                print(f"WRONG UCS No - {ucs_id}")
                self.logText.setText(f"WRONG UCS No - {ucs_id}")
                return -1
            elif "10" in rst:
                self.logText.setText("You already register 10 UCS.")
                return -1
            else:
                print(f"PIU UCS Result - {rst}")
                return ucs_id

    def addUCSFromList(self):
        success_ucs_id = ""

        ucs_id_list = self.ucsListBox.text()
        ucs_id_list = ucs_id_list.split(",")
        for ucs_id in ucs_id_list:
            if ucs_id != "":
                ucs_id = self.addUCS(ucs_id)
                if ucs_id != -1:
                    success_ucs_id += (ucs_id + ", ")
        self.getUCSList()
        self.logText.setText("Add UCS Successfully. Success UCS No - " + success_ucs_id[:-2])

    def addUCSFromSearchBox(self):
        idx = self.searchResultBox.currentIndex()
        ucs_id = self.final_ucs_list_arr[idx][0]
        success_ucs_id = (self.addUCS(ucs_id))
        if success_ucs_id != -1:
            self.getUCSList()
            self.logText.setText(f"Add UCS Successfully - {success_ucs_id}.")

    def clearUCS(self):
        for ucs_no in self.total_ucs_no_arr:
            DELETE_REQ_DATA = {
                'data_no': ucs_no,
                'work_type': "RemovetoUCSSLOT2",
            }
            get_delete = sess.get(self.ucs_api_url, params=DELETE_REQ_DATA)
            rst = json.loads(get_delete.text)['unpack_data']['msg']
            print(f"PIU UCS Result - {rst}")
            if "deleted" not in rst:
                self.logText.setText("Delete UCS Failed.")
        self.getUCSList()
        self.logText.setText("Clear All UCS Finished.")

    def deleteUCS(self):
        idx = self.deleteListBox.currentIndex()
        if idx >= 0:
            DELETE_REQ_DATA = {
                'data_no': self.total_ucs_no_arr[idx],
                'work_type': "RemovetoUCSSLOT2",
            }
            get_delete = sess.get(self.ucs_api_url, params=DELETE_REQ_DATA)
            rst = json.loads(get_delete.text)['unpack_data']['msg']
            print(f"PIU UCS Result - {rst}")
            if "deleted" in rst:
                self.logText.setText("Delete UCS Successfully.")
                self.getUCSList()
            else:
                self.logText.setText("Delete UCS Failed.")
        else:
            return

    def getUCSList(self):
        self.clearButton.setDisabled(True)
        self.deleteButton.setDisabled(True)
        self.registerButton.setDisabled(True)

        self.deleteListBox.clear()
        self.total_ucs_no_arr = []

        my_activity_page = sess.get("http://www.piugame.com/piu.ucs/ucs.my_ucs/ucs.my_upload.php")
        my_activity_parsed = BeautifulSoup(my_activity_page.text, "lxml")
        ucs_list_parsed = my_activity_parsed.find_all(class_="my_list")
        ucs_list_parsed = ucs_list_parsed[1].find_all("tr")

        try:
            if len(ucs_list_parsed) != 0:
                ucs_list = ["Not Registered" for x in range(10)]
                for i in range(len(ucs_list_parsed)):
                    title = ucs_list_parsed[i].find(class_="my_list_title")
                    stepmaker = ucs_list_parsed[i].find(class_="my_list_rating")
                    self.deleteListBox.addItem(f"{i + 1}. Title - {title.text} / StepMaker - {stepmaker.text}")
                    ucs_list[i] = f"Title - {title.text} / StepMaker - {stepmaker.text}"

                    ucs_no = ucs_list_parsed[i].find(class_="ucs_slot_delete")
                    self.total_ucs_no_arr.append(ucs_no['data-ucs_no'])
                    print(f"UCS {i + 1} - Title - {title.text} / StepMaker - {stepmaker.text}")

            self.clearButton.setEnabled(True)
            self.deleteButton.setEnabled(True)
            self.registerButton.setEnabled(True)
        except:
            print("No UCS Data.")
            pass

        self.songInfo1.setText(ucs_list[0])
        self.songInfo2.setText(ucs_list[1])
        self.songInfo3.setText(ucs_list[2])
        self.songInfo4.setText(ucs_list[3])
        self.songInfo5.setText(ucs_list[4])
        self.songInfo6.setText(ucs_list[5])
        self.songInfo7.setText(ucs_list[6])
        self.songInfo8.setText(ucs_list[7])
        self.songInfo9.setText(ucs_list[8])
        self.songInfo10.setText(ucs_list[9])

    def Login(self):
        piu_id = self.idBox.text()
        piu_pw = self.pwBox.text()

        # Login Data
        LOGIN_REQ_HEADERS = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "www.piugame.com",
            "Origin": "http://www.piugame.com",
            "Referer": "http://www.piugame.com/piu.xx/",
            "Upgrade-Insecure-Requests": "1"
        }
        LOGIN_POST_DATA = {
            'url': "http://www.piugame.com/piu.xx/",
            'mb_id': piu_id,
            'mb_password': piu_pw,
        }

        try_login = sess.post("http://www.piugame.com/bbs/piu.login_check.php",
                              data=LOGIN_POST_DATA, headers=LOGIN_REQ_HEADERS)
        if "Hello!" in try_login.text:
            print("Login Successfully.")
            piu_parsed = BeautifulSoup(try_login.text, "lxml")
            nick = piu_parsed.find(class_="outGameid").text.strip()
            self.loginStatus.setText(f"Login Status : {nick}")
            self.logText.setText(f"Successfully Login via {nick}.")

            self.ucsListAddButton.setEnabled(True)
            self.searchButton.setEnabled(True)
            self.deleteButton.setEnabled(True)
            self.clearButton.setEnabled(True)
            self.loginButton.setDisabled(True)

            self.getUCSList()
            self.ucsListBox.setFocus()
        else:
            print("Login Failed.")
            self.logText.setText("Login Failed. Check ID/PW.")

    def registerUCS(self):
        REG_REQ_DATA = {
            'work_type': "MakeUCSPack",
        }
        get_reg = sess.get(self.ucs_api_url, params=REG_REQ_DATA)
        rst = json.loads(get_reg.text)['unpack_data']['msg']
        print(f"PIU UCS Result - {rst}")
        if "complete" in rst:
            self.logText.setText("Build UCS Pack Successfully.")
        else:
            self.logText.setText("Build UCS Pack Failed.")

    def searchUcsList(self):
        self.searchResultBox.clear()
        self.resultAddButton.setDisabled(True)

        ucs_list_arr = []
        self.final_ucs_list_arr = []

        title = self.songTitleBox.text()
        artist = self.stepArtistBox.text()
        level = self.stepLevelBox.text()

        def searchUcsFromTitle(url):
            ucs = requests.get(url)
            ucs_parsed = BeautifulSoup(ucs.text, "lxml")
            total_page = ucs_parsed.find(class_="share_board_info_text")
            total_page = total_page.find("span")
            total_page = re.findall("\d+", total_page.text.strip())[0]
            total_page = int(total_page)

            if total_page % 15 == 0:
                total_page = total_page // 15
            else:
                total_page = total_page // 15 + 1

            for i in range(1, total_page + 1):
                ucs_page = requests.get(url + str(i))
                ucs_parsed = BeautifulSoup(ucs_page.text, "lxml")

                ucs_list_parsed = ucs_parsed.find("tbody")
                ucs_list_parsed = ucs_list_parsed.find_all("tr")

                for j in range(len(ucs_list_parsed)):
                    ucsno = ucs_list_parsed[j].find(class_="btnaddslot_ucs btnAddtoUCSSLOT")['data-ucs_id'].strip()
                    songtitle = ucs_list_parsed[j].find(class_="share_song_title").text.strip()
                    stepmaker = ucs_list_parsed[j].find(class_="share_stepmaker").text.strip()
                    ucslv = ucs_list_parsed[j].find(class_="share_level").find("span")['class']
                    if "single" in ucslv[0]:
                        ucslv = "S" + ucslv[1][4:]
                    else:
                        ucslv = "D" + ucslv[1][4:]
                    ucs_list_arr.append([ucsno, songtitle, stepmaker, ucslv])

                if i == total_page:
                    try:
                        next_search = ucs_parsed.find(class_="pg_page pg_end")
                        url = "http://www.piugame.com/bbs" + next_search['href'][1:-1]
                        searchUcsFromTitle(url)
                    except:
                        return

        if title != '':
            searchUcsFromTitle(f"http://www.piugame.com/bbs/board.php?bo_table=ucs&sfl=ucs_song_no&stx={title}&page=")
        else:
            self.logText.setText("Enter SongTitle.")
            return

        if len(ucs_list_arr) != 0:
            for arr in ucs_list_arr:
                if artist.lower() in arr[2].lower():
                    if level.lower() in arr[3].lower():
                        self.final_ucs_list_arr.append(arr)
                        self.searchResultBox.addItem(f"{arr[0]} - {arr[1]} {arr[3]} - {arr[2]}")
                        self.resultAddButton.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    apply_stylesheet(app, theme='dark_teal.xml')
    window.show()
    app.exec_()