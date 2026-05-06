import os
import requests
import mysql.connector
from pydantic import BaseModel

# Definimos el modelo de datos para la Terminal
class Cita(BaseModel):
    nombre: str
    email: str
    fecha: str
    hora: str
    finalidad: str

def registrar_cita_soporte(datos: Cita):
    # 1. NOTIFICACIÓN POR EMAIL (Resend API)
    cuerpo = f"""
Solicitud de Cita de Soporte/Consultoría:

Nombre:    {datos.nombre}
Email:     {datos.email}
Fecha:     {datos.fecha}
Hora:      {datos.hora}
Finalidad: {datos.finalidad}

-------------------------------------------
Nota: Datos guardados en la tabla 'citas_consultoria'.
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
                "subject": f"🔴 NUEVA CITA SOPORTE: {datos.nombre}",
                "text": cuerpo
            }
        )
        if response.status_code == 200:
            print("✅ Notificación de cita enviada vía Resend.")
        else:
            print(f"❌ Error Resend cita: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error inesperado email cita: {e}")

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
