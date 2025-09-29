# 🌱 Proyecto MORA  
### Monitoreo y Optimización de Recursos Agrícolas  

---

## 📌 Descripción

**Proyecto MORA** es una iniciativa de ciencia de datos aplicada al sector agrícola colombiano.  
Su objetivo es **analizar, visualizar y optimizar el uso de recursos agrícolas** a partir de un conjunto de datos que incluye:  
- Nutrientes del suelo (N, P, K).  
- Variables ambientales (temperatura, humedad, lluvia, pH).  
- Información geográfica (departamentos de Colombia).  
- Catálogo de cultivos.  

Este proyecto busca sentar las bases para **modelos de predicción y recomendaciones inteligentes** para agricultores, potenciando el uso de **Ciencia de Datos + Agricultura de Precisión**.  

---

## 🎯 Objetivos del Proyecto
1. Realizar un **Análisis Exploratorio de Datos (EDA)** sobre un dataset agrícola.  
2. Construir un **esquema relacional en SQLite** que represente las relaciones entre departamentos, cultivos y condiciones ambientales.  
3. Ejecutar **consultas SQL y Pandas** para extraer información clave.  
4. Crear **dashboards interactivos** para la visualización de patrones y tendencias.  
5. Establecer las bases para futuras fases de predicción y optimización agrícola.

---

## 🗂️ Estructura del Proyecto

```bash
├── data/
│   ├── crop_recommendation_unida.csv    # Dataset procesado
│
├── sql/
│   ├── conformacion_base_de_datos.sql   # Esquema principal de SQL
│
├── dashboards/
│   └── images/                          # Gráficas generadas
│
├── README.md                            # Documentación principal
│
├── LICENSE                              # Licencia del proyecto (GPLv3)
