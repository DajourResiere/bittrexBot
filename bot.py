#!/usr/bin/env python
__author__ = 'zaphodbeeblebrox'

# TODO
# add the accrual percentage
# figure out how the hell Wilde's assessing volume
# note the code
# make it more readable

import time
import datetime
import re
import json
from modules import bittrex

with open("config/botConfig.json", "r") as fin:
    config = json.load(fin)

apiKey = str(config['apiKey'])
apiSecret = str(config['apiSecret'])
trade = config['trade']
currency = config['currency']
valuePercent = config['valuePercent']
volumePercent = config['volumePercent']
extCoinBalance = config['extCoinBalance']
checkInterval = config['checkInterval']

api = bittrex.bittrex(apiKey, apiSecret)
market = '{0}-{1}'.format(trade, currency)


def get_orders(market):
    orderInventory = api.getopenorders(market)
    return orderInventory

def get_number_of_sell_orders(orderInventory):
    orderCount = 0
    for order in orderInventory:
        if (order['OrderType'] == 'LIMIT_SELL'):
            orderCount = orderCount + 1
    return orderCount

def kill_sell_order(orderInventory, orders):
    ordersToKill = orders - 1
    for sellOrder in orderInventory:
        while (ordersToKill >  0):
            api.cancel(sellOrder['OrderUuid'])
            ordersToKill = ordersToKill - 1

def control_sell_orders(orderInventory):
    orders = get_number_of_sell_orders(orderInventory)
    if (orders == 1):
        return 1
    elif (orders > 1):
        kill_sell_order(orderInventory, orders)
    else:
        return 0

def get_number_of_buy_orders(orderInventory):
    orderCount = 0
    for order in orderInventory:
        if (order['OrderType'] == 'LIMIT_BUY'):
            orderCount = orderCount + 1
    return orderCount

def kill_buy_order(orderInventory, orders):
    ordersToKill = orders - 1
    for buyOrder in orderInventory:
        while (ordersToKill >  0):
            api.cancel(buyOrder['OrderUuid'])
            ordersToKill = ordersToKill - 1

def control_buy_orders(orderInventory):
    orders = get_number_of_buy_orders(orderInventory)
    if (orders == 1):
        return 1
    elif (orders > 1):
        kill_buy_orders(orderInventory, orders)
    else:
        return 0

def get_last_order_value(market):
    lastOrder = api.getorderhistory(market, 0)
    return lastOrder[0]['PricePerUnit']

def calculate_sell_order_value(orderHistory, valuePercent):
    newSellValue = round((orderHistory * (valuePercent * .01)) + orderHistory, 8)
    return newSellValue

def calculate_sell_order_volume(orderVolume, volumePercent):
    newSellVolume = round(orderVolume * (volumePercent * .01), 8)
    return newSellVolume

def calculate_buy_order_value(orderValueHistory, valuePercent):
    newBuyValue = round(orderValueHistory - (orderValueHistory * (valuePercent * .01)), 8)
    return newBuyValue

def calculate_buy_order_volume(orderVolume, volumePercent):
    newBuyVolume = round((orderVolume * (volumePercent * .01)), 8)
    return newBuyVolume

def check_for_recent_transaction(market, orderInventory):
    lastOrder = api.getorderhistory(market, 0)
    lastOrder = lastOrder[0]['Closed']
    orderTime = re.sub('T', ' ', lastOrder)
    orderTime = datetime.datetime.strptime(orderTime,  "%Y-%m-%d %H:%M:%S.%f")
    currentTime = datetime.datetime.utcnow()
    difference = currentTime - orderTime

    if difference.total_seconds() < checkInterval:
        reset_orders(orderInventory)
        time.sleep(5)


def reset_orders(orderInventory):
    for order in orderInventory:
        print "Removing order: " + order['OrderUuid']
        api.cancel(order['OrderUuid'])


while True:
    orderInventory = get_orders(market)
    check_for_recent_transaction(market, orderInventory)
    sellControl = control_sell_orders(orderInventory)
    buyControl = control_buy_orders(orderInventory)
    orderValueHistory = get_last_order_value(market)
    orderVolume = api.getbalance(currency)['Available'] + extCoinBalance

    if (sellControl == 0):
        newSellValue = calculate_sell_order_value(orderValueHistory, valuePercent)
        newSellVolume = calculate_sell_order_volume(orderVolume, volumePercent)
        print "Currency: " + currency
        print "Sell Value: " + str(newSellValue)
        print "Sell volume: " + str(newSellVolume)
        result = api.selllimit(market, newSellVolume, newSellValue)
        print result

    if (buyControl == 0):
        newBuyValue = calculate_buy_order_value(orderValueHistory, valuePercent)
        newBuyVolume = calculate_buy_order_volume(orderVolume, volumePercent)
        print "Currency: " + currency
        print "Buy Value: " + str(newBuyValue)
        print "Buy Volume: " + str(newBuyVolume)
        result = api.buylimit(market, newBuyVolume, newBuyValue)
        print result
    time.sleep(checkInterval)