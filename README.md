#How to Use:
## 1. Make sure all used libraries are installed
Project written in python3 and Libraries used are in requirements.txt
## 2. Run 'python app.py' in command line
## 3. On the main page there are two buttons:
### Look for room:
To use this button first select a date from the calendar drop down, must be a date in the future within a year. Then click button. This will pull up a page displaying the prices for each room capacity, and how many rooms are available for this day. On this new page there is another calendar dropdown, where you can select a new date and click look for room again and it will update. The return home button will return to the main page.
### Go to editor:
This button takes you to a page for the hotel owner to change the price manually, set a price floor and a price ceiling (selecting a date on the dropdown on the main page will do nothing). On this page there is another date dropdown to select what date to edit the price for. To change which date you want to edit the prices for select a date from the calendar (after current date, and at most a year ahead) and then press the "change date" button. If no date is selected changing the manual price will edit the default price of the hotel, otherwise the prices for the selected date will be updated. Floor and ceiling boxes are already filled with the current floor and ceiling, and the owner can change those values. They can also enter a value into the manually change price boxes to set a price for the room, which will override everthing. The price will update once "update values" is pressed. Lastly to return to the main page press "return home"


# Approach and decisions made
To address this project I split it into 3 main parts, developing the algorithm to update room prices, creating the framework that can support the algorithm, and then creating the web interface for the hotel owner to interact with. To start I began with creating the framework to support the algorithm.
## Framework
The approach I decided to take was to create two objects, a Hotel object and a City object. The City object would consist of many Hotels, which would allow for storage of neighboring hotels and to compare against each other when designing the dynamic algorithm. 
### Each hotel contained the following local variables:
- coords = coordinated on a cartesian plane of the hotel
- idnum = id number of the hotel
- historical_data = historical data of booked rooms for the hotel
- stars = how many stars the hotel has
- city = the city that contains the hotel
- rooms = a dictionary with the keys being the room capacity, and the value being the # of rooms of that capacity in the hotel
- vacancy = total # of room available in the hotel
- prices = a dictionary with keys being the room capacity, and the value being the default price of the rooms of that capacity
- dyanmicprices = a dictionaty with the keys being dates, and the values being prices dictionaries for that date
- ceilings = a dictionary with keys being the room capacity, and the value being the highest a price can get for that type of room
- floors = a dictionary with keys being the room capacity, and the value being the lowest a price can get for that type of room
- date_manually_set = a dictionaty with the keys being dates, and the values being another dictionary with the keys being roomsizes, and the values being a boolean of whether that roomsize at that date has been manually set by the owner
- vacancy_by_size = a dictionary with the keys being roomsizes, and the values being how many rooms are vacant for that roomsize
- datevacancy = a dictionary with the keys being dates, and the values being vacancy_by_size dictionaries for that date

Using all of these local variables gave me all of the resources I needed to execute the algorithm

## Algorithm:
### The algorithm I decided on to calculate the price of each individual roomsize per date was: 
avg(average_price_of_other_hotels, (previous_dynamic_price + ((default_price * occupancy_rate_of_hotel * avg_occupancy_rate_of_other_hotels)/2) + ((default_price * 1-(days_booked_in_advanced/365)/2)))
Then I found the historical value that had the closest roomsize, days_booked_in_advanced, occupancy_rate_of_hotel, avg_occupancy_rate_of_other_hotels, and average_price_of_other_hotels to the current attempted booking, and found the percentage of rooms booked for that night. 
