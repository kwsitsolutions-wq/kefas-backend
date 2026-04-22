import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v4.3 (DEMO LITE)
# =========================================================
app = FastAPI(title="Arcano Kefas - Design Master v4.3 (Demo Lite)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protección de IP para cuidar tus créditos de pago
last_request_time = {}

# Esquema de datos (Lo que llega desde el formulario de Lovable)
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
    return {"status": "Arcano Kefas Engine is Online", "mode": "Demo Lite"}

# =========================================================
# 2. PROCESAMIENTO: GENERACIÓN DE PROMPT ULTRA-CORTO
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    
    # --- SEGURIDAD: Límite de 120s por IP ---
    client_ip = request.client.host
    current_time = time.time()
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            restante = int(120 - (current_time - last_request_time[client_ip]))
            raise HTTPException(status_code=429, detail=f"Espera {restante}s.")
    last_request_time[client_ip] = current_time

    # --- GEMINI: GENERACIÓN DEL PROMPT CRUDO ---
    blueprint_ia = "PENDIENTE: Error en IA. Revisar manualmente."
    error_ia = None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # PROMPT ULTRA-CORTO (Ahorro máximo de tokens)
        # Solo traduce las variables a un comando técnico de Midjourney.
        prompt_maestro = f"""
        Traducción técnica para Midjourney prompt (solo responde con el prompt en inglés, sin texto adicional):
        /imagine prompt: Grid of 5 distinct desktop web design screenshots for a {datos.sector} company named "{datos.nombre_empresa}". 
        Goal: {datos.objetivo_comunicacion}. Style: {datos.personalidad_marca}, {datos.temperatura_visual} lighting. 
        Must include visible {datos.nombre_empresa} logo in header and prominent Call-to-Action buttons. 
        High-resolution UI/UX, photorealistic .png, modern layout concept: {datos.vision_proyecto} --ar 16:9 --v 6.0
        """
        
        # Usando el modelo más rápido y barato
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Mantenemos este que es rápido y barato
            contents=prompt_maestro
        )
        # Guardamos solo el comando limpio que generó la IA
        blueprint_ia = response.text.strip() # .strip() quita espacios extra

    except Exception as e:
        error_ia = f"ERROR GEMINI: {type(e).__name__} — {str(e)}"
        print(error_ia)

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
        print(f"Error DB Hostinger: {db_e}")
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos.")

    return {
        "status": "success", 
        "ia_status": "completado" if error_ia is None else "fallido",
        "ia_error": error_ia,
        "prompt_generado": blueprint_ia # Opcional: devolver el prompt al frontend
    }
