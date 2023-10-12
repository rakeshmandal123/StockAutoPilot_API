import pandas as pd

symbolDataLink = "D:\rupal\LoginApiSap\StockAutoPilot_API\nifty52weekhigh"

symbolData = pd.read_csv(symbolDataLink)
# symbolData.to_csv('Script_Data.csv') // convert file to excel

scriptCode = []


# print(symbolData)

for data in symbolData.iterrows():
    print(data[1][0])
    print("LTP", data[1][5])
    print("52 week high", data[1][10])
    print(data[1][5]>data[1][10])
    print("==============")
#print(len(scriptCode))
