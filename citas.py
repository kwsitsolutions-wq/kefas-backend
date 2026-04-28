import os
import smtplib
import mysql.connector
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Definimos el modelo de datos para la Terminal
class Cita(BaseModel):
    nombre: str
    email: str
    fecha: str
    hora: str
    finalidad: str

def registrar_cita_soporte(datos: Cita):
    # 1. NOTIFICACIÓN POR EMAIL (Usando tu configuración de Gmail)
    email_usuario = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASS")

    if email_usuario and email_password:
        mensaje = MIMEMultipart()
        mensaje["From"] = email_usuario
        mensaje["To"] = email_usuario
        mensaje["Subject"] = f"🔴 NUEVA CITA SOPORTE: {datos.nombre}"

        cuerpo = f"""
        Solicitud de Cita de Soporte/Consultoría:
        
        Nombre: {datos.nombre}
        Email: {datos.email}
        Fecha: {datos.fecha}
        Hora: {datos.hora}
        Finalidad: {datos.finalidad}
        
        -------------------------------------------
        Nota: Datos guardados en la tabla 'citas_consultoria'.
        """
        mensaje.attach(MIMEText(cuerpo, "plain"))

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(email_usuario, email_password)
                servidor.send_message(mensaje)
            print("✅ Notificación de cita enviada.")
        except Exception as e:
            print(f"❌ Error email cita: {e}")

    # 2. GUARDAR EN BASE DE DATOS (Hostinger)
    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        cursor = conexion.cursor()
        sql = """INSERT INTO citas_consultoria 
                 (nombre, email, fecha, hora, finalidad) 
                 VALUES (%s, %s, %s, %s, %s)"""
        
        valores = (datos.nombre, datos.email, datos.fecha, datos.hora, datos.finalidad)
        
        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        conexion.close()
        return {"status": "success", "message": "Cita registrada correctamente."}
    except Exception as db_e:
        print(f"❌ Error BD Cita: {db_e}")
        return {"status": "error", "message": str(db_e)}
