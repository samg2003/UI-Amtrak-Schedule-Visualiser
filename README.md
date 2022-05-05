# Summary of Presentation Introduction

Our project is a tool to plan amtrak routes with a visual interface. It uses Dijkstra to find the shortest path, and uses Threading to give real time updates on the map while not halting access to other parts of program. 

# Technical Architecture

We coded this entire project in Python, with both backend and frontend component. We used PyQt5 for frontend, and several common python libraries for Image manipulation and API calls.

![Screenshot 2022-05-01 at 3 17 02 PM](https://user-images.githubusercontent.com/81476140/166163069-1b7b893d-b1cf-4f46-93c9-bb5984f23bbe.jpeg)

Here Main uses PyQt5, frontend uses Geopy, backend uses Numpy and Pandas, and Image uses Pillow (PIL).


# Installation and Running Instructions

To run this program, you first need to pip3 install all of the libraries listed in the requirements.txt.
This command will do that for you (from the root directory): 
   
   pip install -r requirements.txt

To run all you have to do is run the following the command (from the root directory): 
  
  python src/main.py
  

# Collaboration

Sambhav and Joshua worked on the Diksjtra algorithm and parts of frontend components. Steven worked majorly in rest of the visual interface. Sairam and Leo on other hand worked on test cases and Data manipulation, cleaning, entry, and Graph structure.

Group members:  Sambhav Gupta, Joshua Brown, Leo Luo, Sairam Penumarthy, Steven Gao
