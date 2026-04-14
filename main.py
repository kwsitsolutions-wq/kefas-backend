import os
from google import genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

# 1. Configuración de la API para Arcano Kefas
app = FastAPI(title="Kefas Design Architect - Sistema de Producción")

# 2. Permisos CORS para conectar con Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Estructura de datos que Lovable debe enviar
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
        # 4. Conexión con Gemini (El Cerebro de Diseño)
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # EL PROMPT MAESTRO: Genera la comparativa y los prompts de imagen
        prompt = f"""
        Actúa como Director de Arte Senior y Estratega de Diseño Web de 'Kefas Digital'. 
        Tu objetivo es generar un INFORME DE PRODUCCIÓN INTERNO para Pedro (Dueño de la Agencia). 
        Este informe es confidencial y servirá para crear la propuesta visual.
        
        DATOS DEL PROYECTO:
        - EMPRESA: {datos.nombre_empresa}
        - REPRESENTANTE: {datos.representante}
        - SECTOR: {datos.sector}
        - VISIÓN DEL CLIENTE: {datos.vision_proyecto}
        - REFERENCIAS QUE LE GUSTAN AL CLIENTE: {datos.links_cliente}

        ENTREGA ESTA ESTRUCTURA DE PRODUCCIÓN:

        1. ANÁLISIS ESTRATÉGICO: 
           Analiza los links del cliente ({datos.links_cliente}). Identifica qué elementos estéticos le atraen y cómo podemos elevar esa idea usando nuestros estándares de alta gama.

        2. FICHA TÉCNICA (BLUEPRINT): 
           - Concepto visual sugerido.
           - Paleta de Colores HEX (3 códigos principales).
           - Tipografías recomendadas.
           - Estructura de navegación para los programadores.

        3. GENERADOR DE PROMPTS PARA IMÁGENES (MIDJOURNEY/DALL-E):
           Crea 2 Prompts detallados en INGLÉS para que Pedro genere mockups visuales. Estos deben permitirle comparar la visión del cliente con las plantillas internas de la agencia:
           - PROMPT A (Evolución Directa): Lleva la visión de '{datos.vision_proyecto}' a un nivel ultra-profesional y moderno.
           - PROMPT B (Vanguardia Kefas): Un diseño disruptivo y sofisticado basado en el sector {datos.sector}, con iluminación cinematográfica y UI de última generación.

        4. LINKS DE BENCHMARKING: 
           Proporciona 2 links de sitios web reales (Awwwards/Behance) que representen el 'Nivel 10' de diseño para este sector.

        Usa un tono técnico, estratégico y directo.
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        blueprint_ia = response.text
        
        # 5. Guardado en la Memoria (Base de Datos Hostinger)
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user="u365762194_pedro_admin",
            password=os.environ.get("DB_PASSWORD"),
            database="u365762194_agencia"
        )
        
        cursor = conexion.cursor()
        
        # Consolidamos metadatos de contacto para tu control en la base de datos
        detalles_contacto = f"Rep: {datos.representante} | WA: {datos.whatsapp} | Visión: {datos.vision_proyecto} | Links: {datos.links_cliente}"
        
        sql = "INSERT INTO prospectos (nombre, empresa, email, mensaje, analisis_ia) VALUES (%s, %s, %s, %s, %s)"
        valores = (datos.nombre_empresa, datos.sector, datos.email, detalles_contacto, blueprint_ia)
        
        cursor.execute(sql, valores)
        conexion.commit()
        
        cursor.close()
        conexion.close()
        
        return {
            "status": "success", 
            "message": f"Análisis de producción listo para {datos.representante}",
            "blueprint": blueprint_ia
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
