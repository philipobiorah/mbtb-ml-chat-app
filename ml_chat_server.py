import pandas as pd
import numpy as np
import re

import socket 
import select 
import sys 
from _thread import *

naira_text = pd.read_csv('n_dataset.csv')
naira_text['category_id'] = naira_text['category'].factorize()[0]
category_id_df = naira_text[['category', 'category_id']].drop_duplicates().sort_values('category_id')
category_to_id = dict(category_id_df.values)
id_to_category = dict(category_id_df[['category_id', 'category']].values) 

from sklearn.feature_extraction.text import TfidfVectorizer
tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', encoding='latin-1', ngram_range=(1, 2), stop_words='english')

features = tfidf.fit_transform(naira_text.text).toarray()
labels = naira_text.category_id 

import pickle
filename = 'b1_naira_model.sav'
loaded_model = pickle.load(open(filename, 'rb'))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
# if len(sys.argv) != 3: 
#     print("Correct usage: script, IP address, port number")
#     exit()
# IP_address = str(sys.argv[1])
# Port = int(sys.argv[2])
IP_address = "127.0.0.1"
Port = 12345
server.bind((IP_address, Port))
server.listen(100) 
list_of_clients = [] 
def predictFunc(rawmsg, mbtmlist):
    result = " "
    text_features = tfidf.transform(mbtmlist)
    predictions = loaded_model.predict(text_features)
    for m, predicted in zip(mbtmlist, predictions):
        result = rawmsg + ":" + id_to_category[predicted]
        
#       print('"{}"'.format(rawmsg))
#       print("  - Predicted as: '{}'".format(id_to_category[predicted]))
#       print("")
    return result

def clientthread(conn, addr):
    conn.send("Server: Welcome to our Machine Learning powered chat room".encode()) 
    while True: 
        try: 
            
            mbtmlist = []
            # print("waiting for client..."+str(addr))
            message = conn.recv(1024)
            msg = message.decode("utf-8")
            if len(msg) > 35:
                mbtmlist.append(msg)
                message = predictFunc(msg, mbtmlist)
            else: message = msg    
            if message:
                print("<" + addr[0] + ":" + str(addr[1]) + "> " + message)
                message_to_send = "<" + addr[0] + ":" + str(addr[1]) + "> " + message 
                broadcast(message_to_send.encode(), conn) 
            else:
                print("removing conn")
                remove(conn)
                break
        except: 
            print("exception:"+str(sys.exc_info()))
            break
    print("closing client thread")
def broadcast(message, connection): 
    for client in list_of_clients: 
        if client!=connection: 
            try: 
                client.send(message) 
            except: 
                client.close() 
                print("closing client:"+client)
                remove(client)
def remove(connection): 
    if connection in list_of_clients: 
        list_of_clients.remove(connection) 
while True: 
    conn, addr = server.accept() 
    list_of_clients.append(conn)
    print(addr[0]+ ":" + str(addr[1]) + " connected")
    start_new_thread(clientthread,(conn,addr))
server.close() 