import os
import time
import smtplib
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mysql.connector

# =========================================================
# 1. CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v5.3 (Privacidad Total)
# =========================================================
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

# --- FUNCIÓN DE NOTIFICACIÓN POR EMAIL (Privada) ---
def enviar_notificacion_kefas(datos: Lead):
    email_usuario = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASS")

    if not email_usuario or not email_password:
        print("⚠️ Error: Variables de email no configuradas en Render.")
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
    
    ESTRATEGIA DEL PROYECTO:
    -------------------------------------------
    Visión del Proyecto: 
    {datos.vision_proyecto}
    
    Personalidad de Marca: {datos.personalidad_marca}
    Temperatura Visual: {datos.temperatura_visual}
    Objetivo de Comunicación (CTA): {datos.objetivo_comunicacion}
    Link de Referencia/Inspiración: {datos.links_cliente}
    
    -------------------------------------------
    Nota: Los datos también han sido guardados en la base de datos de Hostinger.
    """
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(email_usuario, email_password)
            servidor.send_message(mensaje)
        print(f"✅ Notificación enviada con éxito.")
    except Exception as e:
        print(f"❌ Error al enviar notificación: {e}")

@app.get("/")
async def root():
    return {"status": "Arcano Kefas Backend Online", "mode": "Private Notification Mode"}

# =========================================================
# 2. RUTA DE CAPTURA (Única ruta activa)
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    client_ip = request.client.host
    current_time = time.time()
    
    # Anti-Spam (120 segundos entre envíos por IP)
    if client_ip in last_request_time:
        if current_time - last_request_time[client_ip] < 120:
            raise HTTPException(status_code=429, detail="Espera un momento entre envíos.")
    last_request_time[client_ip] = current_time

    try:
        # Conexión a Hostinger
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
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente de análisis')"""
        
        valores = (
            datos.nombre_empresa, datos.representante, datos.sector, 
            datos.whatsapp, datos.email, datos.vision_proyecto,
            datos.personalidad_marca, datos.temperatura_visual, 
            datos.objetivo_comunicacion, datos.links_cliente
        )
        
        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        conexion.close()

        # DISPARAR CORREO
        enviar_notificacion_kefas(datos)

        return {"status": "success", "message": "Lead recibido correctamente."}
        
    except Exception as db_e:
        print(f"Error técnico: {db_e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
