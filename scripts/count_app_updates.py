import pymongo
import pandas as pd
import os
from dateutil import parser
from pymongo import MongoClient
from datetime import datetime, timedelta

production_db = "mongodb://roman:Zq4Ln7Vc2Xj9Gt5P@10.2.3.41:27017,10.2.4.41:27017,10.2.5.41:27017/Cluster0?replicaSet=rs0"
myclient = pymongo.MongoClient(production_db)

mydb = myclient["Cluster0"]

table = 'userdevicedatas'
mycol = mydb[table]

all_documents = mycol.find()

count_brand = {}
count_version = {}
count_apple_model = {}
count_apple_osversion = {}
count_version_ios = {}
count_version_android = {}
count_version_huawei = {}
calc = {}


i = 0

# Задайте начальную дату в формате ISO 8601
today = datetime.now()
three_month_ago = today - timedelta(days=90)
# Выполните запрос с фильтром по дате
query = {
    "updated_at": {
        "$gte": three_month_ago
    }
}  # Замените 'your_date_field' на имя вашего поля с датой

necessary_records = {
    "appVersion": 1,
    "brand": 1,
    "modelName": 1,
    "osVersion": 1
}

results = mycol.find(query, necessary_records)

for document in results:
    i += 1
    if document['brand'].lower() == 'apple':
        if document['modelName'] == 'iPhone16,2':
            document['modelName'] = 'iPhone 15 Pro Max'
        if document['modelName'] == 'iPhone16,1':
            document['modelName'] = 'iPhone 15 Pro'
        if document['modelName'] == 'iPhone15,5':
            document['modelName'] = 'iPhone 15 Plus'
        if document['modelName'] == 'iPhone15,4':
            document['modelName'] = 'iPhone 15'
        if document['modelName'] not in count_apple_model:
            count_apple_model[document['modelName']] = 1
        else:
            count_apple_model[document['modelName']] += 1

        if document['osVersion'] not in count_apple_osversion:
            count_apple_osversion[document['osVersion']] = 1
        else:
            count_apple_osversion[document['osVersion']] += 1

    if document['brand'].lower() not in count_brand:
        count_brand[document['brand'].lower()] = 1
    else:
        count_brand[document['brand'].lower()] += 1

    if document['appVersion'].lower() not in count_version:
        count_version[document['appVersion'].lower()] = 1
        count_version_ios[document['appVersion'].lower()] = 0
        count_version_android[document['appVersion'].lower()] = 0
        count_version_huawei[document['appVersion'].lower()] = 0

        if document['brand'].lower() == 'apple':
            count_version_ios[document['appVersion'].lower()] = 1
        else:
            if document['brand'].lower() == 'huawei':
                count_version_huawei[document['appVersion'].lower()] = 1
            else:
                count_version_android[document['appVersion'].lower()] = 1

    else:
        count_version[document['appVersion'].lower()] += 1
        if document['brand'].lower() == 'apple':
            count_version_ios[document['appVersion'].lower()] += 1
        else:
            if document['brand'].lower() == 'huawei':
                count_version_huawei[document['appVersion'].lower()] += 1
            else:
                count_version_android[document['appVersion'].lower()] += 1


for j in count_version:
    calc[j] = round((count_version[j]) / i * 100, 2)

count_apple_model_sorted = dict(sorted(count_apple_model.items(), key=lambda x: x[1], reverse=True))
count_apple_osversion_sorted = dict(sorted(count_apple_osversion.items(), reverse=True))
count_version_sorted = dict(sorted(count_version.items(), key=lambda x: x[0], reverse=True))
calc_sorted = dict(sorted(calc.items(), key=lambda x: x[0], reverse=True))
count_version_sorted['Total'] = i
count_version_sorted['%'] = '-'
count_version_sorted['From date'] = str(three_month_ago).split()[0]
count_version_sorted['Current date'] = str(datetime.now()).split()[0]

count_version_ios['Total'] = sum(count_version_ios.values())
count_version_ios['%'] = (count_version_ios['Total']/count_version_sorted['Total'])
count_version_ios['%'] = round((count_version_ios['%'])* 100, 2)

count_version_android['Total'] = sum(count_version_android.values())
count_version_android['%'] = (count_version_android['Total']/count_version_sorted['Total'])
count_version_android['%'] = round((count_version_android['%'])* 100, 2)

count_version_huawei['Total'] = sum(count_version_huawei.values())
count_version_huawei['%'] = (count_version_huawei['Total']/count_version_sorted['Total'])
count_version_huawei['%'] = round((count_version_huawei['%'])* 100, 2)


vse = [count_version_sorted, calc_sorted, count_version_ios, count_version_android, count_version_huawei]

df = pd.DataFrame(count_brand, index=['value'])
df1 = pd.DataFrame(vse, index=['value', '%', 'ios', 'Android', 'Huawei'])

df2 = pd.DataFrame(count_apple_model_sorted, index=['value'])
df3 = pd.DataFrame(count_apple_osversion_sorted, index=['value'])

df_transposed = df.transpose()
df1_transposed = df1.transpose()
df2_transposed = df2.transpose()
df3_transposed = df3.transpose()


with pd.ExcelWriter('data/ud.xlsx') as writer:
    df1_transposed.to_excel(writer, sheet_name='version')
    df_transposed.to_excel(writer, sheet_name='brand')
    df2_transposed.to_excel(writer, sheet_name='apple_model')
    df3_transposed.to_excel(writer, sheet_name='apple_os')

os.system(f'start excel {'data/ud.xlsx'}')