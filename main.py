import os
import time
import requests
from citas import Cita, registrar_cita_soporte  
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from typing import Optional

# =========================================================
# CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v5.7 - RESEND EMAIL
# =========================================================
app = FastAPI(title="Arcano Kefas - Lead Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kefasdigital.com", "https://www.kefasdigital.com"],
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
    origen_lead: Optional[str] = "Directo"
    codigo_asesor: Optional[str] = None


# --- FUNCIÓN DE NOTIFICACIÓN POR EMAIL (RESEND API) ---
def enviar_notificacion_kefas(datos: Lead):
    cuerpo = f"""
Has recibido un nuevo registro en Kefas Digital:

DETALLES DEL CLIENTE:
-------------------------------------------
Nombre de la Empresa: {datos.nombre_empresa}
Representante:        {datos.representante}
WhatsApp:             {datos.whatsapp}
Email:                {datos.email}
Sector/Nicho:         {datos.sector}

RASTREO DE VENTA:
-------------------------------------------
Origen del Lead:  {datos.origen_lead}
Código de Asesor: {datos.codigo_asesor if datos.codigo_asesor else "N/A"}

ESTRATEGIA DEL PROYECTO:
-------------------------------------------
Visión del Proyecto:            {datos.vision_proyecto}
Personalidad de Marca:          {datos.personalidad_marca}
Temperatura Visual:             {datos.temperatura_visual}
Objetivo de Comunicación (CTA): {datos.objetivo_comunicacion}
Link de Referencia:             {datos.links_cliente}

-------------------------------------------
Los datos han sido guardados en la tabla 'prospectos' en Hostinger.
    """

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
               "Authorization": f"Bearer {os.environ.get('RESEND_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "from": "Kefas Digital <support@send.kefasdigital.com>",
                "to": ["kwsitsolutions@gmail.com"],
                "subject": f"🔥 NUEVO PROSPECTO: {datos.nombre_empresa}",
                "text": cuerpo
            }
        )
        if response.status_code == 200:
            print("✅ Notificación enviada con éxito vía Resend.")
        else:
            print(f"❌ Error Resend: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error inesperado al enviar notificación: {e}")


@app.get("/")
async def root():
    return {"status": "Arcano Kefas Backend Online", "mode": "Resend Active Mode"}


# =========================================================
# RUTA DE CAPTURA (PROCESAR CUESTIONARIO)
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    client_ip = request.client.host
    current_time = time.time()

    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            raise HTTPException(status_code=429, detail="Espera un momento entre envíos.")
    last_request_time[client_ip] = current_time

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
                   objetivo_comunicacion, links_cliente, analisis_ia,
                   origen_lead, codigo_asesor) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente de análisis', %s, %s)"""

        valores = (
            datos.nombre_empresa, datos.representante, datos.sector,
            datos.whatsapp, datos.email, datos.vision_proyecto,
            datos.personalidad_marca, datos.temperatura_visual,
            datos.objetivo_comunicacion, datos.links_cliente,
            datos.origen_lead, datos.codigo_asesor
        )

        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        conexion.close()

        enviar_notificacion_kefas(datos)

        return {"status": "success", "message": "Lead y Referencia registrados correctamente."}

    except Exception as db_e:
        print(f"Error técnico base de datos: {db_e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {db_e}")


# =========================================================
# RUTA DE CITAS
# =========================================================
@app.post("/api/citas")
async def procesar_cita(datos: Cita):
    resultado = registrar_cita_soporte(datos)
    if resultado["status"] == "error":
        raise HTTPException(status_code=500, detail=resultado["message"])
    return resultado
