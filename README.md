# LineChatBot-Fitness-Guru-

นาย ปวณนนท์ พานิช 6510110269 

ที่มาและความสำคัญ
ในปัจจุบัน การดูแลสุขภาพและการออกกำลังกายกลายเป็นสิ่งสำคัญสำหรับหลายๆคน 

อย่างไรก็ตาม ด้วยข้อมูลที่มีอยู่มากมายและแผนการออกกำลังกายที่หลากหลาย การเลือกโปรแกรมการออกกำลังกายที่เหมาะสมกับแต่ละคนอาจเป็นเรื่องยาก จะดีแค่ไหนถ้ามี chatbot ที่สามารถให้คำแนะนำเกี่ยวกับการออกกำลังกายและโภชนาการตามความต้องการของผู้ใช้ 

โดยสามารถกรองข้อมูลและเสนอโปรแกรมที่ตรงกับเป้าหมายสุขภาพและความฟิตของผู้ใช้ได้
ดังนั้นจึงเกิดเป็น Fitness Guru Chatbot ที่จะคอยให้คำแนะนำเกี่ยวกับการออกกำลังกายและโภชนาการที่เหมาะสม โดย LINE ถูกเลือกมาเป็นแพลตฟอร์มในการพัฒนาครั้งนี้ 

เนื่องจากสามารถเข้าถึงผู้ใช้ได้ง่ายและสะดวกสบาย

โครงสร้าง CHATBOT
![image](https://github.com/user-attachments/assets/b9bb82bd-a3a2-49b0-a9b4-22b281d04350)

การตั้งค่าเริ่มต้นและการเริ่มต้นการเชื่อมต่อ
Python lib
bs4 import BeautifulSoup
chromedriver_autoinstaller
flask import Flask, request
googletrans import Translator
json
linebot import LineBotApi, WebhookHandler
linebot.models import TextSendMessage
neo4j import GraphDatabase
numpy as np
pythainlp.corpus import thai_stopwords
pythainlp.tokenize import word_tokenize
requests
selenium import webdriver
sentence_transformers 
import SentenceTransformer, util
sys

NLP Model

sentence-transformers/xlm-r-bert-base-nli-stsb-mean-tokens

Config ngrok

![image](https://github.com/user-attachments/assets/0e04a736-3e68-4f6d-9ade-7fddc52efc12)

Config selenium

![image](https://github.com/user-attachments/assets/01c55993-f352-4f8f-b651-faa256adff5b)

Config line

![image](https://github.com/user-attachments/assets/e4336269-272f-493f-9682-f3822245439a)

ตัวอย่างการทำงาน

![image](https://github.com/user-attachments/assets/a7bf577b-ba2b-4ac9-8b53-413a20cb63ea)
![image](https://github.com/user-attachments/assets/612558a9-4afa-4e80-9af1-f489ca023452)
![image](https://github.com/user-attachments/assets/23bda16f-cecb-4a4e-a343-3c7f95616822)
![image](https://github.com/user-attachments/assets/0e278131-4d3d-4a07-bce9-2d468133e73e)

โอกาสในพัฒนา
Fitness Guru (Chatness) : ยังสามารถเพิ่ม function ได้อีกหลายอย่างที่ทำให้ผู้ใช้สามารถใช้งานได้ครบเครื่องมากกว่านี้

ด้าน webscraper
-เลือกช่วง ราคา จาก ต่ำสุด-สูงสุด
-เลือกประเภค sex,sport,promotion

ด้าน LLMs
-เปลี่ยน LLMs ที่สามารถตอบได้ตรงจุดมากกว่านี้

