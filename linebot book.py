from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import time
import os.path
import sys

import weather as w

import sqlite3

import numpy as np

app = Flask(__name__)

_token=''
_secret=''
line_bot_api = LineBotApi(_token)
handler = WebhookHandler(_secret)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature he
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    pass
    return 'OK'
pass

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
        if event.message.text.find("/addCost")==0:
            result=inputAddRecord(event.message.text,event.source.user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=result))
        elif event.message.text.find("/deleteCost")==0:
            result=deleteCostRecord(event.message.text,event.source.user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=result))
        elif event.message.text == "/all":
            result=getRecord(event.message.text,event.source.user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=result))
        elif event.message.text.find("天氣")==0:
            cmd=event.message.text.split(" ")
            station=cmd[1]
            WeatherMsg=w.MakeWeather(station)
            if not WeatherMsg:
                WeatherMsg = "沒這個氣象站哦!請重新輸入"
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=WeatherMsg))
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="歡迎使用記帳Gε٩(๑> ₃ <)۶з\n輸入使用方法:\n1)新增紀錄:/addCost 項目 金額\n2)刪除紀錄:/deleteCost 時間 項目 金額\n刪除紀錄可以先查詢所有紀錄再刪除喔! \n3)查詢紀錄:/all\n4)查詢天氣:天氣 地區\n\n有空格請記得要輸入!"))
        pass
pass

def isInputCostInt(Input_data):
    
    #:param Input_data: 給於 /inputCostRecord 的金額參數是否為int
    try:
        getCost = int(Input_data[2])
        return True
    except ValueError:
        return False
pass


def inputAddRecord(msg,user_id): #這邊變數是輸入的訊息=記帳,會return結果到handle_message
    timeStr = time.strftime('%Y/%m/%d', time.localtime(time.time()))
    
    dailyCost=msg[8:].replace('\n',' ') #replace(舊,新)是將\n轉換成空白 /addCost 吃飯 100
    try:
       # 判斷輸入的第二位參數一定要是Int以及list的數量一定要等於三個，如果沒有也會請你重新輸入正確格式
       #split是用空格分開兩個str
        if (isInputCostInt(Input_data = dailyCost.split(' ')) is True) and (len(dailyCost.split(' ')) == 3):
            type_=dailyCost.split(' ')[1]
            money=dailyCost.split(' ')[2]
            
            connect = sqlite3.connect("count.db")
            cursor = connect.cursor()
            sql="INSERT INTO count(id,time,type,money) values('%s','%s','%s','%s')" % (user_id,timeStr,type_,money)
            cursor.execute(sql)
            connect.commit()
            cursor.close()
            connect.close()
          
            return "[新增紀錄][{}] \n花費項目:{},金額:{}".format(timeStr, dailyCost.split(' ')[1], dailyCost.split(' ')[2])
        else:
              
            return "你輸入的格式有錯誤喔! \n請輸入:/addCost 項目 金錢 \n例如:/addCost 吃飯 300"
        
    except Exception as e:
        return "你輸入的格式有錯誤喔! \n請輸入:/addCost 項目 金錢 \n例如:/addCost 吃飯 30"
pass

def deleteCostRecord(msg,user_id):
       
       total_list=getTotalCostList(user_id)
       
       if len(total_list) != 0:
            deleteCost = msg[11:].replace('\n',' ')
            isDeleteRecord=False
            
            time = deleteCost.split(' ')[1]
            type_ = deleteCost.split(' ')[2]
            money = deleteCost.split(' ')[3]
            
            count = 0
            
            for deleteRecord in total_list:
                if (deleteRecord[0]==time and deleteRecord[1]==type_ and deleteRecord[2]==money):
                    #total_list是array，將array裡的資料刪掉
                    total_list=np.delete(total_list,count)  
                    isDeleteRecord=True
            count+=1
            
            if isDeleteRecord is True:
                connect = sqlite3.connect("count.db")
                cursor = connect.cursor()
                sql="TRUNCATE FROM count WHERE id='%s' AND time='%s' AND type='%s' AND money='%s'" % (user_id,time,type_,money)
                cursor.execute(sql)
                connect.commit()
                cursor.close()
                connect.close()
          
                update_total_list=getTotalCostList()
                
                return "[刪除項目][{}]\n%s".format(deleteCost) % '刪除後的所有的紀錄:\n%s' % '\n'.join('%s' % a for a in total_list)
            else:
                return "未找到你要刪除的紀錄:{}".format(deleteCost)
           
            
       else:
            return "暫時還沒有記錄喔"



def getTotalCostList(user_id):
    connect = sqlite3.connect("count.db")
    cursor = connect.cursor()
    sql="SELECT time, type, money FROM count WHERE id='%s'" % (user_id)
    cursor.execute(sql)
    connect.commit()
    
    rows = cursor.fetchall()
    
    row = np.array(rows)
    
    cursor.close()
    connect.close()
            
    return row


def getRecord(total_list,user_id):
    total_list=getTotalCostList(user_id)
    
    if len(total_list) != 0:
        return ('所有的花費:\n%s' % '\n'.join('%s' % a for a in total_list))
  
    else:
        return "暫時還沒有記錄喔"
        
pass

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=10080)
