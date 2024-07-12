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

Using all of these local variables gave me all of the resources I needed to execute the algorithm.

## Algorithm:
### The algorithm I decided on to calculate the price of each individual roomsize per date was: 
avg(average_price_of_other_hotels, (previous_dynamic_price + ((default_price * occupancy_rate_of_hotel * avg_occupancy_rate_of_other_hotels)/2) + ((default_price * 1-(days_booked_in_advanced/365)/2)))


Then I found the historical value that had the closest roomsize, days_booked_in_advanced, occupancy_rate_of_hotel, avg_occupancy_rate_of_other_hotels, and average_price_of_other_hotels to the current attempted booking, and found the percentage of rooms booked for that night. If less than 50% of rooms were booked for that night I would multiply the dynamicprice by .5 + % booked, so that it would decrease the price to be more likely to be booked. Likewise if the booking percentage was greater than 50% I would multiply the dynamicprice by 1 + (% booked-.5) so that there would be more profit gained. The historical data for this step was randomly generated, but given live data, I believe it would be more accurate at scaling the dynamic price apporpriately. Lastly, I would check if the new price went above or below the floor or ceiling, and adjust accordingly. I chose not to use ML for this algorithm because there was no real data, using either randomly generated data or synthetic data that followed an algorithm for ml would have produced very lackluster results. For random data, ML cannot gain any insight to the pattern because there would be none, and for algorithmic genenerated data would be redundant, because I could just use that algorithm instead of having ML add small noise to the outputs. If there were real data to train on, I would probably use ML instead of this logic based algorithm because it would be able to see exactly which variables are more important to maximizing profits and weight them better than I can. In addition, I chose to keep the historical data stored in a pandas dataframe rather than a SQL database. While a SQL database would scale better, I felt that the data I was working with was small enough to where the simplicity of a pandas dataframe was better for this usecase. However, to scale this project, I would definitely switch to a SQL database instead. I chose to randomize the hotels and their room capacity, because after thoroughly testing the validity of the math when creating the algorithm, I just needed data to exist to show that it was changing dynamically. My rational between the pricing itself is that I believed that the max price that could be gained from this would be ~previous_dynamic_price *3 and the lowest could be ~previous_dynamic_price/2 which seemed like a good range for the price to be able to fall in, and I weighted it with priority of: average_price_of_other_hotels > days_booked_in_advanced > occupancy_rate_of_hotel = avg_occupancy_rate_of_other_hotels. This was just the order of importance that I felt was best, the truth of the domain could be that the actually order of importance is different.

## Web Interface:
For the web interface I created 3 pages for the user to switch through. A home page, where they can select a date, and choose to go to either the room price page or the price editor page. At the room price page it would display the room prices for each room size for the date selected at the home page, and the user can change and update the date on this page as well. For the editor page I made it so the owner of the hotel can edit the price floor and ceiling and also manually edit the price of a date they select. I kept these two pages separate so that if it was needed to scale in the future where customers could look at the price page and keep the owner's page separate.
