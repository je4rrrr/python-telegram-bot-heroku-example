import logging
import os
import sys
import requests
from numpy import arctan
from datetime import date

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

TOKEN = "1662384534:AAHRMfA1NZMIInG1pLtCKwAs4YG1JA4NQeM"
HEROKU_APP_NAME = "tranquil-acadia-50401"
PORT = int(os.environ.get('PORT', 8443))

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    message = calculate_wbgt()
    update.message.reply_text(message)

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

def emoji(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('testing 😀')

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

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

            
    output = ""
    for station in stations.items():
        symbol = ""
        if station[1][4] == "WHITE":
            symbol = "White ⬜"
        if station[1][4] == "GREEN":
            symbol = "Green 🟩"
        if station[1][4] == "YELLOW":
            symbol = "Yellow 🟨"
        if station[1][4] == "RED":
            symbol = "Red 🟥"
        if station[1][4] == "BLACK":
            symbol = "Black ⬛"
        if station[1][4] == "ERROR":
            symbol = "Error ⚠️"

        output + "Station: " + station[1][0] + "\n" + "🌡 " + str(station[1][1]) + "°C 💦 " + str(station[1][2]) + "%" + "\n" + "Code " + symbol + "\n"
    return output

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("emoji", emoji))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://tranquil-acadia-50401.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()