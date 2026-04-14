import os
import time
from google import genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="Kefas Shielded Engine - v2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diccionario para controlar el tiempo entre envíos por IP (Sesión de seguridad)
# Usaremos 120 segundos para máxima protección
last_request_time = {}

class Lead(BaseModel):
    nombre_empresa: str
    representante: str
    sector: str
    whatsapp: str
    email: str
    vision_proyecto: str
    links_cliente: str = ""

@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    # --- CONTROL DE SEGURIDAD (ANTISPAM 2 MINUTOS) ---
    client_ip = request.client.host
    current_time = time.time()
    TIEMPO_ESPERA = 120 # 2 minutos exactos
    
    if client_ip in last_request_time:
        tiempo_transcurrido = current_time - last_request_time[client_ip]
        if tiempo_transcurrido < TIEMPO_ESPERA:
            tiempo_restante = int(TIEMPO_ESPERA - tiempo_transcurrido)
            raise HTTPException(
                status_code=429, 
                detail=f"Seguridad activa: Por favor, espera {tiempo_restante} segundos para enviar otra solicitud."
            )
    
    # Actualizamos el tiempo del último envío exitoso
    last_request_time[client_ip] = current_time
    # ------------------------------------------------

    # Valor por defecto si la IA falla
    blueprint_ia = "PENDIENTE: El sistema de IA está bajo alta demanda. Pedro revisará tu visión manualmente."
    
    try:
        # Intento de generar contenido con Gemini
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        prompt = f"""
        Actúa como Director de Arte Senior. Genera Ficha Técnica y 2 Prompts de Imagen (A y B).
        Empresa: {datos.nombre_empresa}. Sector: {datos.sector}. Visión: {datos.vision_proyecto}.
        Referencias: {datos.links_cliente}
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        blueprint_ia = response.text
        
    except Exception as e:
        # Si Gemini falla por cuota o error, el proceso NO se detiene
        print(f"ALERTA: Error en Gemini (posible saturación): {e}")
        # Mantenemos el valor de 'blueprint_ia' como PENDIENTE

    # --- GUARDADO OBLIGATORIO EN HOSTINGER ---
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
        print(f"ERROR CRÍTICO DB: {db_e}")
        raise HTTPException(status_code=500, detail="Error de conexión con el servidor de datos.")

    return {
        "status": "success", 
        "message": "Información recibida correctamente", 
        "ia_status": "completado" if "PENDIENTE" not in blueprint_ia else "pendiente"
    }
