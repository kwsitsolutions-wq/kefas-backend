import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL SERVIDOR Y SEGURIDAD (ADUANA)
# =========================================================
app = FastAPI(title="Arcano Kefas - High End Engine v3.9")

# Permitir que Lovable (Frontend) se comunique con Render (Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diccionario para controlar que nadie abuse de tu saldo (Protección IP)
last_request_time = {}

# =========================================================
# 2. DEFINICIÓN DEL FORMULARIO (ESQUEMA DE DATOS)
# =========================================================
# Aquí definimos exactamente qué datos recibimos de Lovable
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

# =========================================================
# 3. RUTA DE INICIO (TEST DE ESTADO)
# =========================================================
@app.get("/")
async def root():
    return {"status": "Arcano Kefas Engine is Running", "mode": "Production"}

# =========================================================
# 4. PROCESO MAESTRO: IA + BASE DE DATOS
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    
    # --- PASO A: PROTECCIÓN CONTRA SPAM (120 SEGUNDOS) ---
    client_ip = request.client.host
    current_time = time.time()
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            restante = int(120 - (current_time - last_request_time[client_ip]))
            raise HTTPException(status_code=429, detail=f"Seguridad activa. Espera {restante}s.")
    
    last_request_time[client_ip] = current_time

    # --- PASO B: MOTOR CREATIVO (GEMINI 2.0 FLASH) ---
    # Si la IA falla, guardamos este texto por defecto
    blueprint_ia = "PENDIENTE: Revisión manual requerida (Fallo de conexión IA)."
    
    try:
        # Iniciamos el cliente de Google con tu API KEY de pago
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # El SUPER PROMPT que mezcla toda la psicología de marca
        prompt_maestro = f"""
        Actúa como Director de Arte de Élite. 
        Proyecto: {datos.nombre_empresa}.
        Estilo: {datos.personalidad_marca} | Clima: {datos.temperatura_visual}.
        Meta: {datos.objetivo_comunicacion}.
        Visión: {datos.vision_proyecto}.

        ENTREGA:
        1. PALETA HEX (3 colores) basada en clima {datos.temperatura_visual}.
        2. TIPOGRAFÍA sugerida para {datos.personalidad_marca}.
        3. SUPER PROMPT (INGLÉS) para Midjourney: {datos.personalidad_marca} high-end design, {datos.temperatura_visual} lighting, cinematic, 8k, photorealistic.
        """
        
        # Llamada a la versión estable de pago
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt_maestro
        )
        blueprint_ia = response.text
        
    except Exception as e:
        print(f"--- LOG ERROR IA: {e} ---")

    # --- PASO C: PERSISTENCIA (GUARDADO EN HOSTINGER) ---
    try:
        # Conectamos a tu DB u365762194_agencia
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor()
        
        # SQL con las 11 columnas que ya tienes en tu phpMyAdmin
        sql = """INSERT INTO prospectos 
                 (nombre_empresa, representante, sector, whatsapp, email, 
                  vision_proyecto, personalidad_marca, temperatura_visual, 
                  objetivo_comunicacion, links_cliente, analisis_ia) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        # Mapeo de datos para insertar
        valores = (
            datos.nombre_empresa, datos.representante, datos.sector, 
            datos.whatsapp, datos.email, datos.vision_proyecto,
            datos.personalidad_marca, datos.temperatura_visual, 
            datos.objetivo_comunicacion, datos.links_cliente, blueprint_ia
        )
        
        cursor.execute(sql, valores)
        conexion.commit() # Guardar cambios permanentemente
        cursor.close()
        conexion.close()
        
    except Exception as db_e:
        print(f"--- LOG ERROR DB: {db_e} ---")
        raise HTTPException(status_code=500, detail="Error de conexión con Hostinger.")

    # Respuesta final para Lovable
    return {
        "status": "success", 
        "ia_status": "completado" if "PENDIENTE" not in blueprint_ia else "pendiente"
    }
