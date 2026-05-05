import os
import time
import smtplib
from citas import Cita, registrar_cita_soporte  
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector
from typing import Optional

app = FastAPI(title="Arcano Kefas - Lead Management")

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
    origen_lead: Optional[str] = "Directo"
    codigo_asesor: Optional[str] = None

# --- FUNCIÓN DE NOTIFICACIÓN POR EMAIL ---
def enviar_notificacion_kefas(datos: Lead):
    email_usuario = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASS")

    if not email_usuario or not email_password:
        print("⚠️ Error: Variables de email no configuradas.")
        return

    mensaje = MIMEMultipart()
    mensaje["From"] = email_usuario
    mensaje["To"] = email_usuario
    mensaje["Subject"] = f"🔥 NUEVO PROSPECTO: {datos.nombre_empresa}"

    cuerpo = f"""
    Has recibido un nuevo registro en Kefas Digital:
    
    DETALLES DEL CLIENTE:
    -------------------------------------------
    Nombre de la Empresa: {datos.nombre_empresa}
    Representante: {datos.representante}
    WhatsApp: {datos.whatsapp}
    Email: {datos.email}
    Sector/Nicho: {datos.sector}
    
    RASTREO DE VENTA:
    -------------------------------------------
    Origen del Lead: {datos.origen_lead}
    Código de Asesor: {datos.codigo_asesor if datos.codigo_asesor else "N/A"}
    
    ESTRATEGIA DEL PROYECTO:
    -------------------------------------------
    Visión del Proyecto: 
    {datos.vision_proyecto}
    
    Personalidad de Marca: {datos.personalidad_marca}
    Temperatura Visual: {datos.temperatura_visual}
    Objetivo de Comunicación (CTA): {datos.objetivo_comunicacion}
    Link de Referencia: {datos.links_cliente}
    
    -------------------------------------------
    Nota: Los datos también han sido guardados en la tabla 'prospectos'.
    """
    mensaje.attach(MIMEText(cuerpo, "plain"))
try:
        # Cambiamos al puerto 587 con STARTTLS para que Render no bloquee la conexión
        with smtplib.SMTP("smtp.gmail.com", 587) as servidor:
            servidor.ehlo()
            servidor.starttls()  # Activa el cifrado seguro
            servidor.ehlo()
            servidor.login(email_usuario, email_password)
            servidor.send_message(mensaje)
        print(f"✅ Notificación enviada con éxito por email.")
    except Exception as e:
        print(f"❌ Error al enviar notificación por email: {e}")

@app.get("/")
async def root():
    return {"status": "Arcano Kefas Backend Online", "mode": "Private Lead & Referral Mode"}


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
        print(f"Error técnico: {db_e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {db_e}")


@app.post("/api/citas")
async def procesar_cita(datos: Cita):
    resultado = registrar_cita_soporte(datos)
    if resultado["status"] == "error":
        raise HTTPException(status_code=500, detail=resultado["message"])
    return resultado
