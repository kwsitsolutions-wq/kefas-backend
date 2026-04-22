import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v4.4 (ULTRA-LITE)
# =========================================================
app = FastAPI(title="Arcano Kefas - Design Master v4.4 (Ultra-Lite)")

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
    return {"status": "Arcano Kefas Engine is Online", "mode": "Ultra-Lite"}

# =========================================================
# 2. PROCESAMIENTO: GENERACIÓN DE PROMPT PARA 1 IMAGEN
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    
    client_ip = request.client.host
    current_time = time.time()
    if client_ip in last_request_time and (current_time - last_request_time[client_ip] < 120):
        raise HTTPException(status_code=429, detail="Espera 120s.")
    last_request_time[client_ip] = current_time

    blueprint_ia = "PENDIENTE: Error en IA."
    error_ia = None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # PROMPT MINIMALISTA: Una sola imagen de impacto.
        # Directo al grano para ahorrar tokens y dar un resultado limpio.
        prompt_maestro = f"""
        Generate only the English Midjourney prompt for: 
        A professional high-end desktop web design screenshot for "{datos.nombre_empresa}" ({datos.sector}). 
        Style: {datos.personalidad_marca}, {datos.temperatura_visual} lighting. 
        Visible logo, hero section with "Get Started" button, conversion-focused. 
        Concept: {datos.vision_proyecto}. Photorealistic UI/UX, 8k, .png --ar 16:9
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt_maestro
        )
        blueprint_ia = response.text.strip()

    except Exception as e:
        error_ia = str(e)
        print(f"Error IA: {e}")

    # =========================================================
    # 3. GUARDADO EN BASE DE DATOS HOSTINGER
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
        print(f"Error DB: {db_e}")
        raise HTTPException(status_code=500, detail="Error DB")

    return {
        "status": "success", 
        "ia_status": "completado" if error_ia is None else "fallido",
        "prompt": blueprint_ia
    }
