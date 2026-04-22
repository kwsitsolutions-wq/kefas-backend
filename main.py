import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v4.2
# =========================================================
app = FastAPI(title="Arcano Kefas - Design Master v4.2")

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
    return {"status": "Arcano Kefas Engine is Online", "tier": "Paid"}

# =========================================================
# 2. PROCESAMIENTO: SUPER PROMPT DE 5 VARIACIONES
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

    # --- GEMINI: GENERACIÓN DEL PROMPT DE DISEÑO WEB ---
    blueprint_ia = "PENDIENTE: Error en IA. Revisar manualmente."
    error_ia = None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # EL SUPER PROMPT: Genera 5 propuestas completas con nombre y CTA
        prompt_maestro = f"""
        Actúa como un Director de Arte Senior y Diseñador UX/UI de clase mundial.
        TU OBJETIVO: Generar el prompt definitivo para crear 5 propuestas visuales de una Landing Page profesional.

        DATOS DEL PROYECTO:
        - Empresa: {datos.nombre_empresa}
        - Sector: {datos.sector}
        - Visión: {datos.vision_proyecto}
        - Estilo: {datos.personalidad_marca}
        - Clima Visual: {datos.temperatura_visual}
        - Meta de Conversión: {datos.objetivo_comunicacion}

        TAREA TÉCNICA (FICHA):
        1. PALETA HEX: 3 colores premium que respeten la temperatura {datos.temperatura_visual}.
        2. TIPOGRAFÍA: Combinación de Google Fonts acorde al estilo {datos.personalidad_marca}.

        TAREA CREATIVA (EL PROMPT PARA IMAGEN):
        Redacta un prompt maestro en INGLÉS para Midjourney/DALL-E que genere 5 variaciones de diseño.
        El prompt debe exigir:
        - FORMATO: High-resolution web design screenshot, .png style, 8k.
        - ELEMENTOS OBLIGATORIOS: 
            * El nombre "{datos.nombre_empresa}" claramente en el Header/Logo.
            * Hero Section con un Call to Action (CTA) brillante (ej. "Get Started").
            * Menú de navegación, layout moderno y estructura de conversión profesional.
        - ESTILO VISUAL: Fusionar la personalidad "{datos.personalidad_marca}" con iluminación cinematográfica "{datos.temperatura_visual}".
        - VARIACIONES: Solicita 5 propuestas de layout distintas basadas en: {datos.vision_proyecto}.
        """
        
        # Usando tu modelo de preferencia
           response = client.models.generate_content(
            model='gemini-3.1-pro-preview',
            contents=prompt_maestro
        )
        blueprint_ia = response.text

    except Exception as e:
        error_ia = f"ERROR GEMINI: {type(e).__name__} — {str(e)}"
        print(error_ia)

    # =========================================================
    # 3. GUARDADO EN BASE DE DATOS HOSTINGER (SIEMPRE SE EJECUTA)
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
        # Mantenemos el error 500 para notificar al frontend
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos.")

    return {
        "status": "success", 
        "ia_status": "completado" if error_ia is None else "fallido",
        "ia_error": error_ia 
    }
