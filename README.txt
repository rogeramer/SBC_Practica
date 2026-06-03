SBC GAMEBOT - CHATBOT EXPERTO DE RECOMENDACIÓN DE VIDEOJUEGOS
==================================================================

1. DESCRIPCIÓN DEL PROYECTO
---------------------------
SBC GameBot es un chatbot web desarrollado en Python que recomienda videojuegos a partir de preferencias expresadas por el usuario mediante lenguaje natural.

El sistema utiliza:
- Una base de conocimiento propia almacenada en reglas.json.
- Reglas condición-conclusión y razonamiento mediante forward chaining.
- Detección de intenciones mediante palabras clave y expresiones regulares.
- Resolución de conflictos entre perfiles mediante prioridad y especificidad.
- Restricciones obligatorias y una puntuación heurística para ordenar recomendaciones.
- La API de RAWG para consultar videojuegos reales.
- La API pública de Steam para analizar bibliotecas visibles y recomendar juegos que el usuario ya posee.
- Contexto conversacional básico para interpretar referencias a juegos propuestos por el chatbot como: "detalles del 2", "guía del último" o "dame otros 5".

No se utiliza ninguna API externa para interpretar el lenguaje natural introducido por el usuario. La detección de intenciones y preferencias ha sido implementada dentro del
propio proyecto.

2. REQUISITOS PREVIOS
---------------------
Es necesario instalar:

- Python 3.10 o superior.
- pip, incluido normalmente con Python.
- Un navegador web moderno.
- Conexión a Internet para realizar consultas a RAWG y Steam.

Para comprobar la versión instalada:
    python --version 
    pip --version
    py --version

3. ESTRUCTURA PRINCIPAL DEL PROYECTO
-----------------------------------
    SBC_Practica/
    |
    |-- chatbot/
    |   |-- filtres.py
    |   |-- formatter.py
    |   |-- intent_parser.py
    |   |-- recommendation_config.py
    |   |-- recommendation_engine.py
    |
    |-- static/
    |   |-- style.css
    |
    |-- templates/
    |   |-- index.html
    |
    |-- .env
    |-- app.py
    |-- main.py
    |-- rawg_service.py
    |-- README.txt
    |-- reglas.json
    |-- requirements.txt
    |-- steam_library.py 
    |-- steam_service.py


Descripción resumida:
- app.py: inicia la aplicación web Flask y gestiona las sesiones.
- main.py: coordina el flujo conversacional y conecta los distintos módulos.
- reglas.json: contiene la base de conocimiento y las reglas de inferencia.
- chatbot/intent_parser.py: detecta la intención principal del mensaje.
- chatbot/filtres.py: extrae preferencias, filtros y referencias conversacionales.
- chatbot/recommendation_engine.py: obtiene candidatos, aplica restricciones y ordena los resultados mediante una puntuación heurística.
- chatbot/recommendation_config.py: contiene etiquetas, perfiles, prioridades y mapas.
- chatbot/formatter.py: convierte los resultados en respuestas legibles.
- rawg_service.py: gestiona las peticiones a la API de RAWG.
- steam_service.py: recupera bibliotecas públicas mediante Steam Web API.
- steam_library.py: cruza los resultados de RAWG con la biblioteca de Steam.

4. INSTALACIÓN
--------------
Desde la carpeta raíz del proyecto, crear un entorno virtual:

Windows PowerShell:
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

Windows CMD:

    python -m venv .venv
    .venv\Scripts\activate

Linux o macOS:

    python3 -m venv .venv
    source .venv/bin/activate

Instalar las dependencias:

    pip install -r requirements.txt

5. EJECUCIÓN
------------
Desde la carpeta raíz del proyecto y con el entorno virtual activado:
    python app.py

La terminal mostrará la dirección:
    http://127.0.0.1:5000

Abrir esa dirección en un navegador web.

Para detener la aplicación:
    Ctrl + C

6. PRUEBAS RECOMENDADAS
-----------------------
Las siguientes pruebas permiten revisar las principales funcionalidades. Es aconsejable ejecutarlas en orden y pulsar "reset" antes de iniciar un bloque nuevo cuando se indique.

A. Saludos y conversación natural
1. Mensaje:
       hola
   Resultado esperado:
       El chatbot muestra un mensaje de bienvenida: ¡Hola! Soy tu chatbot de videojuegos con RAWG...

2. Mensaje:
       hola quiero un juego de acción
   Resultado esperado:
       El chatbot recomienda juegos de acción.

3. Mensaje:
       adiós
   Resultado esperado:
       El chatbot muestra una despedida: ¡Hasta luego! Cuando quieras vuelvo a buscarte juegos.

B. Recomendaciones generales
4. Mensaje:
       Quiero un RPG con historia para PC
   Resultado esperado:
       Se muestran videojuegos compatibles con RPG, narrativa y PC.

5. Mensaje:
       Quiero un juego de acción difícil
   Resultado esperado:
       Se priorizan videojuegos de acción con reto elevado.

6. Mensaje:
       Quiero un juego de terror para jugar solo
   Resultado esperado:
       Se recomiendan videojuegos de terror que pueden jugarse en solitario.

7. Mensaje:
       Quiero un multijugador competitivo
   Resultado esperado:
       Se recomiendan juegos orientados a partidas competitivas.

8. Mensaje:
       Quiero un cooperativo local para jugar con amigos
   Resultado esperado:
       Se priorizan videojuegos con cooperativo local o funciones equivalentes.

9. Mensaje:
       Quiero un juego relajado para Nintendo Switch
   Resultado esperado:
       Se muestran recomendaciones relajadas disponibles para Nintendo Switch.

10. Mensaje:
       Quiero un RPG para PC
    Resultado esperado:
       Se aplican las restricciones obligatorias de género y plataforma.

C. Próximos lanzamientos y paginación
11. Mensaje:
       Quiero próximos lanzamientos RPG para PC
    Resultado esperado:
       Se muestran únicamente videojuegos con fechas futuras compatibles con RPG y PC.

12. Mensaje posterior:
       Dame otros 5
    Resultado esperado:
       Se muestran más resultados sin repetir los anteriores, si existen candidatos suficientes.

13. Mensaje:
       Quiero próximos lanzamientos de acción para PC
    Resultado esperado:
       Se muestran próximos lanzamientos del género acción disponibles para PC.

D. Memoria conversacional y fichas informativas
14. Mensaje:
       Quiero un juego relajado para Nintendo Switch
    Mensaje posterior:
       Detalles del 2
    Resultado esperado:
       Se muestra la ficha informativa del segundo juego de la lista anterior.

15. Mensaje posterior:
       Quiero que me expliques de qué trata el último
    Resultado esperado:
       Se muestra la ficha del último videojuego recomendado.

16. Mensaje:
       Dame una guía de Minecraft
    Resultado esperado:
       Se muestra información detallada de Minecraft recuperada desde RAWG.

17. Mensaje:
       Quiero que me expliques de qué trata Ring Fit Adventure
    Resultado esperado:
       Se busca el videojuego por nombre y se muestra su información detallada.

E. Consejos almacenados
18. Mensaje:
       Dame consejos para Minecraft
    Resultado esperado:
       Se muestran consejos iniciales almacenados para Minecraft.

19. Mensaje:
       Consejos de Stardew Valley
    Resultado esperado:
       Se muestran consejos iniciales almacenados para Stardew Valley.

F. Steam
Para estas pruebas se necesita una biblioteca pública y un SteamID64 válido de 17 dígitos, nosotros hemos probado con 76561198011775992, una ID de un perfil público de Steam.

20. Mensaje:
       Cargar Steam 76561198011775992
    Resultado esperado:
       El chatbot indica que la biblioteca ha sido cargada y muestra el número de juegos visibles.

21. Mensaje posterior:
       Dime mis juegos más jugados
    Resultado esperado:
       Se muestra una lista ordenada por horas de juego.

22. Mensaje posterior:
       Recomiéndame un RPG de mi biblioteca
    Resultado esperado:
       Se recomiendan únicamente juegos RPG que pertenecen a la biblioteca cargada.

23. Mensaje posterior:
       Recomiéndame algo relajado de mi biblioteca
    Resultado esperado:
       Se recomiendan únicamente juegos compatibles con la preferencia y presentes en la biblioteca.

G. Reinicio y errores controlados
24. Mensaje:
       reset
    Resultado esperado:
       Se limpia el contexto conversacional.

25. Mensaje:
       Cargar Steam 1234
    Resultado esperado:
       El chatbot informa de que no se ha encontrado un SteamID64 válido.

26. Mensaje:
       Quiero un juego
    Resultado esperado:
       El chatbot solicita información adicional en lugar de inventar una recomendación.
