import logging
import os
from bs4 import BeautifulSoup
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, Updater, MessageHandler, filters
from dotenv import load_dotenv
import pymongo
import certifi

load_dotenv()


TOKEN = os.getenv('TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

commands = ["moviealert - following imdb url to add to your movie alert list", "deletealert - following imdb url to delete from your movie alert list",
            "moviealertlist - list of your movie alerts", "clearmoviealerts - delete all of your movie alerts", f"coupons - register to receive Udemy 100% off coupons",
            "unregistercoupons - unregister from receiving Udemy coupons", "fuelcosts - register to receive israel fuel costs notifications on change",
            "unregisterfuelnotifications - unregister from receiving fuel costs notifications", "alertlist - list of all registered services"
            ,"waitcoupons - not sending new coupons and holding them until you exit wait mode", "exitwaitcoupons - send all gathered coupons while being in wait mode",
             "managercommands - list of manager command require password", "stopbot - stops the bot and deletes your alert list"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ca = certifi.where()
    await update.message.reply_text(chat_id)
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.manager
    found = db.registered.find_one({"_id": chat_id})
    if found is None:
        db.registered.insert_one({"_id": chat_id})
    await update.message.reply_text('Hi! check out the commands with /help')
    await update.message.reply_text('Also some times the server takes a while (about 30 seconds) to respond, so be patient!')

async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the bot."""
    await update.message.reply_text('Deleting all of your alerts and stopping the bot! bye!')
    chat_id = update.effective_chat.id
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.movie_alerts
    db.alerts.delete_many({"chat_id": chat_id})
    db = client.new_database
    db.registered.delete_many({"_id" : chat_id})
    db = client.manager
    db.registered.delete_many({"_id" : chat_id})


async def help(update, context):
    """Send a message when the command /help is issued."""
    message = ""
    index = 1
    for command in commands:
        message += str(index) + ". " + command + "\n"
        index += 1
    if message != "":
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Can't help you! good luck!")

def to_db(chat_id, movie_name, movie_link):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.movie_alerts
    db.alerts.insert_one({"chat_id": chat_id, "movie_name": movie_name, "movie_link": movie_link})

def get_movie_info(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
    soup = BeautifulSoup(r, 'html.parser')
    movie_name = soup.find('span', {'class': 'hero__primary-text'}).text
    year = int(soup.find_all('ul', {'class': 'ipc-inline-list ipc-inline-list--show-dividers sc-d8941411-2 cdJsTz baseAlt'})[0].text[0:4])
    print(movie_name, year)
    return [movie_name, year]

async def movie_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        movieURL = update.effective_message.text
        movie_name, year = get_movie_info(movieURL.replace("/moviealert ", ""))
        movie_name1 = ''.join(char for char in movie_name if char.isalnum() or char == ' ' or char == '-')
        movie_name1 = movie_name1.replace(" ", "-").lower() + "-" + str(year)
        movie_link = f"https://yts.mx/movies/{movie_name1}"
        to_db(chat_id, movie_name, movie_link)
        await update.message.reply_text("You will be notified when " + movie_name + " is released!")
    except Exception as e:
        print(e)
        await update.message.reply_text("Invalid URL. Try something like this: /moviealert https://imdb.com/title/tt0111161/")

async def clear_movie_alerts(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.movie_alerts
    chat_id = update.effective_chat.id
    db.alerts.delete_many({"chat_id": chat_id})
    await update.message.reply_text("Movie alerts deleted")

def remove_from_db(url, chat_id):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.movie_alerts
    db.alerts.delete_many({"chat_id": chat_id, "movie_link": url})

async def delete_alert(update: Update, context):
    try:
        chat_id = update.message.chat_id
        movieURL = update.effective_message.text
        movie_name, year = get_movie_info(movieURL.replace("/deletealert ", ""))
        movie_name1 = movie_name.replace(":", "")
        movie_name1 = movie_name1.replace(" ", "-").lower() + "-" + str(year)
        movie_link = f"https://yts.mx/movies/{movie_name1}"
        remove_from_db(movie_link, chat_id)
        await update.message.reply_text(movie_name + " is removed from the movie alert list!")
    except Exception as e:
        print(e)
        await update.message.reply_text("Invalid URL. Try something like this: /deletealert https://imdb.com/title/tt0111161/")

async def movie_alert_list(update, context):
    try:
        chat_id = update.effective_chat.id
        ca = certifi.where()
        client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
        db = client.movie_alerts
        alerts = db.alerts.find({"chat_id": chat_id})
        index = 1
        message = ""
        for alert in alerts:
            message += str(index) + ". " + alert["movie_name"] + "\n"
            index += 1
        if message != "":
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("You have no alerts!")
    except Exception as e:
        print(e)
        await update.message.reply_text("Something went wrong!")

async def register_coupons(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.new_database
    chat_id = update.effective_chat.id
    if db.registered.find_one({"_id": chat_id}) is None:
        db.registered.insert_one({"_id": chat_id})
        await update.message.reply_text("You are now registered for coupons alerts!")
    else:
        await update.message.reply_text("You are already registered for coupons alerts!")

async def unregister_coupons(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.new_database
    chat_id = update.effective_chat.id
    if db.registered.find_one({"_id": chat_id}) is not None:
        db.registered.delete_one({"_id": chat_id})
        await update.message.reply_text("You are now unregistered for coupons alerts!")
    else:
        await update.message.reply_text("You are not registered for coupons alerts!")

async def alert_list(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.fuel
    chat_id = update.effective_chat.id
    fuel = db.registered.find_one({"_id": chat_id})
    message = "Registered services:\n"
    index = 1
    if fuel != None:
        message += str(index) + ". " + "Israel fuel costs notifications" + "\n"
        index += 1
    db = client.new_database
    coupon = db.registered.find_one({"_id": chat_id})
    if coupon != None:
        message += str(index) + ". " + "Udemy 100% off coupon notifications" + "\n"
        index += 1
    db = client.movie_alerts
    movie = db.alerts.find({"chat_id": chat_id})
    if movie != None:
        message += str(index) + ". " + "Movie notifications" + "\n"
        index += 1
    if index == 1:
        await update.message.reply_text("you are not registered for any notifications")
    else:
        await update.message.reply_text(message)

async def wait_coupons(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.new_database
    chat_id = update.effective_chat.id
    coupon = db.waiting.find_one({"_id": chat_id})
    if coupon != None:
        await update.message.reply_text("You are already in wait mode")
    else:
        sub = db.registered.find_one({"_id": chat_id})
        if sub != None:
            await update.message.reply_text("Entered wait mode. In the meantime the coupons are gathered and will be sent when you exit wait mode")
            db.waiting.insert_one({"_id": chat_id})
        else:
            await update.message.reply_text("First register for coupons notifications using /coupons")

async def exit_wait_coupons(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.new_database
    chat_id = update.effective_chat.id
    coupon = db.waiting.find_one({"_id": chat_id})
    if coupon != None:
        db.waiting.delete_one({"_id": chat_id})
        await update.message.reply_text("Exited wait mode. sending coupons gathered")
        coupons = db.gathered.find({"chat_id": chat_id})
        sent = False
        for c in coupons:
            sent = True
            name = c["name"]
            coupon_url = c["coupon_url"]
            percent = c["percent"]
            await context.bot.send_photo(chat_id=chat_id, photo=c["image"], caption=f'{name} is {percent}: {coupon_url}')
            db.gathered.delete_one({"_id": c["_id"]})
        if not sent:
            await update.message.reply_text("No coupons gathered")
    else:
        await update.message.reply_text("You are not in wait mode")


async def get_chat_id(update, context):
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id)

async def register_fuel_notifications(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.fuel
    chat_id = update.effective_chat.id
    if db.registered.find_one({"_id": chat_id}) == None:
        db.registered.insert_one({"_id": chat_id})
        await update.message.reply_text("You will receive notifications about fuel prices")
    else:
        await update.message.reply_text("You are already registered")

async def unregister_fuel_notifications(update, context):
    ca = certifi.where()
    client = pymongo.MongoClient(os.environ.get("MONGODB_ACCESS"), tlsCAFile=ca)
    db = client.fuel
    chat_id = update.effective_chat.id
    if db.registered.find_one({"_id": chat_id}) == None:
        await update.message.reply_text("You are not registered")
    else:
        db.registered.delete_one({"_id": chat_id})
        await update.message.reply_text("You will not receive notifications about fuel prices")


async def echo(update, context):
    """Echo the user message."""
    await update.message.reply_text(update.effective_message.text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    # basic commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stopbot', stop_bot))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('alertlist', alert_list))
    application.add_handler(CommandHandler('chatid', get_chat_id))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    # movie commands
    application.add_handler(CommandHandler('moviealert', movie_alert))
    application.add_handler(CommandHandler('clearmoviealerts', clear_movie_alerts))
    application.add_handler(CommandHandler('deletealert', delete_alert))
    application.add_handler(CommandHandler('moviealertlist', movie_alert_list))

    # fuel commands
    application.add_handler(CommandHandler("fuelcosts", register_fuel_notifications))
    application.add_handler(CommandHandler("unregisterfuelnotifications", unregister_fuel_notifications))


    # coupons commands
    application.add_handler(CommandHandler('coupons', register_coupons))
    application.add_handler(CommandHandler('unregistercoupons', unregister_coupons))
    application.add_handler(CommandHandler('waitcoupons', wait_coupons))
    application.add_handler(CommandHandler('exitwaitcoupons', exit_wait_coupons))





    
    application.run_polling()