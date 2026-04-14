import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="API Kefas Digital")

# CORS - Autorizamos tu página de Lovable para que la conexión no sea bloqueada
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kefas-digital-glow.lovable.app", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estructura de los datos que enviará tu formulario en Lovable
class Lead(BaseModel):
    nombre: str
    empresa: str
    email: str
    mensaje_proyecto: str
    es_rebuilding: bool

@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead):
    # 1. Filtro de calidad: Rechazar si es código reciclado
    if datos.es_rebuilding:
        return {
            "status": "rechazado", 
            "mensaje": "Por el momento en Kefas Digital nos enfocamos exclusivamente en estructuración web de alta gama e integración de IA desde cero. No trabajamos sobre código de terceros ni marketing general."
        }
        
    try:
        # 2. Conectar con el "cerebro" de Gemini usando tu API Key
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Eres el consultor analítico de 'Kefas Digital', la agencia derivada de la marca Arcano Kefas. Nuestro enfoque es estrictamente el diseño de alta gama y la automatización con IA.
        Evalúa a este prospecto de forma directa y profesional:
        - Nombre: {datos.nombre}
        - Empresa: {datos.empresa}
        - Email: {datos.email}
        - Visión: {datos.mensaje_proyecto}
        
        Redacta un análisis interno breve sobre la viabilidad de este cliente y genera un borrador de correo confirmando que entregaremos una propuesta en 48 horas. Mantén un enfoque humano, consciente y directo.
        """
        respuesta_ia = model.generate_content(prompt)
        analisis_generado = respuesta_ia.text

        # 3. Base de Datos Hostinger (Sección preparada)
        # NOTA: Comentada temporalmente para que la API suba y funcione sin dar error por falta de credenciales. 
        """
        db_config = {
            'user': 'tu_usuario_hostinger',
            'password': 'tu_password',
            'host': 'tu_ip_hostinger',
            'database': 'tu_nombre_db'
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        query = "INSERT INTO leads_kefas (nombre, empresa, email, mensaje_proyect, es_rebuilding, analisis_ia) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (datos.nombre, datos.empresa, datos.email, datos.mensaje_proyecto, datos.es_rebuilding, analisis_generado))
        conn.commit()
        cursor.close()
        conn.close()
        """
        
        return {
            "status": "aprobado", 
            "mensaje": "¡Tu visión está en camino! Hemos recibido tus datos y en menos de 48 horas recibirás nuestra propuesta en tu correo.",
            "analisis": analisis_generado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))