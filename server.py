#!/usr/bin/env python3

from random import randint
from urllib.parse import parse_qs

import socket
import sys
import traceback
import os
import base64
import datetime


def main():
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = int(sys.argv[1])

    # Serve the connection
    connect(HOST, PORT)

# Handle incoming connection
def handler(conn, header):
    method = header[0].split(" ")
    content = []
    length = []

    for info in header:
        if "Content-Type" in info:
            content = info.split(" ")
            continue
        if "Content-Length" in info:
            length = info.split(" ")


    msgSuccess = ""
    msgErr = ""


    try:
        if (method[2] not in "HTTP/1.0") and (method[2] not in "HTTP/1.1"):
            status = "400 Bad Request"
            c_type = "text/plain; charset=UTF-8"
            msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
            raise ValueError("Cannot parse the request")

        if method[1] == "/hello-world":
            if method[0] == "GET":
                with open("./hello-world.html", "r") as f:
                    html = f.read()
                    data = html.replace("__HELLO__", "World")
            
                status = "200 OK"
                c_type = "text/html"
                msgSuccess = renderMessage(status, str(len(data)), None, None, c_type, data)
                writeResponse(conn, msgSuccess)
            elif method[0] == "POST":
                status = "400 Bad Request"     
                c_type = "text/plain; charset=UTF-8"
                msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
                try:
                    if content[1] == "application/x-www-form-urlencoded":
                        name = exctractUrl(header[-1], "name")
                        
                        with open("./hello-world.html", "r") as f:
                            html = f.read()
                            data = html.replace("__HELLO__", str(name))

                        status = "200 OK"
                        c_type = "text/html"
                        msgSuccess = renderMessage(status, str(len(data)), None, None, c_type, data)
                        writeResponse(conn, msgSuccess)
                    else:  
                        raise ValueError("Cannot parse the request")
                        
                except (IndexError, KeyError) as e:
                    raise ValueError("Cannot parse the request")

        elif method[1] == "/style":
            if method[0] == "GET":
                with open("./style.css", "r") as f:
                    css = f.read()
                
                status = "200 OK"
                c_type = "text/css"
                msgSuccess = renderMessage(status, str(len(css)), None, None, c_type, css)
                writeResponse(conn, msgSuccess)

        elif method[1] == "/background":
            if method[0] == "GET":
                with open("./background.jpg", "rb") as f:
                    img = f.read()

                status = "200 OK"
                c_type = "image/jpeg"
                enc = "base64"
                msgSuccess = renderMessage(status, str(len(img)), None, enc, c_type, "")
                msgSuccess = msgSuccess + img
                writeResponse(conn, msgSuccess)
        
        elif "/info" in method[1]:
            if method[0] == "GET":
                query = method[1].split("?")
                data = "No Data"

                try:
                    tipe = exctractUrl(query[1], "type")
                    if tipe == "time":
                        data = "{}".format(datetime.datetime.now())
                    elif tipe == "random":
                        data = "{}".format(randint(111111,999999))
                except (IndexError, ValueError) as e:
                    pass

                status = "200 OK"
                c_type = "text/plain; charset=UTF-8"
                msgSuccess = renderMessage(status, str(len(data)), None, None, c_type, data)
                writeResponse(conn, msgSuccess)

        elif method[1] == "/":
            status = "302 Found"
            loc = "/hello-world"
            msgSuccess = renderMessage(status, None, loc, None, None, None)
            writeResponse(conn, msgSuccess)
        
        else:
            status = "404 Not Found"
            c_type = "text/plain; charset=UTF-8"
            msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
            raise ValueError("URL Not Found")
        
        if (method[0] != "POST") and (method[0] != "GET"):
            status = "501 Not Implemented"
            c_type = "text/plain; charset=UTF-8"
            msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
            raise ValueError("Method not implemented")
            
    except IndexError:
        print(traceback.format_exc())
        return
    
    except ValueError:
        print(traceback.format_exc())
        writeResponse(conn, msgErr)
        return
    
    return
    

def writeResponse(conn, message):
    conn.sendall(message)

def renderMessage(stat, c_length, location, encoding, c_type, data):
    msg = ""
    if stat != None:
        status = "HTTP/1.0 {}\n".format(stat)
        msg = msg + status
    msg = msg + "Connection: close\n"
    if c_length != None:
        content_length = "Content-Length: {}\n".format(c_length)
        msg = msg + content_length
    if location != None:
        loc = "Location: {}\n".format(location)
        msg = msg + loc
    if encoding != None:
        enc = "Content-Transfer-Encoding: {}\n".format(encoding)
        msg = msg + enc
    if c_type != None:
        content_type = "Content-Type: {}\n".format(c_type)
        msg = msg + content_type
    if data != None:
        msg = msg + "\n" + data
    return bytes(msg, "utf-8")

def exctractUrl(url, query):
    return parse_qs(url)[query][0]

def connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()

    try:
        while True:
            try:
                conn, addr = s.accept()
                data = conn.recv(1024).decode("utf-8").replace("\r", "")
                header = data.split("\n")

                handler(conn, header)

                conn.shutdown(socket.SHUT_WR)
                conn.close()
            except UnicodeDecodeError:
                status = "400 Bad Request"
                c_type = "text/plain; charset=UTF-8"
                msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
                writeResponse(conn, msgErr)

    except Exception as e:
        print(traceback.format_exc())
        s.close()

main()