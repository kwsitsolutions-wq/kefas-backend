import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v4.0
# =========================================================
app = FastAPI(title="Arcano Kefas - Resilient Engine v4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protección IP para cuidar tus créditos de pago
last_request_time = {}

# Esquema de datos sincronizado con Lovable y Hostinger
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
# 2. PROCESAMIENTO CON REINTENTOS (ANTI-SATURACIÓN)
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

    # --- MOTOR DE IA CON SISTEMA DE PERSISTENCIA ---
    blueprint_ia = "PENDIENTE: IA ocupada tras 3 intentos. Revisar manualmente."
    
    # Intentamos 3 veces en caso de error 503 (Servidor ocupado)
    for intento in range(3):
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
                model='gemini-2.5-flash', 
                contents=prompt_maestro
            )
            blueprint_ia = response.text
            break  # Éxito: salimos del bucle de reintentos
            
        except Exception as e:
            if "503" in str(e):
                print(f"Intento {intento+1} fallido (503), reintentando en 3s...")
                time.sleep(3) # Pausa estratégica
            else:
                print(f"Error crítico IA: {e}")
                break

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
        "ia_status": "completado" if "Revisar" not in blueprint_ia else "reintento_fallido"
    }
