from typing import Optional
from fastapi import FastAPI, File, UploadFile
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from psycopg2 import connect
from os import getenv
import shutil

from typing import Annotated
from fastapi import Form

from sqlmodel import SQLModel, create_engine, Session, Field

class FileRegister(SQLModel, table=True):
    __tablename__ = "arquivos"
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    conteudo: bytes


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI( upload_max_size=1073741824, )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/files/")
async def create_file(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()],
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }
    

@app.post("/salvar")
async def salvar(request: Request):
    try:
        # Obter dados do corpo da requisição
        data = await request.form()
        nome, conteudo = data["nome"], data["conteudo"]
        conn = connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port="5432",
        )

        cursor = conn.cursor()

        # Inserir dados na tabela
        cursor.execute(
            """
            INSERT INTO arquivos (nome, conteudo)
            VALUES (%s, %s)
            """,
            (nome, conteudo),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return HTMLResponse(
            """
            <h1>Dados salvos com sucesso!</h1>
            <p>Nome: {}</p>
            <p>Conteúdo: {}</p>
            """.format(
                nome, conteudo
            )
        )

    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao salvar dados: {e}</h1>")


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
        '''
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
        '''
        cursor.execute(
                """
                INSERT INTO arquivos (nome, conteudo)
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
            """.format(
                file.filename, file.content_type
            )
        )

    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao receber arquivo: {e}</h1>")


@app.post("/uploadfile")
async def uploadfile(file: UploadFile = File(...)):
    # Ler o conteúdo do arquivo
    contents_file = await file.read()
    engine = create_engine(f"postgresql+asyncpg://{user}:{password}@{host}/{database}")
    
    # Criar uma nova sessão do banco de dados
    with Session(engine) as session:
        # Criar um novo objeto File com o nome e o conteúdo do arquivo
        new_file = FileRegister(nome=file.filename, conteudo=contents_file)
        
        # Adicionar o novo objeto ao banco de dados
        session.add(new_file)
        session.commit()
        session.refresh(new_file)
    
    return {"file uploaded": file.filename}
