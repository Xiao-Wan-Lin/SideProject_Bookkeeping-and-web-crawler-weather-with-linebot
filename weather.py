import os
from flask import Flask, request, abort
import requests
import json

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage,ImageSendMessage
)


def MakeAQI(station):
    end_point = "http://opendata.epa.gov.tw/webapi/api/rest/datastore/355000000I-000259?filters=SiteName eq '" + \
        station + "'&sort=SiteName&offset=0&limit=1000"

    data = requests.get(end_point)
    AQImsg = ""

    if data.status_code == 500:
        return "無空氣品質資料"
    else:
        AQIdata = data.json()["result"]["records"][0]
        AQImsg += "空氣品質：" + AQIdata["Status"]
        return AQImsg


def GetWeather(station):

    end_point= " https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization=CWB-B76A6C74-EBCA-443C-9B2C-855111D83979"

    data = requests.get(end_point).json()
    data = data["records"]["location"]

    target_station = "not found"
    for item in data:
        if item["locationName"] == str(station):
            target_station = item
    return target_station


def MakeWeather(station):
    WeatherData = GetWeather(station)
    if WeatherData == "not found":
        return False

    WeatherData = WeatherData["weatherElement"]
    msg = "天氣報告 - " + station
    msg += "\n\n氣溫 = " + WeatherData[3]["elementValue"] + "℃\n" #第三個陣列的值
    msg += "濕度 = " + \
        str(float(WeatherData[4]["elementValue"]) * 100) + "% RH\n"

    msg += MakeAQI(station)
    return msg
    