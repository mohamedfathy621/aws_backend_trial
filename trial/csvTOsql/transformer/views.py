from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import sqlite3
from django.http import JsonResponse
from django.contrib.sessions.models import Session
SESSION_DB_CONNS = {}
def create_sqlite_connection():
    return sqlite3.connect(':memory:', check_same_thread=False)
def get_session_db(request):
    session_key = request.session[session_key]
    if not session_key:
        # If no session exists, create one
        request.session.create()  # This will create a session and assign it a session_key
        session_key = request.session.session_key
        request.session[session_key]=session_key
    if session_key not in SESSION_DB_CONNS:
         conn = sqlite3.connect(f'./transformer/databases/{session_key}.db', check_same_thread=False)
         SESSION_DB_CONNS[session_key] = conn
    return SESSION_DB_CONNS[session_key]

# Create your views here.
def sayHI(request):
    if request.method =='GET':
        return JsonResponse({"message":"HI"} , status=200)
@csrf_exempt
def csv_col(request):
    if request.method =='POST':
        conn = get_session_db(request)
        csv_file= request.FILES['file']
        df=pd.read_excel(csv_file, sheet_name=None)
        tables=[]
        cursor = conn.cursor()
        for sheet_name, data in df.items():
            table_name = sheet_name.replace(" ", "_").lower()
            data.to_sql(table_name, conn, index=False, if_exists='replace')
            cursor.execute(f"SELECT * FROM {sheet_name}")
            ret=cursor.fetchall()
            result_df = pd.read_sql_query(f"SELECT * FROM book1", conn)
            tables=tables+[[sheet_name,ret,result_df.columns.tolist()]]
            print(f"Sheet '{sheet_name}' has been written to SQLite table '{table_name}'.")
        print(tables)
        return JsonResponse({"message":tables} , status=200)
@csrf_exempt
def get_Data(request):
    if request.method =='POST':
        conn = get_session_db(request)
        query=request.POST.get("query", "")
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            result_df = pd.read_sql_query(query, conn)
            return JsonResponse({"message":cursor.fetchall(),"column":result_df.columns.tolist()} , status=200)
        except Exception as error:
            return JsonResponse({"message":"bad query","error":str(error)} , status=201)
       