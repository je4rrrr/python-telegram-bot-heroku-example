import logging
import os
import sys
import requests
from numpy import arctan
from datetime import date

from telegram.ext import Updater, CommandHandler

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

mode = "dev"
TOKEN = "1662384534:AAHRMfA1NZMIInG1pLtCKwAs4YG1JA4NQeM"
if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)


def start_handler(update, context):
    stations = calculate_wbgt()
    update.message.reply_text(stations)

def calculate_wbgt():
    today = str(date.today())
    air_temp = requests.get('https://api.data.gov.sg/v1/environment/air-temperature?date=' + today)
    #print(air_temp.json()['metadata'])

    stations = {}
    for station in air_temp.json()['metadata']['stations']:
        stations[station['id']] = [station['name'], 0, 0, '', '']

    #optimisation opportunity
    for item in air_temp.json()['items']:
        for reading in item['readings']:
            stations[reading['station_id']][1] = reading['value']


    relative_humidity = requests.get('https://api.data.gov.sg/v1/environment/relative-humidity?date=' + today)

    for item in relative_humidity.json()['items']:
        for reading in item['readings']:
            stations[reading['station_id']][2] = reading['value']

    for station_id in stations.keys():
        t = stations[station_id][1]
        rh = stations[station_id][2]
        wbgt = t * arctan(0.151977 * (rh + 8.313659)**(1/2)) + arctan(t + rh) - arctan(rh - 1.676331) + 0.00391838 * rh**(3/2) * arctan(0.023101 * rh) - 4.686035
        stations[station_id][3] = wbgt
        if wbgt <= 29.9:
            stations[station_id][4] = 'WHITE'
        elif wbgt >= 30 and wbgt <=30.9:
            stations[station_id][4] = 'GREEN'
        elif wbgt >= 31 and wbgt <=31.9:
            stations[station_id][4] = 'YELLOW'
        elif wbgt >= 32 and wbgt <=32.9:
            stations[station_id][4] = 'RED'
        elif wbgt > 33:
            stations[station_id][4] = 'BLACK'
        else:
            stations[station_id][4] = 'ERROR'
        
    return stations

if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start_handler))

    run(updater)
