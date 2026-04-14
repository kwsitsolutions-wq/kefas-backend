import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# --- ARCANO KEFAS: ENGINE v2.6 (PAID PRODUCTION) ---
app = FastAPI(title="Kefas High-End Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diccionario de seguridad por IP (Bloqueo de 2 minutos)
last_request_time = {}

class Lead(BaseModel):
    nombre_empresa: str
    representante: str
    sector: str
    whatsapp: str
    email: str
    vision_proyecto: str
    links_cliente: str = ""

@app.get("/")
async def root():
    return {"status": "Arcano Kefas Engine is Running"}

@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    # --- 1. SEGURIDAD DE ACCESO (120 SEGUNDOS) ---
    client_ip = request.client.host
    current_time = time.time()
    TIEMPO_BLOQUEO = 120 
    
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < TIEMPO_BLOQUEO:
            tiempo_restante = int(TIEMPO_BLOQUEO - (current_time - last_request_time[client_ip]))
            raise HTTPException(
                status_code=429, 
                detail=f"Seguridad activa. Espera {tiempo_restante} segundos."
            )
    
    last_request_time[client_ip] = current_time

    # --- 2. MOTOR DE INTELIGENCIA ARTIFICIAL (PAID TIER) ---
    blueprint_ia = "PENDIENTE: Revisión manual requerida por alta demanda."
    
    try:
        # Forzamos la versión v1 de producción para evitar errores 404
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
            http_options={'api_version': 'v1'}
        )
        
        prompt = f"""
        Actúa como Director de Arte Senior. Genera Ficha Técnica y 2 Prompts de Imagen (A y B).
        Empresa: {datos.nombre_empresa}. Sector: {datos.sector}. Visión: {datos.vision_proyecto}.
        Referencias: {datos.links_cliente}
        """
        
        # Usamos el modelo estable que Google garantiza para el plan de pago
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        blueprint_ia = response.text
        
    except Exception as e:
        print(f"Log: Fallo en IA (pero guardando datos): {e}")

    # --- 3. PERSISTENCIA EN HOSTINGER ---
    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor()
        
        sql = """INSERT INTO prospectos 
                 (nombre_empresa, representante, sector, whatsapp, email, vision_proyecto, links_cliente, analisis_ia) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        valores = (
            datos.nombre_empresa, datos.representante, datos.sector, 
            datos.whatsapp, datos.email, datos.vision_proyecto, 
            datos.links_cliente, blueprint_ia
        )
        
        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        conexion.close()
        
    except Exception as db_e:
        print(f"Log: Fallo en DB: {db_e}")
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos.")

    return {
        "status": "success", 
        "ia_status": "completado" if "PENDIENTE" not in blueprint_ia else "pendiente"
    }
