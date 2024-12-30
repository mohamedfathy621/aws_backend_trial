from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import sqlite3
from django.http import JsonResponse
from .models import User
from django.http import HttpResponse
import io
loggedin_users= []
@csrf_exempt
def regist(request):
    if request.method =='POST':
        password=request.POST.get('password')
        username=request.POST.get('username')
        user=User.objects.filter(username=username).first()
        if user:
            return JsonResponse({"error":"user already exists","username":username,"password":password},status=201)
        user=User(username=username,password=password)
        user.save()
        return JsonResponse({"message":"user register successfull"},status=200)

@csrf_exempt
def login(request):
    if request.method =="POST":
        password=request.POST.get('password')
        username=request.POST.get('username')
        user=User.objects.filter(username=username).first()
        if not user:
             return JsonResponse({"error":"user does not exist"},status=201)
        if not user.password == password:
             return JsonResponse({"error":"wrong password"},status=201)
        if username in loggedin_users:
             return JsonResponse({"error":"user is already logged in"},status=201)
        loggedin_users.append(username)
        return JsonResponse({"message":"log in succuessfull","username":username}, status=200)
    
@csrf_exempt
def logout(request):
    if request.method =="POST":
        username=request.POST.get('username')
        loggedin_users.remove(username)
        return JsonResponse({"message":"log out succuessfull","username":username}, status=200)
    
def create_sqlite_connection(username):
    return sqlite3.connect(f'./transformer/databases/{username}', check_same_thread=False)

# Create your views here.
def sayHI(request):
    if request.method =='GET':
        return JsonResponse({"message":"HI"} , status=200)

@csrf_exempt
def csv_col(request):
    if request.method =='POST':
        csv_file= request.FILES['file']
        username= request.POST.get('username',"")
        user=User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"error":"user does not exist"},status=200)
        conn = create_sqlite_connection(username)
        df=pd.read_excel(csv_file, sheet_name=None)
        tables=[]
        cursor = conn.cursor()
        for sheet_name, data in df.items():
            table_name = sheet_name.replace(" ", "_").lower()
            data.to_sql(table_name, conn, index=False, if_exists='replace')
            cursor.execute(f"SELECT * FROM {sheet_name}")
            ret=cursor.fetchall()
            result_df = pd.read_sql_query(f"SELECT * FROM {sheet_name}", conn)
            tables=tables+[[sheet_name,ret,result_df.columns.tolist()]]
            print(f"Sheet '{sheet_name}' has been written to SQLite table '{table_name}'.")
        print(tables)
        conn.close()
        return JsonResponse({"message":tables} , status=200)

@csrf_exempt
def get_Data(request):
    if request.method =='POST':
        query=request.POST.get("query", "")
        username= request.POST.get('username',"")
        user=User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"error":"user does not exist"},status=200)
        conn = create_sqlite_connection(username)
        cursor = conn.cursor()
        query_type = query.strip().split()[0].upper()
        try:
            if query_type == 'SELECT':
                cursor.execute(query)
                result_df = pd.read_sql_query(query, conn)
                message=cursor.fetchall()
                conn.close()
                return JsonResponse({"message":"query succesfull","column":result_df.columns.tolist(),"rows":message,"type":"read"} , status=200)
            else:
                cursor.execute(query)
                conn.commit()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [table[0] for table in cursor.fetchall()]
                dataset = {}
                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = [col[1] for col in cursor.fetchall()]  # PRAGMA table_info returns a tuple
                    cursor.execute(f"SELECT * FROM {table};")
                    rows = cursor.fetchall()
                    dataset[table] = {"columns": columns, "rows": rows}
                conn.close()
                return JsonResponse({"message":'query succesfull',"type":"write","dataset":dataset} , status=200)
        except Exception as error:
            conn.close()
            return JsonResponse({"message":"bad query","error":str(error)} , status=201)
        
@csrf_exempt
def download_sheet(request):
    if request.method =='POST':
        username= request.POST.get('username',"")
        user=User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"error":"user does not exist"},status=200)
        conn = create_sqlite_connection(username)
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(query, conn)
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            for table_name in tables['name']:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                df.to_excel(writer, sheet_name=table_name, index=False)
        conn.close()
        output_buffer.seek(0)
        response = HttpResponse(
                output_buffer,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{username}_data.xlsx"'
        return response

@csrf_exempt
def refresh_sheet(request):
    if request.method =='POST':
        username= request.POST.get('username',"")
        user=User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({"error":"user does not exist"},status=200)
        conn = create_sqlite_connection(username)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        dataset = {}
        for table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = [col[1] for col in cursor.fetchall()]  # PRAGMA table_info returns a tuple
                cursor.execute(f"SELECT * FROM {table};")
                rows = cursor.fetchall()
                dataset[table] = {"columns": columns, "rows": rows}
        conn.close()
        return JsonResponse({"message":'query succesfull',"type":"write","dataset":dataset} , status=200)