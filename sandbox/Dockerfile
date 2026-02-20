FROM python:3.11-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /sandbox

# Instalación de herramientas base de análisis
# Estas librerías estarán disponibles para el código generado por la IA
RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    numpy==1.26.4 \
    scikit-learn==1.4.2 \
    matplotlib==3.8.4 \
    seaborn==0.13.2 \
    scipy==1.13.0 \
    statsmodels==0.14.2

# Creamos un usuario sin privilegios para ejecutar el código
RUN useradd -m -s /bin/bash sandboxuser
USER sandboxuser

# Entrada genérica (El host inyectará el script)
CMD ["python3", "-c", "print('Sandbox Ready')"]
