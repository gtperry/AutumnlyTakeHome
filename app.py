from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
from RoomPrice import Hotel, CityHotels, generate_hotels, generate_rooms
import sys
import pandas as pd

#Make a default floors and ceilings array
def make_floors(floors):
    arr = []
    for i in floors:
        arr.append(floors[i])
    return arr
app = Flask(__name__)

#Default global variables
values = ["20", "40", "60", "80", "100", "120"]
room_prices = [(1,20,0), (1,20,0),(1,20,0),(1,20,0),(1,20,0),(1,20,0)]

#Generate the city
city = generate_hotels(100)

#Generate hotel 
# myHotel = Hotel(152,[50, 50],3, city, generate_rooms())
# myHotel.save_hotel("Myhotel")

#Load up hotel once already generated for consistent testing
myHotel = Hotel(historical_data=pd.read_csv("HistoricalData.csv"))
myHotel.load_hotel("Myhotel.json", city)

#Init global variables
currentdate = "Default"
floors = make_floors(myHotel.floors)
ceilings = make_floors(myHotel.ceilings)
keydate = datetime.today()
index = 0
for i in myHotel.prices:
    values[index] = myHotel.prices[i]
    index+=1

#Index page
@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')

#Page for searching for room prices
@app.route('/submit', methods=['GET','POST'])
def submit():
    try:
        global room_prices
        global myHotel
        
        #Get the date
        datetime_str = request.form['datetime']
        #Convert to datetime object
        datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d')
        
        #Dynamically update the price for date
        myHotel.set_price_for_date(datetime_obj)
        #Change the room_prices array to correspond to the values for this date
        for i in range(len(room_prices)):
            room_prices[i] = (i+1, myHotel.dynamicprices[datetime_obj][str(i+1)], myHotel.datevacancy[datetime_obj][str(i+1)])

        return render_template('result.html', date_looking_at=datetime_str, rooms=room_prices)
    except Exception as e:
        return str(e)

#Page for the owner to set ceilings, floors, and manually update price
@app.route('/owner', methods=['GET','POST'])
def owner():
    try:
        global values
        global myHotel
        global city
        global currentdate
        global floors
        global ceilings
        global keydate
        
        if request.method == 'POST':
            #Differentiate between buttons pressed
            hiddenval = request.form.get("btn_identifier")
            #If updating floor, ceiling, manual price
            if hiddenval == "fc":
                #Go through each room size
                for i in range(len(values)):\
                    #Collect inputs (floor and ceiling and shown as their default values)
                    floor = request.form.get(f'floor{i+1}')
                    ceiling = request.form.get(f'ceiling{i+1}')
                    newprice = request.form.get(f'price{i+1}')

                    #If the manual price is set the override floor and ceiling and update that
                    if not newprice == "":
                        values[i] = float(newprice)
                        #If a date is selected, update for that date, if not, update default price
                        if currentdate != "Default":
                            myHotel.dynamicprices[keydate][str(i+1)] = values[i] 
                            myHotel.date_manually_set[keydate][str(i+1)] = True
                        else:
                            myHotel.prices[str(i+1)] = values[i]
                    else:
                        #Check if floor and ceiling are changed, and update the price if the price is outside the range
                        if not floor == "":
                            myHotel.floors[str(i+1)] = float(floor)
                            floors = make_floors(myHotel.floors)
                            if float(floor) > float(values[i]):
                                values[i] = float(floor)
                        if not ceiling == "":
                            myHotel.ceilings[str(i+1)] = float(ceiling)
                            ceilings = make_floors(myHotel.ceilings)
                            if float(ceiling) < float(values[i]):
                                values[i] = float(ceiling)
                        #If a date is selected, update for that date, if not, update default price
                        if currentdate != "Default":
                            myHotel.dynamicprices[keydate][str(i+1)] = values[i] 
                        else:
                            myHotel.prices[str(i+1)] = values[i]
                            
                
                return redirect(url_for('owner'))
            #If the date is updated
            elif hiddenval == "date":
                date = request.form.get('datetime2')
                currentdate = date
                keydate = datetime.strptime(date, "%Y-%m-%d")
                
                #Set dynamic price for this date
                myHotel.set_price_for_date(keydate)
                index = 0
                
                #Update the values (making sure they stay within floor/ceiling range)
                for i in myHotel.dynamicprices[keydate]:
                    
                    values[index] = myHotel.dynamicprices[keydate][i]
                    #print("4",values[index], floors[index], file=sys.stderr)
                    if values[index] < floors[index]:
                        values[index] = floors[index]
                    elif values[index] > ceilings[index]:
                        values[index] = ceilings[index]
                    index+=1
                
                return redirect(url_for('owner'))
        else:
            
            return render_template('owner.html', values=values, date_looking_at=currentdate, floors=floors, ceilings=ceilings)
    except Exception as e:
        
        return str(e)


if __name__ == '__main__':
    app.run(debug=True)