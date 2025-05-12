# Imagen base de Python
FROM python:3.10-slim

# Establece las variables de entorno para evitar la escritura de archivos pyc y para que Python no bufferice la salida
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar las dependencias del sistema necesarias para compilar psycopg2
RUN apt-get update && \
    apt-get install -y libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código al contenedor
COPY . .

# Expone el puerto de Flask
EXPOSE 5000

# Comando por defecto al iniciar el contenedor
CMD ["python", "run.py"]
