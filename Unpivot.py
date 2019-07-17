import csv
import datetime

datafile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\ExampleModel\\simulated engineered jun 19_v1 (Copy)_NetSimData\\Ext data_Forecast raw.txt"
writefile = "C:\\Users\\greg.plank\\OneDrive - LLamasoft, Inc\\SCG\\Projects\\201907 LBrands\\Models\\ExampleModel\\simulated engineered jun 19_v1 (Copy)_NetSimData\\StoreForecast.txt"
t = open(datafile)

startdate = datetime.date(2018,10,6)
csv_t = csv.reader(t, delimiter =',')
with open('StoreForecast.txt', 'wb') as writeFile:
    writer = csv.writer(writeFile)

    for row in csv_t:
        site = row[3]
        product = row[2]

        # write site, product, row[2]
        writer.writerow([site,product,row[1],str(startdate)])

        for i in range(1,15,1):
            # write site, product, row[4+i]
            date_title = startdate + datetime.timedelta(days = (i * 7))
            writer.writerow([site, product, row[3 + i],str(date_title)])
