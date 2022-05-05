'''
frontend_utils.py provides utils on visualization
'''
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QLineEdit, QGridLayout, \
    QScrollArea, QHBoxLayout, QSizePolicy
from backend import *
from frontend import *
from image import *
from PIL.ImageQt import ImageQt
from threading import Thread
import time
import sys

class GUIFrontend(QWidget):
    def __init__(self, window_name, window_width, window_height, app):
        '''
        input:  string  windowName
                int     windowWidth
                int     windowHeight
        - Creates a PyQT window for visualization
        '''
        super().__init__()
        
        self.app = app
        self.log = []  #log of all user input
        self.action = []    #log of all actions user did

        #storing image for front end
        self.my_image = MyImage("static/usmap.jpeg")
        self.my_image.plot_paths(verbose = False)
        self.my_image.plot_stations(verbose = False)

        self.qtApp = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle(window_name)
        self.window.setMinimumHeight(window_height)
        self.window.setMinimumWidth(window_width)
        
        self.windowLayout = QVBoxLayout()
        self.innerL = QGridLayout()

        self.image = QLabel()
        self.image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image.setScaledContents(True)
        self.time_click = 0     #helper variable to check if user made single or double click
        self.double_click_loc = -1  #helper variable to check what was the purpose of double click
        self.image.mousePressEvent = self.onClick
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidget(self.image)
        self.add_component(self.image_scroll_area)
        self.status = QLabel("")
        self.status.setAlignment(QtCore.Qt.AlignCenter)
        self.add_component(self.status)

        #add zoom in / out button
        self.scale_factor = 1
        self.zoom_buttons_row = QHBoxLayout()
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_buttons_row.addWidget(self.zoom_in_btn)
        self.zoom_buttons_row.addWidget(self.zoom_out_btn)
        zoom_buttons_widget = QWidget()
        zoom_buttons_widget.setLayout(self.zoom_buttons_row)
        self.add_component(zoom_buttons_widget)

        #adding picture for first time
        self.start = 0
        self.putImage()

        #added inner layout (all the buttons)
        self.save_img = QPushButton("Save Image")
        self.save_img.clicked.connect(lambda: self.saveImg())
        self.innerL.addWidget(self.save_img, 0, 3, 1, 1)
        self.clear_img = QPushButton("Clear Image")
        self.clear_img.clicked.connect(lambda: self.clearImg())
        self.innerL.addWidget(self.clear_img, 0, 4, 1, 1)
        self.undo = QPushButton("Undo")
        self.undo.clicked.connect(lambda: self.Undo())
        self.innerL.addWidget(self.undo, 0, 0, 1, 1) 
        self.find_station = QPushButton("Find station")
        self.innerL.addWidget(self.find_station, 1, 0) 

        #added a textboxes for user to enter stations
        self.stn1 = QLineEdit("Station1")
        self.stn2 = QLineEdit("Station2")
        self.innerL.addWidget(self.stn1, 1, 3)
        self.innerL.addWidget(self.stn2, 1, 4)
        self.stn1.returnPressed.connect(lambda: self.StnLocate(2))
        self.stn2.returnPressed.connect(lambda: self.StnLocate(3))
        self.find_station.clicked.connect(lambda: self.StnLocate(6))
        
        #added more buttons for user
        self.add_path = QPushButton("Add Path")
        self.innerL.addWidget(self.add_path,  2, 0, 1, 4)
        self.add_path.clicked.connect(lambda: self.addPath())
        self.remove_path = QPushButton("Remove Path")
        self.innerL.addWidget(self.remove_path,  2, 4, 1, 4)
        self.remove_path.clicked.connect(lambda: self.removePath())

        self.windowLayout.addLayout(self.innerL)
        self.setLayout(self.windowLayout)

    def event(self, event):
        '''
        Overrides event handlers for shift + - keys.
        '''

        if (event.type() == QtCore.QEvent.KeyPress):
            if (event.key() == 43):
                self.zoom_in()
            if (event.key() == 95):
                self.zoom_out()

        return super().event(event)

    def set_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.image.setPixmap(pixmap)

    def add_component(self, component):
        self.windowLayout.addWidget(component)

    def display(self):
        '''
        Shows the window
        '''
        self.window.show()
        self.qtApp.exec()
    
    def putImage(self):
        '''
        Put Images in the visualisation of the the box.
        '''

        self.qim =  ImageQt(self.my_image.im)
        self.pixmap = QPixmap.fromImage(self.qim)
        # self.pixmap = self.pixmap.scaledToHeight((512 + 256 + 128 + 728))
        self.image.setPixmap(self.pixmap)
        self.image.setAlignment(QtCore.Qt.AlignCenter)

        #if program started
        if (self.start == 0):
            for i in range(7):
                self.zoom_out()
            self.start = 1

    def onClick(self, event):
        '''
        This function runs when user click on the map.
        It displays the closest station to the point where the user clicked
        '''

        #if it's double click
        prev = ""
        if time.time() - self.time_click < 0.5:
            prev = self.status.text()[-3:]

        x = event.pos().x()
        y = event.pos().y()

        img_x = x / self.scale_factor   
        img_y = y / self.scale_factor   

        #use this img_x and img_y to find closest point.
        stn = self.my_image.closest_stn_to_pixel(img_x, img_y)
        self.status.setText("Closest station to this location is " + stn)
        if (stn == prev):
            stn1 = self.stn1.text()
            stn2 = self.stn2.text()
            if ((len(stn2) != 3 and len(stn1) == 3) or (len(stn1) == 3 and len(stn2) == 3 and self.double_click_loc == 1)):
                self.stn2.setText(stn)
                self.addPath()
                self.double_click_loc = 0
            elif (len(stn1) != 3 or (len(stn1) == 3 and len(stn2) == 3 and self.double_click_loc != 1)):
                self.stn1.setText(stn)
                self.double_click_loc = 1
        
        #updated the time of the last click
        self.time_click = time.time()

    def removePath(self):
        '''
        It removes the path in the input boxes. 
        It does so with help of helper functions in Image classs
        '''

        self.double_click_loc = -1
        stn1 = self.stn1.text()
        stn2 = self.stn2.text()

        #checks if user has found the stations
        if type(stn1) != str or type(stn2) != str:
            self.status.setText("Find the stations first.")
            return
        if not stn1.isupper() or not stn2.isupper() or not stn1.isalpha() or not stn2.isalpha():
            self.status.setText("Find the stations first.")
            return

        #removes the path if valid stations are there
        path, found = findPath(stn1, stn2)
        if (found):
            if (stn1, stn2) not in self.log:
                self.status.setText("Path between " + stn1 + " and " + stn2 + " is not added yet.")
                return
            else:
                still_exist = 0
                for i in range(len(self.log)):
                    if self.log[i] == (stn1, stn2):
                        still_exist += self.action[i]
                if still_exist == 0:
                    self.status.setText("Path between " + stn1 + " and " + stn2 + " is already removed.")
                    return
                self.log.append((stn1, stn2))
                self.action.append(-1)      
            self.my_image.plot_given_paths(path)
            self.my_image.plot_given_stations(path)
            self.putImage()
            self.status.setText("Removed path between " + stn1 + " and " + stn2)
        else:
            self.status.setText("Path not found.")
            return

    def addPath(self):
        '''
        This function adds the path as specified in the input boxes
        addPath calls the helper functions of the image class to display the path on the map
        '''
        self.double_click_loc = -1
        stn1 = self.stn1.text()
        stn2 = self.stn2.text()
        if type(stn1) != str or type(stn2) != str:
            self.status.setText("Find the stations first.")
            return
        
        if not stn1.isupper() or not stn2.isupper() or not stn1.isalpha() or not stn2.isalpha():
            self.status.setText("Find the stations first.")
            return
        path, found = findPath(stn1, stn2)
        if (found):
            if len(self.log) == 0:
                self.log.append((stn1, stn2))
                self.action.append(1)
            elif self.log[-1] == (stn1, stn2):
                pass
            else:
                self.log.append((stn1, stn2))
                self.action.append(1)
            self.my_image.add_path(path)
            self.putImage()
            self.status.setText("Added path between " + stn1 + " and " + stn2)
        else:
            self.status.setText("Path not found.")
            return

    def StnLocate(self, stn_num):
        '''
        This function is a helper function to know where to put a station on the event of a double click
        input:
            param stn_num is the number that the station corresponds to (station1 or station 2 or both - when remainder is taken)
        output:
            this function replaces the user entered text to the correct station code 
        '''
        if (stn_num % 2 == 0):
            stn1 = self.stn1.text()
            self.stn1.setText(FindStation(stn1))
        if (stn_num % 3 == 0):
            stn2 = self.stn2.text()
            self.stn2.setText(FindStation(stn2))
    
    def clearImg(self):
        '''
        Resets the image as another thread so that the user can still access other functions while this happens
        '''
        dh = Thread(target= self.clearImgHelper)
        dh.start()

    def clearImgHelper(self):
        '''
        Helper for clearImg, draws new image and replaces it with the current image. 
        '''

        self.my_image = MyImage("static/usmap.jpeg")
        self.my_image.plot_paths(verbose = False)
        self.my_image.plot_stations(verbose = False)
        self.putImage()
        self.status.setText("Cleared the Image.")
        self.log = []
        self.action = []

    def animate(self):
        '''
        It's the progress bar to give rough estimate of how much time the save image will take
        '''
        count = 0
        for i in range(15):
            count += 1
            string = ("Saving the output image. " + "|" + ("⡿" * count) + (" " * (15 * 3 - 3 * count)) + "|")
            self.status.setText(string)
            time.sleep(0.6)
        self.status.setText("Saved the image at static/out.png")

    def saveImg(self):
        '''
        Saves the image in another thread so that the user can still access other functions while this happens
        '''

        dh = Thread(target= self.animate)
        dh.start()
        temp = lambda: self.my_image.save_img("out.png")
        ch = Thread(target= temp)
        ch.start()

    def Undo(self):
        '''
        This function gets rid of the last action in the log by calling the inverse of it to make sure that it is reset to before
        Undo updates the log so it can be pressed repeatedly
        '''
        if (len(self.log) == 0):
            self.status.setText("Nothing to undo.")
            return
        stns = self.log[-1]
        self.log.pop()
        action = self.action[-1]
        self.action.pop()

        stn1 = stns[0]
        stn2 = stns[1]
        if (stn1 == stn2):
            if (action == 1):
                self.status.setText("Removed path between " + stn1 + " and " + stn2)
            if (action == -1):
                self.status.setText("Added path between " + stn1 + " and " + stn2)
            return
        path, found = findPath(stn1, stn2)
        if (found):
            if (action == 1):
                self.my_image.plot_given_paths(path)
                self.my_image.plot_given_stations(path)
                self.putImage()
                self.status.setText("Removed path between " + stn1 + " and " + stn2)
            else:
                self.my_image.add_path(path)
                self.putImage()
                self.status.setText("Added path between " + stn1 + " and " + stn2)
        else:
            self.status.setText("Path not found.")
            return

    def zoom_in(self):
        self.scale(1.25)
        pass

    def zoom_out(self):
        self.scale(0.8)
        pass

    def scale(self, factor):
        self.scale_factor *= factor
        self.image.resize(self.scale_factor * self.image.pixmap().size())
        self.adjust_scrollbar(self.image_scroll_area.horizontalScrollBar(), factor)
        self.adjust_scrollbar(self.image_scroll_area.verticalScrollBar(), factor)

    def adjust_scrollbar(self, scrollbar, factor):
        scrollbar.setValue(int(factor * scrollbar.value() + ((factor - 1) * scrollbar.pageStep() / 2)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GUIFrontend("Amtrak Planner", 2000, 2000, app)
    window.show()
    os._exit(app.exec_())

