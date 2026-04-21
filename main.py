import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# --- ARCANO KEFAS: ENGINE v3.5 (ULTRA-PROMPTER EDITION) ---
app = FastAPI(title="Kefas High-End Design Engine")

# Configuración de CORS para Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seguridad: Bloqueo de 120s por IP para proteger tus créditos
last_request_time = {}

# 1. ESQUEMA DE DATOS (Sincronizado con los nuevos campos de Lovable)
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
    return {"status": "Arcano Kefas Engine is Running", "mode": "Production"}

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

    # --- 2. MOTOR DE INTELIGENCIA ARTIFICIAL (SUPER PROMPT PARA DISEÑADORES) ---
    blueprint_ia = "PENDIENTE: Revisión manual requerida (Fallo de conexión IA)."
    
    try:
        # Inicialización limpia: El SDK detectará tu Paid Tier automáticamente
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # El "Super Prompt" que combina toda la nueva data de Lovable
        prompt_maestro = f"""
        Actúa como un Director de Arte de Élite y experto en Prompt Engineering.
        Genera una GUÍA MAESTRA DE DISEÑO basada en estos parámetros:

        - EMPRESA: {datos.nombre_empresa} (Sector: {datos.sector})
        - VISIÓN: {datos.vision_proyecto}
        - PERSONALIDAD: {datos.personalidad_marca}
        - CLIMA VISUAL: {datos.temperatura_visual}
        - OBJETIVO: {datos.objetivo_comunicacion}
        - REFERENCIAS: {datos.links_cliente}

        TAREA PARA EL EQUIPO DE DISEÑO:
        1. PALETA TÉCNICA: 3 códigos HEX que respeten la temperatura {datos.temperatura_visual}.
        2. TIPOGRAFÍA: Combinación premium (Heading/Body) acorde a {datos.personalidad_marca}.
        3. CONCEPTO: Cómo los visuales lograrán el objetivo de '{datos.objetivo_comunicacion}'.
        4. SUPER PROMPT (INGLÉS) PARA MIDJOURNEY: 
           Crea un prompt de ultra-lujo que describa la 'Hero Section'. 
           Incluye: Estilo {datos.personalidad_marca}, iluminación cinematográfica (coherente con tonos {datos.temperatura_visual}), 
           texturas detalladas (vidrio, metal o texturas orgánicas), profundidad de campo y resolución 8k.
        """
        
        # Usamos el modelo que ya probaste exitosamente
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_maestro
        )
        blueprint_ia = response.text
        
    except Exception as e:
        print(f"Log: Fallo en IA (pero guardando datos): {e}")

    # --- 3. PERSISTENCIA EN HOSTINGER (TU CRM REAL) ---
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
