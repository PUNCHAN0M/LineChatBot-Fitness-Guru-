from neo4j import GraphDatabase
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from sentence_transformers import SentenceTransformer, util
import numpy as np
import requests
import json
from pythainlp.corpus import thai_stopwords
from pythainlp.tokenize import word_tokenize
import sys
sys.path.insert(0, 'chromedriver.exe')
from flask import Flask,request
from bs4 import BeautifulSoup
from selenium import webdriver
import chromedriver_autoinstaller
from googletrans import Translator

quickreply_chat = [
    {
        "type": "action",
        "action": {
            "type": "message",
            "label": "รวมคำสั่ง",
            "text": "/command"
        }
    },
    {
        "type": "action",
        "action": {
            "type": "message",
            "label": "แนะนำ",
            "text": "/แนะนำ"
        }
    },
    {
        "type": "action",
        "action": {
            "type": "message",
            "label": "วิธีการการใช้",
            "text": "/วิธีการ"
        }
    },
    {
        "type": "action",
        "action": {
            "type": "message",
            "label": "ค้นหาสินค้า",
            "text": "/search"
        }
    }
]

model = SentenceTransformer('sentence-transformers/xlm-r-bert-base-nli-stsb-mean-tokens')
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "test")
#ALL Caculate
def compute_response(sentence,uid):
   greeting_vec = model.encode(greeting_corpus, convert_to_tensor=True,normalize_embeddings=True)
   ask_vec = model.encode(sentence, convert_to_tensor=True,normalize_embeddings=True)
   greeting_scores = util.cos_sim(greeting_vec, ask_vec) 
   greeting_score = greeting_scores.cpu()
   greeting_np = greeting_score.numpy()
   max_greeting_score = np.argmax(greeting_np)
   Match_Question = greeting_corpus[max_greeting_score] 
   #conversation_history.append(f"user:{sentence}")
   if greeting_np[np.argmax(greeting_np)] > 0.8 :
        My_cypher = f"MATCH (n:Barista) where n.question ='{Match_Question}' RETURN n.msg_reply as reply"
        my_msg  = neo4j_search(My_cypher)
        my_msg = f"By Neo4j:\n{my_msg}"
   else:
      #ตัดstopwordไทย
      msg = remove_stopwords(sentence) 
      print(f'remove stop-word :{msg}')
      my_msg = get_llama_response(sentence,uid)  
      # create_barista_node(sentence,my_msg)
      my_msg = f"Create by ollama:\n{my_msg}"
   #conversation_history.append(f"bot:{my_msg}")
   print(my_msg)
   return my_msg   
    
#Sub Caculate Ollama
def get_llama_response(prompt,uid):
   OLLAMA_API_URL = "http://localhost:11434/api/generate"
   headers = {
      "Content-Type": "application/json"
   }
   role_prompt = f"""ตอบลูกค้า
   {prompt}
   โดยคำตอบยาวไม่เกิน 20 คำ 
   """
   payload = {
      "model": "supachai/llama-3-typhoon-v1.5",
      "prompt": role_prompt,
      "stream": False
   }
   
   response = requests.post(OLLAMA_API_URL, headers=headers, data=json.dumps(payload))
   
   if response.status_code == 200:
      response_data = response.text
      data = json.loads(response_data)
      return data.get("response", "ขอโทษด้วย ฉันไม่สามารถให้คำตอบนี้ได้")  # Default message if response not found
   else:
      print(f"Failed to get a response: {response.status_code}, {response.text}")
      return "ขอโทษด้วย ฉันไม่สามารถให้คำตอบนี้ได้"

#ALL Neo4j
def run_query(query, parameters=None):
   with GraphDatabase.driver(URI, auth=AUTH) as driver:
       driver.verify_connectivity()
       with driver.session() as session:
           result = session.run(query, parameters)
           return [record for record in result]
   driver.close()
#หาคำามที่ตรงกับneo4j
def neo4j_search(neo_query):
   results = run_query(neo_query)
   # Print results
   for record in results:
       response_msg = record['reply']
   return response_msg 

cypher_query = '''
MATCH (n:Barista) RETURN n.question as question, n.msg_reply as reply;
'''
greeting_corpus = []
greeting_vec = None
results = run_query(cypher_query)
for record in results:
   greeting_corpus.append(record['question'])
greeting_corpus = list(set(greeting_corpus))
print(greeting_corpus)  

#สร้างnode neo4j เมื่อ ollama ตอบ
def create_barista_node(question, reply):
    create_query = f'''
    CREATE (:Barista {{question: '{question}', msg_reply: '{reply}'}})
    '''
    run_query(create_query)
#save หรือ change uid,username
def save_user_info(uid, name):
    query = '''
    MERGE (u:User {uid: $uid})
    SET u.name = $name
    '''
    run_query(query, parameters={'uid': uid, 'name': name})
#เรียกหา User
def get_user_name(uid):
    query = '''
    MATCH (u:User {uid: $uid})
    RETURN u.name AS name
    '''
    result = run_query(query, parameters={'uid': uid})
    return result[0]['name'] if result else None
#save chat_history ของแต่ละ uid
def save_response(uid, answer_text, response_msg):
    query = '''
    MATCH (u:User {uid: $uid})
    CREATE (a:Answer {text: $answer_text})
    CREATE (r:Response {text: $response_msg})
    CREATE (u)-[:useranswer]->(a)
    CREATE (a)-[:response]->(r)
    '''
    parameters = {
        'uid': uid,
        'answer_text': answer_text,
        'response_msg': response_msg
    }
    run_query(query, parameters)

#จัดการ Sentence
def remove_stopwords(text):
    text = f"{text}"
    stopwords = set(thai_stopwords())
    #print(f"text:{text}")
    words = word_tokenize(text, engine="newmm")
    #print(f"words {words}")
    filtered_words = [word for word in words if word not in stopwords]
    #print(f"filter:{filtered_words}")
    return ' '.join(filtered_words)
def translator_th2en(text_th,ls,ll):
    try:
        translator = Translator()
        result = translator.translate(text_th, src=ls, dest=ll)
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return "ขอโทษด้วย ฉันไม่สามารถแปลข้อความนี้ได้"

with open('e:/MiniProjectChatBot/line_chatbot/username_line.txt', 'r') as file:
    lines = file.readlines()
    channel_access_token = lines[0].strip()  
    channel_secret = lines[1].strip()  

text_help="""โปรดเลือกเรื่องที่คุณอยากรู้\n1.แนะนำเกี่ยวกับ Chatbot\n2.วิธีการใช้ Chatbot\n3.ค้นหาอุปกรณ์กีฬาจาก SuperSport"""
text_search="""วิธีการใช้งาน Search\n\nพิมพ์ \n/search:(อุปกรณืกีฬาที่อยากหา)(ราคา) \n***ถ้าหาภาษาไทยไม่เจอให้เขียนเป็นภาษาอังกฤษ \n***ราคาสูงสุดที่ต้องการ\n\nเช่น /search:bag , /search:รองเท้า /search:รองเท้า1000"""
text_how="""วิธีการใช้งาน ChatBot\n\n1.แนะนำตัวเองโดยการพิมพ์ชื่อ \nเช่น ผมชื่อปัน,ฉันชื่อเปา,เราชื่อปาย\n 2.เช็คคำสั่งต่างๆโดายการพิมพิมพ์ /command"""
text_command=f"รวมคำสั่งของ ChatBot ทั้งหมด\n1./command \nเช็คคำสั่งทั้งหมด\n2./help \nเรียกปุ่มลัดในการเรียกและบอกว่าทำอะไรได้บ้าง \n3./แนะนำ \nความสามารถ ChatBot\n4./วิธีการ \nบอกขั้นตอนการทำงานของ ChatBot\n5./search \nบอกวิธีใช้ ChatBot\n6./search:(ชื่ออุปกรณ์)(ราคา)  ค้นหาอุปกรณ์"

app = Flask(__name__)

@app.route("/", methods=['POST'])
def linebot():
   body = request.get_data(as_text=True)                   
   
   try:
      json_data = json.loads(body)                       
      line_bot_api = LineBotApi(channel_access_token)             
      handler = WebhookHandler(channel_secret)                   
      signature = request.headers['X-Line-Signature']     
      handler.handle(body, signature)                     
      msg = json_data['events'][0]['message']['text']     
      tk = json_data['events'][0]['replyToken']  
      uid = json_data['events'][0]['source']['userId']
      
      #QuickReply 
      #เมื่อพิมพ์ /help จะทำงาน ตอนนี้มี 3 อัน 1.แนะนำตัว 2.ขั้นตอน 3.รายการสินค้าแนะนำ
      if "/help" in msg:
         line_bot_api.reply_message(
            tk,
            TextSendMessage(
                  text=text_help
                  ,
                  quick_reply={
                     "items": quickreply_chat
                  }
            )
         )
         save_response(uid, msg, text_help)
      #command ต่างๆ
      if msg == "/command"   :
         line_bot_api.reply_message(tk,TextSendMessage(text=text_command,quick_reply={
                     "items": quickreply_chat
                  }))
         save_response(uid, msg, text_command)
      if msg == "/แนะนำ"   :
         line_bot_api.reply_message(tk,TextSendMessage(text=f"""สวัสดีครับคุณ{get_user_name(uid)} ผมชื่อ Fitness Guru\n\nผมถูกสร้างมาเพื่ออำนวยความสะดวกและตอบคำถามของคุณ{get_user_name(uid)}\n\nคำถามทั้งหมดมาจากคำถามที่เราพบได้บ่อยๆในการออกกำลังกายหรือการเลือกซื้ออุปกรณ์ออกกำลังกาย\n\nรวมถึงยังสามารถแนะนำสินค้าดีๆจาก SupperSport:https://www.supersports.co.th/\nให้คุณ{get_user_name(uid)}ได้อีกด้วย""",quick_reply={
                     "items": quickreply_chat
                  }))
         save_response(uid, msg, f"""สวัสดีครับคุณ{get_user_name(uid)} ผมชื่อ Fitness Guru\n\nผมถูกสร้างมาเพื่ออำนวยความสะดวกและตอบคำถามของคุณ{get_user_name(uid)}\n\nคำถามทั้งหมดมาจากคำถามที่เราพบได้บ่อยๆในการออกกำลังกายหรือการเลือกซื้ออุปกรณ์ออกกำลังกาย\n\nรวมถึงยังสามารถแนะนำสินค้าดีๆจาก SupperSport:https://www.supersports.co.th/\nให้คุณ{get_user_name(uid)}ได้อีกด้วย""")
      elif msg == "/วิธีการ":
         line_bot_api.reply_message(tk,TextSendMessage(text=text_how,quick_reply={
                     "items": quickreply_chat
                  }))
         save_response(uid, msg, text_how)
      elif msg == "/search":
         line_bot_api.reply_message(tk,TextSendMessage(text=text_search,quick_reply={
                     "items": quickreply_chat
                  }))
         save_response(uid, msg, text_search)
      elif "/search:" in msg:
         # Setup Chrome options
         chrome_options = webdriver.ChromeOptions()
         chrome_options.add_argument('--headless')  # Ensure GUI is off
         chrome_options.add_argument('--no-sandbox')
         chrome_options.add_argument('--disable-dev-shm-usage')
         # Automatically install chromedriver
         chromedriver_autoinstaller.install()
         #webscrapper
         search_text = msg.split("/search:")[-1].strip()
         print(f"Received message: {msg}")

         #แปลงเป็น th-eng
         if search_text:  # Check if search_text is not empty
            print(f"search_text message: {search_text}")
            # แยกชื่อสินค้าและราคา
            search_rate_prince = ''.join(filter(lambda x: x.isdigit(), search_text))
            print(f"rate price bf :{search_rate_prince}")
            if search_rate_prince == "":
               search_rate_prince = int(1000000)
            else:
               search_rate_prince = int(search_rate_prince)
            print(f"rate price after:{search_rate_prince}")
            # ลบตัวเลขออกจากชื่อ
            search_name = ''.join(filter(lambda x: not x.isdigit(), search_text))
            search_name_old =search_name
            search_name = translator_th2en(search_name,"th","en")
            print(f'text-convert: {search_name}')
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(f"https://www.supersports.co.th/th/search/{search_name}")  # Open the URL
            print(search_name)
            html = driver.page_source
            driver.quit()  # Close the driver after use
            mysoup = BeautifulSoup(html, "html.parser")
            product_cards = mysoup.find_all('div', class_='flip-card-front')
            product_info_list = []
            product_info_list_new = []
            idx_new=0
            # ดึงข้อมูล
            for card in product_cards:
               title = card.find('a', class_='sliderDesc')  # Assuming product title is in <a> tag with class 'sliderDesc'
               price = card.find('h4')  # Assuming price is in <h4> tag
               link = card.find('a', class_='sliderDesc')['href']        
               product_info = [title.text.strip() if title else 'N/A', price.text.strip() if price else 'N/A',f"Link: https://www.supersports.co.th/{link}"]
               product_info_list.append(product_info)
            # print("เก่า",product_info_list)

            # เรียงลำดับสินค้าแนะนำ
            for idx, item in enumerate(product_info_list, start=1):
               title, price_str, link = item
               price_num = int(price_str.replace('฿', '').replace(',', ''))  # Convert price to an integer

               if price_num <= search_rate_prince:
                  # print("ok")
                  idx_new+=1
                  product_info_new = f"{idx_new}. {title}: {price_str}\n{link}"
                  product_info_list_new.append(product_info_new)
               # else:
                  # print("over")
            # print("ใหม่",product_info_list_new)

            search_name = translator_th2en(search_name,"en","th") #แปลงกลับเป็นไทย
            # showแค่ 10 อันดับสินค้า
            if product_info_list_new:
               response_text = f"{search_name_old} แนะนำ 10 อันดับ จาก SuperSport:\n" + "\n".join(product_info_list_new[:10])
            # ไม่มีใรรายการ
            else:
               if search_rate_prince == 1000000:
                  search_rate_prince = "ไม่ระบุราคา"
               else:
                  search_rate_prince+"บาท"
               response_text = f"ขออภัยด้วยครับคุณลูกค้าเนื่องจาก \n\nสินค้าชื่อ: {search_name_old} ราคา: {search_rate_prince} \nไม่ได้มีอยู่ในรายการ หรือ ช่วงราคาที่คุณตั้งต่ำเกินกว่าสินค้าที่เรามี \n\nกรุณาลอง /search ค้นหาอุปกรณ์ที่ต้องการอีกครั้ง"
            line_bot_api.reply_message(tk, TextSendMessage(text=response_text))
            save_response(uid, msg, response_text)
         else:
            line_bot_api.reply_message(tk, TextSendMessage(text="โปรดระบุชื่อสินค้าที่คุณต้องการค้นหา"))
            save_response(uid, msg, "โปรดระบุชื่อสินค้าที่คุณต้องการค้นหา")
         
         

      #recognize name
      #1.user ถามชื่อ hisself
      if "ชื่อ" and "อะไร" in msg:
         user = get_user_name(uid)
         if user:
            line_bot_api.reply_message(tk,TextSendMessage(text=f"สวัสดีครับคุณ{user}"))
            save_response(uid, msg, f"สวัสดีครับคุณ{user}")
         else :
            line_bot_api.reply_message(tk,TextSendMessage(text=f"โปรดระบุชื่อของผู้ใช้ เช่น ผมชื่อ{user}"))
            save_response(uid, msg, f"โปรดระบุชื่อของผู้ใช้ เช่น ผมชื่อ{user}")

      #2.user introduce himself 
      elif "ชื่อ" in msg:
         name = msg.split("ชื่อ")[-1].strip()
         if name:
            save_user_info(uid,name)
            line_bot_api.reply_message(tk,TextSendMessage(text=f"สวัสดีครับคุณ{name}"))
            save_response(uid, msg, f"สวัสดีครับคุณ{name}")
         else:
            line_bot_api.reply_message(tk,TextSendMessage(text=f"โปรดระบุชื่อของผู้ใช้ เช่น ผมชื่อ{user}"))
            save_response(uid, msg, f"โปรดระบุชื่อของผู้ใช้ เช่น ผมชื่อ{user}") #recognize response

      response_msg = compute_response(msg,uid) #chatbot cacullate

      line_bot_api.reply_message(tk,TextSendMessage(text=response_msg)) #chatbot response user
      save_response(uid, msg, response_msg) #recognize response
      print(msg, tk)                     

   except:
       print(body)                                         
   return 'OK'             

      
if __name__ == '__main__':
   app.run(port=5000)
