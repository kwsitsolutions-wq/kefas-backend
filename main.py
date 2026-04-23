import os
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v5.1
# =========================================================
app = FastAPI(title="Arcano Kefas - Lead Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_request_time = {}

class Lead(BaseModel):
    nombre_empresa: str
    representante: str
    sector: str
    whatsapp: str
    email: str
    vision_proyecto: str
    links_cliente: str = ""
    personalidad_marca: str
    temperatura_visual: str
    objetivo_comunicacion: str

@app.get("/")
async def root():
    return {"status": "Arcano Kefas Backend Online", "routes": ["/procesar-cuestionario (POST)", "/prospectos (GET)"]}

# =========================================================
# 2. RUTA DE CAPTURA (Desde Lovable)
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    client_ip = request.client.host
    current_time = time.time()
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            raise HTTPException(status_code=429, detail="Espera un momento entre envíos.")
    last_request_time[client_ip] = current_time

    blueprint_ia = "Análisis delegado al Gem de Arcano."

    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor()
        sql = """INSERT INTO prospectos 
                 (nombre_empresa, representante, sector, whatsapp, email, 
                  vision_proyecto, personalidad_marca, temperatura_visual, 
                  objetivo_comunicacion, links_cliente, analisis_ia) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        valores = (
            datos.nombre_empresa, datos.representante, datos.sector, 
            datos.whatsapp, datos.email, datos.vision_proyecto,
            datos.personalidad_marca, datos.temperatura_visual, 
            datos.objetivo_comunicacion, datos.links_cliente, blueprint_ia
        )
        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        conexion.close()
        return {"status": "success", "message": "Lead guardado correctamente."}
    except Exception as db_e:
        raise HTTPException(status_code=500, detail="Error de base de datos.")

# =========================================================
# 3. RUTA DE LECTURA (Para alimentar tu Gem)
# =========================================================
@app.get("/prospectos")
async def obtener_prospectos():
    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM prospectos ORDER BY fecha DESC LIMIT 20")
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        return {"status": "success", "prospectos": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al leer prospectos.")
