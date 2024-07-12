import math
import random 
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy 
import json 
from sklearn.metrics.pairwise import cosine_similarity
import sys

"""
Class for each individual hotels
"""
class Hotel:
	#Default to empty values so that a hotel can be loaded from a saved file
	def __init__(self, idnum=-1, coords=[0,0], stars=1, city=None, rooms={}, historical_data=pd.DataFrame()):
		#Coordinates of the hotel
		self.coords = coords
		#Hotel ID
		self.idnum = idnum
		#Historical Selling data for the hotel
		self.historical_data = historical_data
		#Ranking of the hotel
		self.stars = stars
		#Object containing all other hotels in the city
		self.city = city
		#Will be an dictionary ints [roomcapacity] total of room type
		self.rooms = rooms 
		#Total rooms available in the hotel
		self.vacancy = self.get_total_rooms()

	
		#Dictionary for default price per room size
		self.prices = {}

		#Prices for each date for each room size that change
		self.dynamicprices = {}

		#Price ceilings and floors so the dynamic pricing wont pass a certain threshold
		self.ceilings = {}
		self.floors = {}

		#Dictionary of booleans to track if the owner manually set the price for a certain date
		self.date_manually_set = {}

		#Initialize the prices, floors, and ceilings
		for i in range(1, 7):
			#Make default price 20 * stars * room capacity
			self.prices[i] = round(stars*random.uniform(18,22)*i, 2)

			#Made them high enough and low enough that the dynamic pricing wont often reach unless the ceilings and floors are changed
			self.ceilings[i] = self.prices[i]*5
			self.floors[i] = self.prices[i]/4

		#Holds the vacancy by each size room
		self.vacancy_by_size = {}
		for i in self.rooms:
			self.vacancy_by_size[i] = rooms[i]

		#Will hold the vacancy by size, by datee
		self.datevacancy = {}

		#Initialize datevacancy, date_manually_set and dynamic prices
		self.init_dates()


	#Adds a room to the hotel of with capacity of size
	def add_room(self, size):
		self.rooms[size] = self.rooms[size]+1
		self.vacancy += 1
		self.vacancy_by_size[size] += 1

	#Get the distance between two hotels
	def get_dist(self, other):
		return math.dist(self.coords, other.coords)

	#Check if two hotels are equal to each other
	def __eq__(self, other):
		return self.idnum == other.idnum

	#Get the price of a room at a size
	def get_price_of_room(self, size):
		return self.prices[size]
	#Get the vacancy
	def get_vacancy(self):
		return self.vacancy
	#Get the vacancy by size
	def get_vacancy_by_size(self, size):
		return self.vacancy_by_size
	#Get the total # of rooms
	def get_total_rooms(self):
		total = 0
		for i in self.rooms:
			
			total += self.rooms[i]
		return total

	#Init dictionaries with date keys, will only do a year ahead for reduced time to compute
	def init_dates(self):
		currentdate = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		for size in self.rooms:
			for i in range(1,365):
				self.datevacancy[currentdate + timedelta(days=i)] =  copy.deepcopy(self.vacancy_by_size)
				self.dynamicprices[currentdate+ timedelta(days=i)] = copy.deepcopy(self.prices)
				self.date_manually_set[currentdate+ timedelta(days=i)] = {1:False, 2:False, 3:False, 4:False, 5:False, 6:False}

	#Fill booking, return false if no rooms available of that size
	def fill_booking(self, date, roomsize):
		if self.datevacancy[date][roomsize] > 0:
			self.datevacancy[date][roomsize] -= 1
			return True
		else:
			return False
	#Add a random booking, used for simulating other hotels
	def add_rand_booking(self):
		currentdate = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
		day = random.randint(1,100)
		capacity = random.randint(1,6)
		self.fill_booking(currentdate+ timedelta(days=day), capacity)

	#Dyanmic price setting
	def set_price_for_date(self, date):
		#Iterat through each roomsize
		for i in self.rooms:
			#Check if the owner manually set the price for this date, if true, do not change
			if self.date_manually_set[date][i] == False:
				
				#Get how many days in advance the booking is being made
				currentdate = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
				days_in_advance = (date - currentdate).days
				booking_ahead_adjustment = days_in_advance/365
				
				#Collect all nearby hotels in a radius (set to 40 for default)
				nearby_hotels = self.city.get_close_hotels(self, 40)
				
				#Get the average competitor price
				average_comp_price = self.city.get_average_comp_price(i, date, nearby_hotels)
				
				#Find what % of rooms are full for this date
				own_occupancy_rate = 1-(self.datevacancy[date][i]/self.rooms[i])
				
				#Find what average % of rooms are full for other hotels
				comp_occupancy = (self.city.get_average_comp_occupancy(i, date, nearby_hotels))
				

				#Adjust the price: the > occupancy rate, > comp occupancy rate, and closer to the booking date it is the higher the price goes
				self.dynamicprices[date][i] += ((self.prices[i] * own_occupancy_rate * comp_occupancy)/2) + ((self.prices[i] * (1-booking_ahead_adjustment))/2)
				
				#Average out the price with the average competitor price, so it is not too overblown
				self.dynamicprices[date][i] = (average_comp_price+ self.dynamicprices[date][i])/2
				
				#Collect variables to be compared against historical data
				comprow = [i, days_in_advance, own_occupancy_rate, comp_occupancy,average_comp_price]
				#To decrease runtime only look at 1000 datapoints
				sampled = self.historical_data.sample(n=1000, random_state=1).reset_index(drop=True)
				#Find the index of the datapoint that is the most similar to the current date
				sim_index = get_similar_index(sampled.drop(columns=["Set Price", "Percent Booked"]), comprow)

				#Get the percentange of rooms sold for that historical date
				pbooked = sampled["Percent Booked"][sim_index]
				
				#If the room was booked < 50% historically then decrease the price of the hotel, else increase price relative to % booked
				if pbooked < .5:
					self.dynamicprices[date][i] = self.dynamicprices[date][i] * (.5 + pbooked)
				else:
					self.dynamicprices[date][i] = self.dynamicprices[date][i] * (1 + (pbooked/2))
				
				#Make sure the price does not pass the floor or the ceiling
				if self.dynamicprices[date][i] < self.floors[i]:
					self.dynamicprices[date][i] = self.floors[i]
				elif self.dynamicprices[date][i] > self.ceilings[i]:
					self.dynamicprices[date][i] = self.ceilings[i]
				
				#Round the price so it is easier to view
				self.dynamicprices[date][i] = round(self.dynamicprices[date][i] ,2)
				
	#Save the hotel in a json file
	def save_hotel(self, name):
		converteddt = {}
		convertedprices = {}
		convertmanual = {}
		#Convert datetime keys into strings for storage
		for i in self.datevacancy:
			converteddt[i.strftime('%Y-%m-%d')] = self.datevacancy[i]
		for i in self.dynamicprices:
			convertedprices[i.strftime('%Y-%m-%d')] = self.dynamicprices[i]
		for i in self.date_manually_set:
			convertmanual[i.strftime('%Y-%m-%d')] = self.date_manually_set[i]
		hotel_dict = {
			"coords": self.coords,
			"idnum" : self.idnum,
			"stars" : self.stars,
			"rooms" : self.rooms,
			"prices" : self.prices,
			"dynamicprices" : convertedprices,
			"ceilings" : self.ceilings,
			"floors" : self.floors,
			"vacancy" : self.vacancy,
			"vacancy_by_size" : self.vacancy_by_size,
			"datevacancy" : converteddt,
			"date_manually_set": convertmanual


		}
		with open(f"{name}.json", "w") as outfile:
			json.dump(hotel_dict, outfile)

	#Load a hotel from a json file
	def load_hotel(self, file, city):
		with open(file,"r") as file:
			hotel_dict = json.load(file)
		self.coords = hotel_dict["coords"]
		self.idnum = hotel_dict["idnum"]
		self.stars = hotel_dict["stars"]
		self.rooms = hotel_dict["rooms"]
		self.prices = hotel_dict["prices"]
		convertedprices = hotel_dict["dynamicprices"]
		self.ceilings = hotel_dict["ceilings"]
		self.floors = hotel_dict["floors"]
		self.vacancy = hotel_dict["vacancy"]
		self.vacancy_by_size = hotel_dict["vacancy_by_size"]
		converteddt = hotel_dict["datevacancy"]
		convertmanual = hotel_dict["date_manually_set"]
		#print( convertmanual, file=sys.stderr)
		self.city = city
		#Convert string dates into datetime keys
		for i in converteddt:
			self.datevacancy[datetime.strptime(i, '%Y-%m-%d')] = converteddt[i]
		for i in convertedprices:
			self.dynamicprices[datetime.strptime(i, '%Y-%m-%d')] = convertedprices[i]
		for i in convertmanual:
			self.date_manually_set[datetime.strptime(i, '%Y-%m-%d')] = convertmanual[i]
		


"""Class for the entire city of hotels"""
class CityHotels:
	#Initialize the city
	def __init__(self, hotels={}):
		self.hotels = hotels 

	#Add a hotel to the city
	def add_hotel(self, hotel):
		self.hotels[hotel.idnum] = hotel

	#Get all the nearby hotels to a center hotel within the radius
	def get_close_hotels(self, center, radius):
		nearby = []
		for i in self.hotels:
			
			if not self.hotels[i] == center:

				if center.get_dist(self.hotels[i]) <= radius:
					nearby.append(self.hotels[i])
		return nearby

	#Same as get close hotels, but only look at hotels that have the same # of stars as the center
	def get_close_hotels_by_stars(self, center, radius):
		nearby = []
		for i in self.hotels:
			if not self.hotels[i] == center:

				if center.get_dist(self.hotels[i]) <= radius and center.stars == self.hotels[i].stars:
					nearby.append(self.hotels[i])
		return nearby

	#Get the average occupancy of the nearby hotels
	def get_average_comp_occupancy(self, roomsize, date, nearby):
		total_rooms = 0
		total_available = 0
		for i in nearby:
			total_rooms += i.rooms[int(roomsize)]
			total_available += i.datevacancy[date][int(roomsize)]
		return total_available/total_rooms

	#Get the average price of the nearby hotels
	def get_average_comp_price(self, roomsize, date, nearby):
		total = 0
		counter = 0
		for i in nearby:
			#print(i.dynamicprices[date][1], type(date), type(roomsize), roomsize, file=sys.stderr)
			total += i.dynamicprices[date][int(roomsize)]
			counter += 1

		return total/counter


#Cosine similarity for finding the historical data point closest to current one
def cosine_sim(vec1, vec2):
	#print(vec1.shape(), vec2.shape())
	return cosine_similarity([vec1], [vec2])[0][0]

#Finds the historical data point closest to the current one
def get_similar_index(df, array):
	max_similarity = -1
	most_similar_index = -1

	for index, row in df.iterrows():
	    row_array = np.array(row)  # Assuming each cell contains a list
	    similarity = cosine_sim(array, row_array)
	    
	    if similarity > max_similarity:
	        max_similarity = similarity
	        most_similar_index = index
	return most_similar_index


#Generate rooms for the city
def generate_rooms():
	rooms = {}
	for i in range(1,7):
		n = random.randint(10,50)
		rooms[i] = n

	return rooms

#Generate hotels
def generate_hotels(x):
	city = CityHotels()
	for i in range(x):
		xcoord = random.randint(0,x)
		ycoord = random.randint(0,x)
		stars = random.randint(1,5)
		
		rooms = generate_rooms()
		temp_hotel = Hotel(i,[xcoord, ycoord],stars, city, rooms)
		#Add random bookings to simulate filled hotels
		for i in range(random.randint(1000,10000)):
			temp_hotel.add_rand_booking()
		city.add_hotel(temp_hotel)
	return city



#Save the city data to be loaded again later (only used for testing consistency)
def save_city_data(city):
	hotelarr = []
	roomarr = []
	bookingarr = []
	for i in city.hotels:
		hotelarr.append([city.hotels[i].idnum, city.hotels[i].coords[0], city.hotels[i].coords[1], city.hotels[i].stars])
		for j in city.hotels[i].rooms:
			roomarr.append([j, city.hotels[i].idnum, city.hotels[i].prices[j], city.hotels[i].rooms[j]])
		for date in city.hotels[i].datevacancy:
			#print(city.hotels[i].datevacancy[date], date)
			for size in city.hotels[i].datevacancy[date]:
				if city.hotels[i].datevacancy[date][size] != city.hotels[i].rooms[size]:

					bookingarr.append([date, city.hotels[i].idnum, size, city.hotels[i].rooms[size]-city.hotels[i].datevacancy[date][size], city.hotels[i].rooms[size]])



	hoteldf = pd.DataFrame(hotelarr, columns=["HotelID", "Xcoord", "Ycoord", "Stars"])
	hoteldf.to_csv("Hotels.csv", index=False)

	roomdf = pd.DataFrame(roomarr, columns=["RoomSize", "HotelID", "BasePrice", "NumRoomsAtHotel"])
	roomdf.to_csv("Rooms.csv", index=False)

	bookingdf = pd.DataFrame(bookingarr, columns=["Date", "HotelID", "RoomSize", "BookedRooms", "TotalRooms"])
	bookingdf.to_csv("Bookings.csv", index=False)

# Generate random historical data
def gen_historical_data(x):
	data_arr = []
	for i in range(x):
		stars = 3
		roomsize = random.randint(1,6)
		days_in_advance = random.randint(1,364)
		own_occupancy_rate = random.random()
		average_comp_price = round(stars*random.uniform(18,22)*roomsize, 2)
		booking_ahead_adjustment = days_in_advance/365
		comp_occupancy_rate = random.random()
		price = average_comp_price + random.randint(-10,10)
		price = price + ((price * own_occupancy_rate * comp_occupancy_rate)/10) + ((price * (1-booking_ahead_adjustment))/10)
		
		r = random.random()

		if price > average_comp_price:
			percent_booked = random.uniform(0,.8)
		else:
			percent_booked = random.uniform(.2, 1)
		data_arr.append([roomsize, days_in_advance, own_occupancy_rate, comp_occupancy_rate,average_comp_price, price, percent_booked])
	datadf = pd.DataFrame(data_arr, columns=["RoomSize", "Days In Advance", "Occupancy Rate", "Comp Occupancy Rate", "Avg Comp Price", "Set Price", "Percent Booked"])
	datadf.to_csv("HistoricalData.csv", index=False)





gen_historical_data(100000)
city = generate_hotels(100)
myHotel = Hotel(152,[50, 50],3, city, generate_rooms(), historical_data=pd.read_csv("HistoricalData.csv"))
counter = 0
# for i in myHotel.dynamicprices:
# 	myHotel.set_price_for_date(i)
	
# 	break

save_city_data(city)