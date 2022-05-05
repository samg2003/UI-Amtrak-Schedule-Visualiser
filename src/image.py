'''
Generates images of map/routes
'''

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import random
from backend import data_, graph_, findPath
from threading import Thread
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = os.path.join(dir_path, "..", "static")

class MyImage:
  
  def __init__(self, path):
    self.worldmap = Image.open("static/worldmap.jpg").convert('RGB')
    self.im = Image.open(path).convert('RGB')
    self.draw = ImageDraw.Draw(self.im)
    self.pixels = self.im.load()
    self.path = path
    self.width = self.im.width
    self.height = self.im.height
    self.path_width = 11
    self.done = 0

  def closest_stn_to_pixel(self, x, y):
    '''
    input: pixel loc on our map
    output: [Station code string] returns closest stn code to the given pixel
    '''

    xs = []
    ys = []
    code = []

    #finding the distance of all stations and return whichever is closest
    for i, j, k in zip(data_["Latitude"].to_list(), data_["Longitude"].to_list(), data_["code"].to_list()):
      x_, y_ = self.convert_cord_to_pix((i,j))
      xs.append(x_)
      ys.append(y_)
      code.append(k)
    xs = np.array(xs)
    ys = np.array(ys)
    x_delta = (xs - x)**2
    y_delta = (ys - y)**2
    delta = np.sqrt(x_delta + y_delta)
    idx = np.argmin(delta)

    return code[idx]
  
  def plot_given_stations(self, stations, color = "red", radius = 9, verbose = False):
    '''
    input: 
       param stations: list of station codes
       param color:  color to draw of stations
       param radius: radius of the stations to draw
       param verbose: bool, if true prints out what code is doing
    output:
       Plots given amtrak stations on the map.
    '''
    
    smaller_radius = radius - 4
    normal_radius = radius
    count = 0
    for k in stations:
      i = data_[data_["code"] == k]["Latitude"].to_numpy()[0]
      j = data_[data_["code"] == k]["Longitude"].to_numpy()[0]
      count += 1
      if graph_[k].is_closely_packed():
        radius = smaller_radius
      else:
        radius = normal_radius
      if verbose and (count % 125 == 0): print(count, "stations plotted")
      x, y = self.convert_cord_to_pix((i,j))
      self.draw_circle((x, y), color = color, radius = radius, text = k)

  def plot_stations(self, color = "red", radius = 9, verbose = False):
    '''
    input: color of station points, radius of those points, verbose
    Plots all amtrak stations
    '''
    smaller_radius = radius - 4
    normal_radius = radius
    count = 0
    for i, j, k in zip(data_["Latitude"].to_list(), data_["Longitude"].to_list(), data_["code"].to_list()):
      count += 1
      if graph_[k].is_closely_packed():
        radius = smaller_radius
      else:
        radius = normal_radius
      if verbose and (count % 125 == 0): print(count, "stations plotted")
      x, y = self.convert_cord_to_pix((i,j))
      self.draw_circle((x, y), color = color, radius = radius, text = k)
  
  def plot_given_paths(self, stations, color = "white", width = 8, verbose = False):
    '''
    input: list of route stations, color of station paths, width of those paths, verbose
    Plots paths between given amtrak stations
    '''

    smaller_width = int(width / 2) 
    normal_width = int(width)
    count = 0
    for i in stations:
      i = graph_[i]
      count += 1 
      
      #finding cordinate of station
      if verbose and (count % 125 == 0): print(count, "paths printed")
      x, y = data_[data_["code"] == i.id]["Latitude"].to_list()[0], data_[data_["code"] == i.id]["Longitude"].to_list()[0]
      x, y = self.convert_cord_to_pix((x,y))

      #checking if stations are closely packed, if yes then width of lines would be small
      if i.is_closely_packed():
        width = smaller_width
      else:
        width = normal_width
  
      #plot connections
      for j in i.get_connections():
        xn, yn = data_[data_["code"] == j]["Latitude"].to_list()[0], data_[data_["code"] == j]["Longitude"].to_list()[0]
        xn, yn = self.convert_cord_to_pix((xn,yn))
        self.draw_line((x, y), (xn, yn), color = color, w = width)

  def plot_paths(self, color = "white", width = 8, verbose = False):
    '''
    input: color of station paths, width of those paths, verbose
    Plots all routes
    '''

    smaller_width = int(width / 2) 
    normal_width = int(width)
    count = 0
    for i in graph_.get_stations():
      count += 1 
      
      #finding cordinate of station
      if verbose and (count % 125 == 0): print(count, "paths printed")
      x, y = data_[data_["code"] == i.id]["Latitude"].to_list()[0], data_[data_["code"] == i.id]["Longitude"].to_list()[0]
      x, y = self.convert_cord_to_pix((x,y))

      #checking if stations are closely packed, if yes then width of lines would be small
      if i.is_closely_packed():
        width = smaller_width
      else:
        width = normal_width
  
      #plot connections
      for j in i.get_connections():
        xn, yn = data_[data_["code"] == j]["Latitude"].to_list()[0], data_[data_["code"] == j]["Longitude"].to_list()[0]
        xn, yn = self.convert_cord_to_pix((xn,yn))
        self.draw_line((x, y), (xn, yn), color = color, w = width)
  
  def convert_cord_to_pix(self, cords):
    '''
    input: tuple of cordinates of any location
    output: tuple of pixel location on the umage
    Using world map to calculate cordinates and translating and scaling those to 
    US map.
    '''  
    #calculating pixels values (x and y) from cordinates
    image_size_factor = 4
    x = (cords[1] + 180) * (self.worldmap.width / 360)
    latRad = cords[0]  * np.pi / 180
    mercN = np.log(np.tan((np.pi / 4) + (latRad / 2)))
    y = (self.worldmap.height / 2) - (self.worldmap.width * mercN / (2 * np.pi))
    
    #translating those pixels from world map to us map
    x_corrected, y_corrected = x + 8, y + 4
    x_offset = 1146
    y_offset = 1862
    x_new = image_size_factor*(x_corrected - x_offset)
    y_new = image_size_factor*(y_corrected - y_offset)
    return x_new, y_new 
 
  def get_width(self):
    return self.width
    
  def get_height(self):
    return self.height
    
  def draw_circle(self, coordinate, color ='green', radius=10, text = None):
    '''
    param coordiante is a tuple with the x and y coordinates (in the pixel) of the center of the circle
    param color is a string of the color to be drawn.  for example: 'green'
    param radius is the radius of the circle to draw
    '''

    #get center of circle
    centerx = coordinate[0]
    centery = coordinate[1]

    #get points to define the location of the circle
    x1 = centerx - radius
    y1 = centery - radius
    x2 = centerx + radius
    y2 = centery + radius

    #draw the circle
    self.draw.ellipse((x1, y1, x2, y2), fill = color, outline =color)

    #if text is not none add text in image
    if (text == None): return
    title_font = ImageFont.truetype('OpenSans-BoldItalic.ttf', 15)
    title_text = text
    offset = int(np.sqrt(2) * radius) + 3
    self.draw.text((coordinate[0] + offset, coordinate[1] - offset), title_text, (245, 233, 66), font = title_font)

  def draw_line(self, start, end, color='blue', w=5):
    '''
    start is a tuple with the x and y coordinates (in the pixel) of the start point on the line, likewise
    end is a tuple with the x and y coordinates (in the pixel) of the end point on the line
    color is a string which represents a color to use for the line fill in
    w is the width of the line to draw
    '''
    #get points to define the start and end of line
    x1 = start[0]
    y1 = start[1]
    x2 = end[0]
    y2 = end[1]
    self.draw.line((x1, y1, x2, y2), fill = color, width = w)
  
  def animate(self):
    #helper function for save image
    count = 0
    while True:
      count += 1
      if self.done:
        break
      print("\r", "Saving the output image. ", "|", "⡿" * count, " " * (15 - count), "|", end = "", sep="", flush=True)
      time.sleep(0.6)
  
  def save_img(self, path = "out.png", verbose = False):
    ''''
    This function saves the modified image file (after doing drawing items) to the out folder
    '''
    if verbose: 
      ch = Thread(target= self.animate, daemon=True)
      ch.start()
    self.im.save("out/" + path)
    if verbose: self.done = 1
    if verbose: print()
    if verbose: self.done = 0
  
  def add_path(self, path):
    '''
    input: list of connected station codes
    output: draws the path on image
    todo: to check whether two consecutive stations are connected 
    '''

    if (len(path) < 2):
      return -1

    #gives random but new color each time
    random_number = random.randint(0,16777215)
    hex_number = str(hex(random_number))
    color = hex_number[2:]
    while (len(color) < 6):
      color = "0" + color
    color = "#" + color

    #change all station nodes to respective color
    inv_color = self.find_inverted_color(color)
    self.change_station_color(path, inv_color)

    #draws lines between those stations.
    prev_stn = path[0]
    x_p, y_p = data_[data_["code"] == prev_stn]["Latitude"].to_list()[0], data_[data_["code"] == prev_stn]["Longitude"].to_list()[0]
    x_p, y_p = self.convert_cord_to_pix((x_p, y_p))
    for i in range(1, len(path)):
      stn = path[i]
      width = 9
      if graph_[stn].is_closely_packed():
        width = 4
      x, y = data_[data_["code"] == stn]["Latitude"].to_list()[0], data_[data_["code"] == stn]["Longitude"].to_list()[0]
      x, y = self.convert_cord_to_pix((x, y))
      self.draw_line((x_p, y_p), (x,  y), color=color, w= width)
      x_p, y_p = x, y
      prev_stn = stn

  def change_station_color(self, path, color):
    '''
    This function takes the path of all of the stations and it changes each of the stations color to the specified color
    so that it is easier to view on the map
    '''
    smaller_radius = 6
    normal_radius = 9
    for i in range(len(path)):
      if graph_[path[i]].is_closely_packed():
        radius = smaller_radius
      else:
        radius = normal_radius
      x_center, y_center = data_[data_["code"] == path[i]]["Latitude"].to_list()[0], data_[data_["code"] == path[i]]["Longitude"].to_list()[0]
      coords = self.convert_cord_to_pix((x_center,y_center))
      self.draw_circle(coords, color=color, radius = radius)

  def find_inverted_color(self, color):
    '''
    This function takes in the string representing the hexadecimal value of a color and returns its inverted color as a hexadecimal string
    '''

    hex1 = int(color[1:],16)
    hex_max = int("ffffff",16)
    inverted = hex_max-hex1
    str_inverted = str(hex(inverted))[2:]
    while (len(str_inverted) < 6):
      str_inverted = "0" + str_inverted
    return "#" + str_inverted



#img = MyImage("static/usmap.jpeg")
#img.plot_paths(verbose = True)
#img.plot_stations(verbose = True)
# path, found = findPath("RGH", "JAX")
# print(path)
# if (found):
#   img.add_path(path)
# else:
#   print("no path found")

#img.save_img("addedCHMtoCHIpath.png", verbose=1)



