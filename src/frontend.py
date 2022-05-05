'''
Frontend would be responsible for
- reading user input
- communicating with backend and image
- displaying results as an annotated image
'''


from cmath import nan
from geopy.geocoders import Nominatim

import numpy as np

import backend
import difflib
import re
from util import abbrev_to_us_state, us_state_to_abbrev, Assert, common_words
import util
import pgeocode
import math
import matplotlib.pyplot as plt
import time

#gets detail about us zipcodes
nomi = pgeocode.Nominatim('us')
#getting distance between stations
dist = pgeocode.GeoDistance('us')
#find geolocator
geolocator = Nominatim(user_agent="geoapiExercises")

data_ = backend.data_
graph_ = backend.graph_

WIDTH = 20
HEIGHT = 20

def FindStation(data, nearby = True, thread_ = []):
    '''
    input:  [string] User enter string for station, nearby = False would give precise location
    Outputs: [string] station code, (None if not found any)
    takes user entered data and with help of FindStationCommon(data) and 
    FindStationInter(data) finds the closest code
    '''

    code = None
    if (len(data.split()) > 4 and code == None):
        code = FindStationBasic(data)
        if code != None:
            return code
    if (code == None):
        code = FindStationCommon(data)
    if (code == None):
        code = FindStationInter(data)
    if (code == None):
        code = FindStationBasic(data)
    if (nearby and code == None): code = FindStationBasic(data, 400)

    thread_.append(code)
    return code

def FindStationBasic(data, dist = 10):
    '''
    input: String
    output: Code
    It takes data from user for stations and maps to station code
    It handles very simple ones using API
    '''

    cords = geolocator.geocode(data + ", United States of America")
    if (cords == None):
        return None
    cords = cords[-1]
    lats = list(data_["Latitude"])
    longs = list(data_["Longitude"])
    cords_ = []
    for lat, long in zip(lats, longs):
        cords_.append((lat, long))
    optimal_cord = 0
    max = dist
    for cord in cords_:
        distance = backend.Distance(cord, cords)
        if distance < max:
            optimal_cord = cord[0]
            max = distance
    if optimal_cord != 0:
        return list(data_[data_["Latitude"] == optimal_cord]["code"])[0]   
    return None

def CheckFindStation(verbose = True):
    '''
    It runs findstation on various inputs to see whether it gives right
    output.
    '''

    t = time.time()
    Assert(FindStation("1 C&O Plaza on Railroad Avenue"), "ALD")
    Assert(FindStation("Rensselaer, NX"), "ALB")
    if verbose:print("Rensselaer, NX -> ALB")
    Assert(FindStation("Ransseller, NY"),"ALB")
    if verbose: print("Ransseller, NY -> ALB")
    Assert(FindStation("61820") , "CHM")
    Assert(FindStation("525 Water st CT") , "BRP")
    if verbose:print("525 Water st CT -> BRP")
    Assert(FindStation("East Harrison st marryland") , "CUM")
    Assert(FindStation("61800") , "CHM") #chm = champaign
    if verbose:print("61800 -> CHM")
    Assert(FindStation("Um please anywhere near 61800 :(") , "CHM")
    if verbose:print("Um please anywhere near 61800 :( -> CHM")
    Assert(FindStation("somewhere in Ilinos, maybe matoon?") , "MAT")
    if verbose:print("somewhere in Ilinos, maybe matoon? -> MAT")
    Assert(FindStation("Chigaco in illinois") , "CHI")
    if verbose:print("Chigaco in illinois -> CHI")
    Assert(FindStation("somewhere near 61800 starting with champ") , "CHM")
    if verbose:print("somewhere near 61800 starting with champ -> CHM")
    Assert(FindStation("East Harrison, marryland") , "CUM")
    Assert(FindStation("somewhere in miami amtrak station"), "MIA")
    Assert(FindStation("St paul MN") , "MSP")
    Assert(FindStation("St paul") , "MSP")
    Assert(FindStation("Saint paul") , "MSP")
    Assert(FindStation("chmpgn illinis") , "CHM")
    Assert(FindStation("evanston"), "GLN")
    Assert(FindStation("Inver Grove Heights"), "MSP")
    Assert(FindStation("This is some random text lol"), None)
    Assert(FindStation("Is it actually random"), None)
    Assert(FindStation("I guess so oof"), None)
    Assert(FindStation("whaaaa"), None)
    Assert(FindStation("ILL INI ooh close one"), None)
    Assert(FindStation("smh, how is this even working at this point"), None)
    Assert(FindStation("Illn"), None)
    Assert(FindStation("Idk what to do"), None)
    Assert(FindStation("bruh"), None)
    Assert(FindStation("199 S E avenue"), "KKI")
    Assert(FindStation("400 1st avenue"), "MOT")
    Assert(FindStation("Amtrak Station Miami"), "MIA")
    Assert(FindStation("somewhere in Illinoys, let's say kankee"), "KKI")
    Assert(FindStation("marshal maybe in souther parts of taxus"), "MHL")
    Assert(FindStation("What about ostin of texas"), "AUS")
    Assert(FindStation("somewhere near 68900"), "HAS") #has has 68901 other answers possible
    Assert(FindStation("Geraldine"), "ATN", "HAV")  #assumes geraldine Alabama, but can be Geraldine Montana
    Assert(FindStation("Geraldine", nearby = 0), None)
    Assert(FindStation("Wisconsin Madison", nearby = 0), None)
    Assert(FindStation("Wisconsin MAdison"), "CBS", "POG")
    Assert(FindStation("cBS"), "CBS")
    Assert(FindStation("sckneketty new york"), "SDY")
    print(util.count, "assertions passed")
    print(round(util.avgtime, 4), "secs  per assertion")
    print(round(time.time() - t, 4), "secs", "for all assertions: ")
    #depending on speed of connection less than a second querries

def FindStationCommon(data, p = 0.8):
    '''
    input:  [string] User enter string for station
    - finds the station
        - if (data == zipcode), mark that station
        - if (data == one of the station code), mark that station
        - else, mark the one station closest in full addresses
    returns the valid station code associated with the user enter data
    this function checks for most of the common user entered data
    '''
    valid_zipcode, zipcode = CheckZipCode(data)
    valid_code, station_code = CheckStationCode(data.upper())
    if (valid_zipcode):
        # since the data entered is a valid zipcode of a train station, we need to mark that train station on the map
        # Also, return the station code that is associated with this zipcode for use later
        code = list((data_[data_["zipcode"] == zipcode])['code'])[0]
        return code
    elif (valid_code):
        # since the data entered is a valid code of a train station, we need to mark that train station on the map
        # Also, return the station code for use later
        return station_code
    else:
        # This is the general case so we have to check if the user inputted data matches any of the address parts at all and return the closest match
        # if no match, return None
        Full_Addresses, Addresses1, Addresses2 = GetAddresses()
        matches = difflib.get_close_matches(data, Full_Addresses, cutoff = p)
        matches1 = difflib.get_close_matches(data, Addresses1, cutoff = p)
        matches2 = difflib.get_close_matches(data, Addresses2, cutoff=p)
        # now that the close matches are filled in, return the closest one (if one exists)
        if (len(matches) != 0):
            code = list(data_[data_["Full_Address"] == matches[0]]["code"])[0]
            return code
        elif (len(matches1) != 0):
            code = list(data_[data_["address1"] == matches1[0]]["code"])[0]
            return code
        elif (len(matches2) != 0):
            code = list(data_[data_["address2"] == matches2[0]]["code"])[0]
            return code
        else:
            return None


def FindStationInter(data):
    '''
    input:  [string] User enter string for station
    - finds the station
        - if FindStationCommon returned none
        - if (data == City, State), mark that station
    returns the valid station code associated with the user enter data
    this function checks for some of less likely inputs
    '''

    # closer_data is data frame of interest
    global data_

    #closer_data will be limting data_ to potential matches based on more info
    closer_data = data_.copy()

    data = data.strip()
    data = re.split(", |,| ", data)
    
    # removing empty string
    data = [s for s in data if s != ""]
    states = list(us_state_to_abbrev.keys())

    # how strict similarity has to be
    prob = 0.8

    # replaced explicit state names to their respective code
    for idx, i in enumerate(data):
        closest_state = difflib.get_close_matches(i, states, cutoff=prob)
        if len(closest_state) != 0:
            closest_state = us_state_to_abbrev[closest_state[0]]
            data[idx] = closest_state
            closer_data = closer_data[closer_data["state"] == closest_state]
            prob = 0.65
            break
        #check if two words combined. States like New York.
        if (idx != len(data) - 1):
            closest_state = difflib.get_close_matches((i + " " + data[idx+1]).capitalize(), states, cutoff=0.8)
            if len(closest_state) == 0:continue
            if len(closest_state[0].split()) == 1:continue
            closest_state = us_state_to_abbrev[closest_state[0]]
            data[idx] = closest_state
            closer_data = closer_data[closer_data["state"] == closest_state]
            prob = 0.45
            break

    # if there is state name in query: localise those
    for i in data:
        if i in list(us_state_to_abbrev.values()):
            if (prob > 0.65):
                prob = 0.65
            closer_data = closer_data[closer_data["state"] == i]
            break

    # finding cities in dataframe if there is any in user input
    cities = list(closer_data["city"])
    for idx, j in enumerate(data):
        if j.lower() in common_words:
            continue
        closest_city = difflib.get_close_matches(j, cities, cutoff=prob)
        if (idx != len(data) - 1 and len(closest_city) == 0):
            closest_city = difflib.get_close_matches(j + " " + data[idx+1], cities, cutoff=0.63)
        if (len(closest_city) != 0):
            closest_city = closest_city[0]
            if len(closest_city.split()) > 1:
                break
            closer_data = closer_data[closer_data["city"] == closest_city]
            break

    # if our dataframe of interest has atleast one row return it's code
    possiblities = list(closer_data["code"])
    if len(possiblities) < 5 and len(possiblities) > 0:
        return possiblities[0]
    
    #if code is not found, then check normal cases again. with new data
    s = ""
    for i in data: 
        s += i + " "
    stored_data = data_.copy()
    data_ = closer_data
    code = FindStationCommon(s, 0.6)
    data_ = stored_data
    if (code != None):
        return code

    #get all zipcodes of amtrak stations
    zips = []
    for i in GetZipcodes():
        try:
            zips.append(int(i))
        except:
            continue
    zips = np.array(zips)
    

    #finding if there is any potential zip code in user data
    main_zip = -1
    for potential in data:
        if len(potential) == 5:
            try:
                int(potential)
            except:
                continue
            main_zip = potential

    #if there is zip
    if (main_zip != -1):

        #checking if it's under certain distance
        within_proximity = abs(zips - int(main_zip)) < 1000
        zips = zips[within_proximity]
        distances = []
        station_zip = []

        #looping over each potential zipcode and checking it's distance from zipcode in user
        for zip_ in zips:
            temp_dist = dist.query_postal_code(str(zip_), main_zip) 
            if not (math.isnan(temp_dist)) and temp_dist < 200:
                distances.append(temp_dist)
                station_zip.append(str(zip_))

        #if there are few zip codes, withing 200 kms of user entered zip code,
        if (len(distances) != 0):
            idx = np.argmin(distances)
            return list(data_[data_["zipcode"] == station_zip[idx]]["code"])[0]

        #else just find whichever is closest abs distance from zipcode
        else:
            idx = np.argmin(np.abs(zips - int(main_zip)))
            return list(data_[data_["zipcode"] == str(zips[idx])]["code"])[0]
            
    return None



def GetZipcodes():
    '''
    returns all of the zipcodes of train stations as a list of strings
    '''
    return list(data_["zipcode"])


def GetStationCodes():
    '''
    returns all of the station codes of train stations as a list
    '''
    return list(data_["code"])


def GetAddresses():
    '''
    returns a list of three lists: the full addresses, part 1 of the addresses, and part 2 of the addresses respectively
    '''
    return (list(data_["Full_Address"]), list(data_["address1"]), list(data_[~data_["address2"].isna()]["address2"]))


def CheckZipCode(data):
    '''
    this function checks if the data is in the format of a zipcode (a 5 digit number)
    input: data that is entered by the user
    returns two things.  First, a boolean value of if the zipcode is valid or not (true if it is, false if it is not)
    Second, the actual zipcode assuming that it is valid
    '''
    try:
        test_zip = int(data)
    except:
        test_zip = -1
    all_zipcodes = GetZipcodes()
    if str(test_zip) in all_zipcodes:
        return True, str(test_zip)
    else:
        return False, "00000"


def CheckStationCode(data):
    '''
    this function checks if the data is in the format of a station code (a valid 3 character string)
    input: data that is entered by the user
    returns two things.  First, a boolean value of if the station code is valid or not (true if it is, false if it is not)
    Second, the actual station code assuming that it is valid
    '''
    code = data
    all_station_codes = GetStationCodes()
    if code in all_station_codes:
        return True, code
    else:
        return False, "000"

#In this case: it is returning the Boston Union Station, but we can later add functionality to give the user the options of all the matches of union stations
#print(FindStation(""))



if __name__ == '__main__':
    # DisplayPath(graph_.stations.values())
    for i in range(10):
        print(FindStation(input("Enter the station: ")))
    # CheckFindStation(True)
    pass
