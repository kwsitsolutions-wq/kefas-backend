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

# =========================================================
# CONFIGURACIÓN DEL MOTOR ARCANO KEFAS v5.7 - HOSTINGER SMTP
# =========================================================
app = FastAPI(title="Arcano Kefas - Lead Management")

# 🟡 FIX #4 — CORS restringido a dominios reales en producción
# Cambia los valores por tus dominios reales antes de desplegar
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "https://kefasdigital.com").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🟠 FIX #6 — Rate limiter con limpieza de entradas antiguas
last_request_time: dict[str, float] = {}
RATE_LIMIT_SECONDS = 120
RATE_LIMIT_CLEANUP_INTERVAL = 600  # limpiar cada 10 minutos
_last_cleanup = time.time()


def check_rate_limit(client_ip: str) -> None:
    """Verifica y aplica rate limiting por IP, limpiando entradas expiradas periódicamente."""
    global _last_cleanup
    current_time = time.time()

    # Limpieza periódica para evitar crecimiento ilimitado en memoria
    if current_time - _last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL:
        expired = [
            ip for ip, t in last_request_time.items()
            if current_time - t > RATE_LIMIT_SECONDS
        ]
        for ip in expired:
            del last_request_time[ip]
        _last_cleanup = current_time

    if client_ip in last_request_time:
        elapsed = current_time - last_request_time[client_ip]
        if elapsed < RATE_LIMIT_SECONDS:
            remaining = int(RATE_LIMIT_SECONDS - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Espera {remaining} segundos entre envíos."
            )

    last_request_time[client_ip] = current_time


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


# =========================================================
# FUNCIÓN DE NOTIFICACIÓN POR EMAIL (HOSTINGER SMTP CORREGIDO)
# =========================================================
def enviar_notificacion_kefas(datos: Lead) -> None:
    email_usuario = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASS")
    # 🔴 FIX #2 — Destinatario configurable, no el mismo remitente
    email_destino = os.environ.get("EMAIL_DESTINO", email_usuario)

    if not email_usuario or not email_password:
        print("⚠️  Error: Variables EMAIL_USER / EMAIL_PASS no configuradas en Render.")
        return

    mensaje = MIMEMultipart()
    mensaje["From"] = email_usuario
    mensaje["To"] = email_destino
    mensaje["Subject"] = f"🔥 NUEVO PROSPECTO: {datos.nombre_empresa}"

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
    Visión del Proyecto:           {datos.vision_proyecto}
    Personalidad de Marca:         {datos.personalidad_marca}
    Temperatura Visual:            {datos.temperatura_visual}
    Objetivo de Comunicación (CTA):{datos.objetivo_comunicacion}
    Link de Referencia:            {datos.links_cliente}

    -------------------------------------------
    Nota: Los datos también han sido guardados en la tabla 'prospectos' en Hostinger.
    """
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        # 🔴 FIX #1 — Puerto 465 para SMTP_SSL (587 es para STARTTLS, incompatible con SMTP_SSL)
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as servidor:
            servidor.login(email_usuario, email_password)
            servidor.send_message(mensaje)
        print("✅ Notificación enviada con éxito vía Hostinger SMTP.")
    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación SMTP. Verifica EMAIL_USER y EMAIL_PASS.")
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP al enviar notificación: {e}")
    except Exception as e:
        print(f"❌ Error inesperado al enviar notificación: {e}")


@app.get("/")
async def root():
    return {
        "status": "Arcano Kefas Backend Online",
        "mode": "Hostinger SMTP Active Mode",
    }


# =========================================================
# RUTA DE CAPTURA (PROCESAR CUESTIONARIO)
# =========================================================
@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead, request: Request):
    client_ip = request.client.host

    # Rate limiting con limpieza automática
    check_rate_limit(client_ip)

    # 🟡 FIX #3 — Credenciales DB completamente en variables de entorno
    db_config = {
        "host":     os.environ.get("DB_HOST"),
        "user":     os.environ.get("DB_USER"),        # era hardcoded
        "password": os.environ.get("DB_PASSWORD"),
        "database": os.environ.get("DB_NAME"),        # era hardcoded
    }

    if not all(db_config.values()):
        raise HTTPException(
            status_code=500,
            detail="Configuración de base de datos incompleta en variables de entorno."
        )

    sql = """
        INSERT INTO prospectos
            (nombre_empresa, representante, sector, whatsapp, email,
             vision_proyecto, personalidad_marca, temperatura_visual,
             objetivo_comunicacion, links_cliente, analisis_ia,
             origen_lead, codigo_asesor)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pendiente de análisis', %s, %s)
    """

    valores = (
        datos.nombre_empresa, datos.representante, datos.sector,
        datos.whatsapp, datos.email, datos.vision_proyecto,
        datos.personalidad_marca, datos.temperatura_visual,
        datos.objetivo_comunicacion, datos.links_cliente,
        datos.origen_lead, datos.codigo_asesor,
    )

    # 🟠 FIX #5 — Cierre garantizado de conexión DB con try/finally
    conexion = None
    cursor = None
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()
        cursor.execute(sql, valores)
        conexion.commit()
    except mysql.connector.Error as db_e:
        print(f"❌ Error de base de datos: {db_e}")
        raise HTTPException(status_code=500, detail=f"Error interno de base de datos: {db_e}")
    finally:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()

    # Notificación por email (fuera del bloque DB — fallo de email no revierte el registro)
    enviar_notificacion_kefas(datos)

    return {"status": "success", "message": "Lead y Referencia registrados correctamente."}


# =========================================================
# RUTA DE CITAS
# =========================================================
@app.post("/api/citas")
async def procesar_cita(datos: Cita):
    resultado = registrar_cita_soporte(datos)
    if resultado["status"] == "error":
        raise HTTPException(status_code=500, detail=resultado["message"])
    return resultado
