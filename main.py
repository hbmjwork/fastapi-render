from typing import Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from psycopg2 import connect
from os import getenv
import shutil

app = FastAPI( upload_max_size=1073741824, )

url = str(getenv("P_URL","")).replace("postgres://", "")
user = database = url.split(":")[0] if url else "postgres"
password = url.split("@")[0].replace(database,"").replace(":","") if url else "postgres" 
host = url.split("@")[1].replace(database,"").replace("/","") if url else "localhost"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/bd")
async def root():
    return {"u": user, "p": password, "h": host, "url": getenv("P_URL","<VAZIO>")}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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

        # Salvar arquivo no servidor
        with open(f"uploads/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ler arquivo e inserir no Postgresql
        with open(f"uploads/{file.filename}", "rb") as f:
            cursor.execute(
                """
                INSERT INTO arquivos (nome, conteudo)
                VALUES (%s, %s)
                """,
                (file.filename, f.read()),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return HTMLResponse(
            """
            <h1>Arquivo recebido com sucesso!</h1>
            <p>Nome do arquivo: {}</p>
            <p>Tamanho do arquivo: {}</p>
            """.format(
                file.filename, file.content_type
            )
        )

    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao receber arquivo: {e}</h1>")
