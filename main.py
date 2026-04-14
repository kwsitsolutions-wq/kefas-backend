import os
from google import genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="API Kefas Digital")

# CORS - Autorizamos tu página de Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kefas-digital-glow.lovable.app", "*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estructura de los datos
class Lead(BaseModel):
    nombre: str
    empresa: str
    email: str
    mensaje_proyecto: str
    es_rebuilding: bool

@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead):
    if datos.es_rebuilding:
        return {
            "status": "rechazado", 
            "mensaje": "Por el momento en Kefas Digital nos enfocamos exclusivamente en estructuración web de alta gama e integración de IA desde cero. No trabajamos sobre código de terceros."
        }
        
    try:
        # 1. Análisis con Inteligencia Artificial
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        prompt = f"""
        Eres el consultor analítico de 'Kefas Digital', la agencia derivada de la marca Arcano Kefas. Nuestro enfoque es estrictamente el diseño de alta gama y la automatización con IA.
        Evalúa a este prospecto de forma directa y profesional:
        - Nombre: {datos.nombre}
        - Empresa: {datos.empresa}
        - Email: {datos.email}
        - Visión: {datos.mensaje_proyecto}
        
        Redacta un análisis interno breve sobre la viabilidad de este cliente y genera un borrador de correo confirmando que entregaremos una propuesta en 48 horas.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        analisis_generado = response.text
        
        # 2. Guardado en la Base de Datos de Hostinger
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        
        cursor = conexion.cursor()
        sql = "INSERT INTO prospectos (nombre, empresa, email, mensaje, analisis_ia) VALUES (%s, %s, %s, %s, %s)"
        valores = (datos.nombre, datos.empresa, datos.email, datos.mensaje_proyecto, analisis_generado)
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        cursor.close()
        conexion.close()
        
        return {
            "status": "aprobado", 
            "mensaje": "¡Tu visión está en camino! Hemos recibido tus datos y en menos de 48 horas recibirás nuestra propuesta en tu correo.",
            "analisis": analisis_generado
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
