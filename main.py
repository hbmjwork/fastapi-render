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
    engine = create_engine(f"postgresql://{user}:{password}@{host}/{database}")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    arquivos = Table("arquivos", MetaData(), autoload_with=engine)
    with SessionLocal() as session:
        query = session.query(arquivos).all()
        arquivos_html = ""
        for arquivo in query:
            arquivos_html += f"<p>Nome: {arquivo.nome}, Conteúdo: {arquivo.conteudo}</p>"
        
        return f"""
        <html><head><title>Arquivos</title></head>
            <body>
                <h1>Arquivos</h1>
                {arquivos_html}
            </body>
        </html>
        """
    

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
