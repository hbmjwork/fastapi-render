from typing import Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from psycopg2 import connect
from os import getenv

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker


app = FastAPI( upload_max_size=1073741824, )
url = str(getenv("P_URL","")).replace("postgres://", "")
user = database = url.split(":")[0] if url else "postgres"
password = url.split("@")[0].replace(database,"").replace(":","") if url else "postgres" 
host = url.split("@")[1].replace(database,"").replace("/","") if url else "localhost"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bd")
async def get_bd():
    return {"u": user, "p": password, "h": host, "url": getenv("P_URL","<VAZIO>")}


@app.get("/arquivos", response_class=HTMLResponse)
async def get_arquivos():
    try:
        # Conectar ao Postgresql
        
        conn = connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port="5432",
        )
             
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM arquivos LIMIT 100")
        data = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        return HTMLResponse(
            """
            <h1>Registro persistido!</h1>
            <p>Nome: {}</p>
            """.format(data)
        )

    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao receber arquivo: {e} - {conn}</h1>")    
    

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        # Conectar ao Postgresql
        
        conn = connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port="5432",
        )
        contents_file = await file.read()        
        cursor = conn.cursor()
        cursor.execute(
                """
                INSERT INTO public.arquivos (nome, conteudo)
                VALUES (%s, %s)
                """, (file.filename, contents_file),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return HTMLResponse(
            """
            <h1>Arquivo recebido com sucesso!</h1>
            <p>Nome do arquivo: {}</p>
            <p>Tamanho do arquivo: {}</p>
            """.format(file.filename, file.content_type)
        )

    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao receber arquivo: {e} - {conn}</h1>")
