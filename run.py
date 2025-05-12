from app import create_app

app = create_app()

if __name__ == '__main__':
    # Permite que la aplicación escuche en todas las interfaces de red, 
    # lo cual es necesario cuando se ejecuta dentro de Docker
    app.run(debug=True, host='0.0.0.0', port=5000)
