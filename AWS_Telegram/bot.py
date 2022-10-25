import logging

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pandas as pd
import os
import json
import requests
from flask import Flask, request, Response
import io
import numpy as np 
import matplotlib.pyplot as plt

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def graph(d1,store_id):
    buf = io.BytesIO()
    d1['date'] = pd.to_datetime( d1['date'] )

    cinza = "#787878"
    cor = '#0f89b9'

    fig, ax = plt.subplots(figsize=(8, 4))
    # calculation
    d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
    
    # Título
    fig.suptitle('Sales forecasting: Store {}'.format(store_id), fontsize=14, fontweight='bold', color=cor)
    ax.set_title('Esta loja {} venderá $ {:,.2f} nas próximas 6 semanas'.format(d2['store'].values[0], d2['prediction'].values[0]))

    # Gráfico Linha
    candidato_line = ax.plot(d1['date'], d1['prediction'], label='line', color = cor)

    # Remover grids e eixos
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)

    return buf

def  echo2(update: Update, context: CallbackContext) -> None:
    store_id = update.message.text
    store_id = int(store_id)
    
     # load test dataset
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # merge test dataset + store
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id ]
    # df_test = df_test[df_test['Store'].isin( [8] )]

    # remove closed days
    df_test = df_test[df_test['Open'] != 0]
    df_test = df_test[~df_test['Open'].isnull()]
    df_test = df_test.drop('Id', axis=1)

    # convert do to JSON
    data = json.dumps(df_test.to_dict(orient='records'))

    # API Call
    # url = 'https://rossmannapp.herokuapp.com/rossmann/predict'
    # url = 'http://127.0.0.1:5000/rossmann/predict'
    url = 'http://ec2-3-93-179-152.compute-1.amazonaws.com:5000/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    # calculation
    d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
    # send message

    # imagem
    buf = graph(d1,store_id)
    buf.seek(0)
    #buf=dict(photo=buf)
    update.message.reply_photo(buf)
    buf.close()

    msg = 'Esta loja {} venderá $ {:,.2f} nas próximas 6 semanas'.format(d2['store'].values[0], d2['prediction'].values[0])
    update.message.reply_text(msg) 
    

def  echo(update: Update, context: CallbackContext) -> None:
    store_id = update.message.text
    store_id = int(store_id)
    
     # load test dataset
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # merge test dataset + store
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id ]
    # df_test = df_test[df_test['Store'].isin( [8] )]

    # remove closed days
    df_test = df_test[df_test['Open'] != 0]
    df_test = df_test[~df_test['Open'].isnull()]
    df_test = df_test.drop('Id', axis=1)

    # convert do to JSON
    data = json.dumps(df_test.to_dict(orient='records'))

    # API Call
    # url = 'https://rossmannapp.herokuapp.com/rossmann/predict'
    # url = 'http://127.0.0.1:5000/rossmann/predict'
    url = 'http://ec2-3-93-179-152.compute-1.amazonaws.com:5000/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    # calculation
    d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()
    # send message
    msg = 'Esta loja {} venderá $ {:,.2f} nas próximas 6 semanas'.format(d2['store'].values[0], d2['prediction'].values[0])

    update.message.reply_text(msg) 
    

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5417009768:AAEQcH53n33xoir0POzuCvcInMZT9KJ9Cgk")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    ##
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo2))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()