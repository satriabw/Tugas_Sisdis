# coding: utf-8

from random import randint
from urllib.parse import parse_qs

import socket
import sys
import json
import traceback
import os
import base64
import yaml
import datetime
import requests
import re

class Route:
    def __init__(self):
        self._route = []

    def route(self, method, path, handler):
        self._route.append({"method": method, "path": path, "handler": handler})
    
    def dispatch(self, path, method):
        pattern = re.compile(r'/api/plusone/[0-9]*[0-9]$')
        match = re.match(pattern, path)
        if match != None:
            path = "/api/plusone/<:digit>"
        for item in self._route:
            if item["path"] == path and item["method"] == method:
                return item["handler"]
        return None
    
    def findPath(self, path):
        for item in self._route:
            if item["path"] == path:
                return True
        return False

route = Route()

class HTTPRequest:
    def __init__(self, request):
        self._raw_request = request
        self._build_header()
        self._build_body()
    
    def _build_header(self):
        raw_head = self._split_request()[0]
        head = raw_head.split("\n")
        
        # Get method, path, and http version
        temp = head[0].split(" ")
        self.header = {
            "method"        : temp[0],
            "path"          : temp[1],
            "http_version"  : temp[2],
        }

        # Get Content-type and Content-length
        for info in head:
            if "Content-Type" in info:
                self.header["content_type"] = info.split(" ")[1]
                continue
            if "Content-Length" in info:
                self.header["content_length"] = info.split(" ")[1]

    def _build_body(self):
        self._raw_body = self._split_request()[1]
    
    def _split_request(self):
        return self._raw_request.decode(
            "utf-8").replace("\r", "").split("\n\n")
    
    def body_json(self):
        return json.loads('[{}]'.format(self._raw_body))
    
    def body_query(self, query):
        return parse_qs(self._raw_body)[query]
    

def validation(func):
    def func_wrapper(conn, request):
        if (request.header["http_version"]  not in "HTTP/1.0") and (request.header["http_version"]  not in "HTTP/1.1"):
            badRequest(conn, request)
        else:
            func(conn, request)
    return func_wrapper

@validation
def getRoot(conn, request):
    debugger = "Hooray getRoot end point is hitted\n"
    print(debugger)
    status = "302 Found"
    loc = "/hello-world"
    c_type = "text/plain; charset=UTF-8"
    data = '302 Found: Location: /hello-world'
    msgSuccess = renderMessage(status, str(21+len(loc)), loc, None, c_type, data)
    writeResponse(conn, msgSuccess)

@validation
def getHelloWorld(conn, request):
    with open("./hello-world.html", "r") as f:
        html = f.read()
        data = html.replace("__HELLO__", "World")

    status = "200 OK"
    c_type = "text/html"
    msgSuccess = renderMessage(status, str(len(data)), None, None, c_type, data)
    writeResponse(conn, msgSuccess) 

@validation
def getStyle(conn, request):
    with open("./style.css", "r") as f:
        css = f.read()
    
    status = "200 OK"
    c_type = "text/css"
    msgSuccess = renderMessage(status, str(len(css)), None, None, c_type, css)
    writeResponse(conn, msgSuccess)

@validation
def getBackground(conn, request):
    with open("./background.jpg", "rb") as f:
        img = f.read()

    status = "200 OK"
    c_type = "image/jpeg"
    enc = "base64"
    msgSuccess = renderMessage(status, str(len(img)), None, enc, c_type, "")
    msgSuccess = msgSuccess + img
    writeResponse(conn, msgSuccess)

@validation
def getSpesifikasi(conn, request):
    with open("./spesifikasi.yaml", "r") as f:
        yaml = f.read()
    
    status = "200 OK"
    c_type = "text/plain; charset=UTF-8"
    msgSuccess = renderMessage(status, str(len(yaml)), None, None, c_type, yaml)
    writeResponse(conn, msgSuccess)

@validation
def getInfo(conn, request):
    query = request.header["path"].split("?")
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

def notFound(conn, request):
    if "/api" in request.header["path"]:
        notFoundJson(conn)
    status = "404 Not Found"
    c_type = "text/plain; charset=UTF-8"
    msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
    writeResponse(conn, msgErr)

def notImplemented(conn, request):
    status = "501 Not Implemented"
    c_type = "text/plain; charset=UTF-8"
    msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
    writeResponse(conn, msgErr)

def badRequest(conn, request):
    if "/api" in request.header["path"]:
        badRequestJson(conn)
    status = "400 Bad Request"
    c_type = "text/plain; charset=UTF-8"
    msgErr = renderMessage(status, str(len(status)), None, None, c_type, status)
    writeResponse(conn, msgErr)

@validation
def postHelloWorld(conn, request):
    debugger = "Hooray postHelloWorld end point is hitted\n"
    print(debugger)
    try:
        if request.header["content_type"] == "application/x-www-form-urlencoded":
            name = request.body_query("name")[0]
            
            with open("./hello-world.html", "r") as f:
                html = f.read()
                data = html.replace("__HELLO__", str(name))

            status = "200 OK"
            c_type = "text/html; charset=UTF-8"
            msgSuccess = renderMessage(status, str(len(data)), None, None, c_type, data)
            writeResponse(conn, msgSuccess)
        else:  
            raise ValueError("Cannot parse the request")
            
    except (IndexError, KeyError, ValueError) as e:
        badRequest(conn, request)

def validateHelloAPI(func):
    def func_wrapper(conn, request):
        if (request.header["http_version"]  not in "HTTP/1.0") and (request.header["http_version"]  not in "HTTP/1.1"):
            badRequestJson(conn)     
        elif request.header["method"] != "POST":
            methodNotAllowedJson(conn)
        else:
            func(conn, request)
    return func_wrapper

@validateHelloAPI
def helloAPI(conn, request):    
    req = requests.get(url='http://172.22.0.222:5000')
    data = req.json()
    current_visit = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    
    try:
        name = request.body_json()[0]["request"]
        count = getCounter() + 1
        writeCounter(count)
        res = "Good {}, {}".format(data["state"], name)
        json_http_ok(conn, count=count, currentvisit=current_visit, response=res)
    except KeyError:
        badRequestJson(conn, "'request' is a required property")

@validation
def plusOneAPI(conn, request):
    val = int(request.header["path"].split("/")[-1])
    json_http_ok(conn, plusoneret=val+1)

def getTime(t_raw):
    t = datetime.datetime.strptime(t_raw, "%Y-%m-%d %H:%M:%S")
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def getCounter():
    with open('counter.json', 'r') as json_file:  
        data = json.load(json_file)
    return data["count"]

def writeCounter(c):
    count = {"count": c}
    with open('counter.json', 'w') as json_file:  
        data = json.dump(count, json_file)

def getApiVersion():
    with open('./spesifikasi.yaml', 'r') as f:
        doc = yaml.load(f)
    return doc["info"]["version"]

def notFoundJson(conn):
    detail = "The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again."
    status = "404"
    title = "Not Found"
    json_http_error(conn, detail, status, title)

def methodNotAllowedJson(conn):
    detail = "Method is not allowed, please use POST method"
    status = "405"
    title = "Method Not Allowed"
    json_http_error(conn, detail, status, title)

def badRequestJson(conn, d):
    detail = d
    status = "400"
    title = "Bad Request"
    json_http_error(conn, detail, status, title)
    
def json_http_ok(conn, **kwargs):
    res_dict = {'apiversion': getApiVersion()}
    for key, value in kwargs.items():
        res_dict[key] = value
    data = json.dumps(res_dict)
    # Build Response
    status = "200 OK"
    c_type = "application/json; charset=UTF-8"
    msgErr = renderMessage(status, str(len(data)), None, None, c_type, data)
    writeResponse(conn, msgErr)

def json_http_error(conn, detail, status, title):
    res_dict = {'detail': detail, 'status': status, 'title': title}
    data = json.dumps(res_dict)
    status = "{} {}".format(status, title)
    c_type = "application/json; charset=UTF-8"
    msgErr = renderMessage(status, str(len(data)), None, None, c_type, data)
    writeResponse(conn, msgErr)
    
def main():
    # HOST = socket.gethostbyname(socket.gethostname())
    HOST = "0.0.0.0"
    PORT = int(sys.argv[1])

    #Get method
    route.route("GET", "/", getRoot)
    route.route("GET", "/hello-world", getHelloWorld)
    route.route("GET", "/style", getStyle)
    route.route("GET", "/background", getBackground)
    route.route("GET", "/info", getInfo)
    route.route("GET", "/api/hello", helloAPI)
    route.route("GET", "/api/plusone/<:digit>", plusOneAPI)
    route.route("GET", "/api/spesifikasi.yaml", getSpesifikasi)

    #Post Method
    route.route("POST", "/api/hello", helloAPI)
    route.route("POST", "/hello-world", postHelloWorld)

    # PUT
    route.route("PUT", "/api/hello", helloAPI)

    #PATCH
    route.route("PATCH", "/api/hello", helloAPI)

    #DELETE
    route.route("DELETE", "/api/hello", helloAPI)

    #HEAD
    route.route("HEAD", "/api/hello", helloAPI)

    # Serve the connection
    connect(HOST, PORT)

def handler(conn, req):
    try:
        debugger = "=== Got Request ===\n{}\n===Got Header====\n{}\n".format(req._raw_request, req.header)
        print(debugger)
        route.dispatch(cleanURL(req.header["path"]), req.header["method"])(conn, req)
    except TypeError as e:
        print(traceback.format_exc())
        if route.findPath(cleanURL(req.header["path"])):
            notImplemented(conn, req)
            return
        notFound(conn, req)
        return

def cleanURL(url):
    return url.split("?")[0]
    
def writeResponse(conn, message):
    debugger = "=== Got Message ===\n{}\n".format(message)
    print(debugger)
    conn.sendall(message)

def renderMessage(stat, c_length, location, encoding, c_type, data):
    msg = ""
    if stat != None:
        status = "HTTP/1.1 {}\r\n".format(stat)
        msg = msg + status
    msg = msg + "Connection: close\r\n"
    if c_length != None:
        content_length = "Content-Length: {}\r\n".format(c_length)
        msg = msg + content_length
    if location != None:
        loc = "Location: {}\r\n".format(location)
        msg = msg + loc
    if encoding != None:
        enc = "Content-Transfer-Encoding: {}\r\n".format(encoding)
        msg = msg + enc
    if c_type != None:
        content_type = "Content-Type: {}\r\n".format(c_type)
        msg = msg + content_type
    if data != None:
        msg = msg + "\r\n" + data
    return bytes(msg, "utf-8")

def exctractUrl(url, query):
    return parse_qs(url)[query][0]

def connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()

    while True:
        try:
            conn, addr = s.accept()

            data = conn.recv(1024)
            req = HTTPRequest(data)
            handler(conn, req)

            conn.shutdown(socket.SHUT_WR)
            conn.close()
        except Exception:
            print(traceback.format_exc())
            continue
                

main()