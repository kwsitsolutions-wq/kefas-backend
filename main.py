import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="Arcano Kefas - Resilient Engine v4.0")

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
    return {"status": "Arcano Kefas Engine is Online", "tier": "Paid"}

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

    # --- GEMINI: UN INTENTO, ERROR VISIBLE, NO BLOQUEA EL GUARDADO ---
    blueprint_ia = "PENDIENTE: Error en IA. Revisar manualmente."
    error_ia = None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        prompt_maestro = f"""
        Actúa como Director de Arte Senior. 
        Genera una Guía Maestra para: {datos.nombre_empresa} ({datos.sector}).
        
        PARÁMETROS PSICOLÓGICOS:
        - Estilo: {datos.personalidad_marca}
        - Temperatura: {datos.temperatura_visual}
        - Meta: {datos.objetivo_comunicacion}
        - Visión: {datos.vision_proyecto}

        ENTREGA:
        1. PALETA HEX: 3 colores según {datos.temperatura_visual}.
        2. TIPOGRAFÍA: Pareja ideal para {datos.personalidad_marca}.
        3. SUPER PROMPT (INGLÉS): Midjourney prompt con iluminación cinematográfica, 8k y estilo {datos.personalidad_marca}.
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt_maestro
        )
        blueprint_ia = response.text

    except Exception as e:
        # ❌ Captura el error pero CONTINÚA para guardar en BD
        error_ia = f"ERROR GEMINI: {type(e).__name__} — {str(e)}"
        print(error_ia)

    # =========================================================
    # GUARDADO EN BASE DE DATOS HOSTINGER (siempre se ejecuta)
    # =========================================================
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
        
    except Exception as db_e:
        print(f"Error DB Hostinger: {db_e}")
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos.")

    return {
        "status": "success", 
        "ia_status": "completado" if error_ia is None else "fallido",
        "ia_error": error_ia  # None si todo fue bien, mensaje si falló
    }
