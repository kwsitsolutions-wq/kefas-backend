import os
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v5.0 (Cero Costos)
# =========================================================
app = FastAPI(title="Arcano Kefas - Lead Capture Only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protección IP para evitar spam en tu base de datos
last_request_time = {}

# Esquema de datos (Sincronizado con Lovable y tu base de datos)
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
    return {"status": "Arcano Kefas Backend is Online", "mode": "Capture Only"}

# =========================================================
# 2. CAPTURA Y GUARDADO (SIN GASTAR TOKENS DE IA)
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    
    # --- SEGURIDAD: Límite de 120s ---
    client_ip = request.client.host
    current_time = time.time()
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            restante = int(120 - (current_time - last_request_time[client_ip]))
            raise HTTPException(status_code=429, detail=f"Espera {restante}s.")
    last_request_time[client_ip] = current_time

    # Llenamos la columna 12 (analisis_ia) con un mensaje indicando que se usa el Gem
    blueprint_ia = "Análisis delegado al Gem de Arcano."

    # =========================================================
    # 3. GUARDADO DIRECTO EN BASE DE DATOS HOSTINGER
    # =========================================================
    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor()
        
        # Insertamos en las 11 columnas que configuraste
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
        
    except Exception as db_e:
        print(f"Error DB Hostinger: {db_e}")
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos.")

    return {
        "status": "success", 
        "ia_status": "delegado_al_gem",
        "message": "Lead guardado correctamente."
    }
