import os
from google import genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

app = FastAPI(title="Kefas High-End Design Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estructura de datos completa
class Lead(BaseModel):
    nombre_empresa: str
    representante: str
    sector: str
    whatsapp: str
    email: str
    vision_proyecto: str
    links_cliente: str = ""

@app.post("/procesar-cuestionario")
async def procesar_cuestionario(datos: Lead):
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # PROMPT INTERNO DE PRODUCCIÓN
        prompt = f"""
        Actúa como Director de Arte Senior de 'Kefas Digital'. 
        Genera un INFORME DE PRODUCCIÓN INTERNO para Pedro.
        
        DATOS:
        - EMPRESA: {datos.nombre_empresa} (Rep: {datos.representante})
        - SECTOR: {datos.sector}
        - VISIÓN: {datos.vision_proyecto}
        - REF. CLIENTE: {datos.links_cliente}

        ENTREGA:
        1. ANÁLISIS ESTRATÉGICO: Comparativa de referencias vs. estándares de Arcano Kefas.
        2. FICHA TÉCNICA: Colores HEX, Tipografía y Estructura.
        3. GENERADOR DE PROMPTS (MIDJOURNEY/DALL-E): 
           - Prompt 1: Evolución técnica de la idea del cliente.
           - Prompt 2: Propuesta disruptiva de alta gama para {datos.sector}.
        4. BENCHMARKING: 2 links de sitios nivel mundial.
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        blueprint_ia = response.text
        
        # Conexión y guardado en los nuevos campos
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
            datos.nombre_empresa, 
            datos.representante, 
            datos.sector, 
            datos.whatsapp, 
            datos.email, 
            datos.vision_proyecto, 
            datos.links_cliente, 
            blueprint_ia
        )
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        cursor.close()
        conexion.close()
        
        return {"status": "success", "blueprint": blueprint_ia}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
