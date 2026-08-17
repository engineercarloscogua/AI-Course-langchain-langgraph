# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                    CHATBOT CON LANGCHAIN Y STREAMLIT                        ║
# ║                          (Versión Educativa)                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# ==============================================================================
# PASO 1: IMPORTAR LAS LIBRERÍAS NECESARIAS
# ==============================================================================
# Cuando importas una librería, le dices a Python que cargue todo el código
# de esa librería para que puedas usarlo en tu programa.

# 1.1) Importar ChatOpenAI
# ¿QUÉ HACE? Proporciona la clase ChatOpenAI que conecta con los servidores
#            de OpenAI y accede a modelos como GPT-4, GPT-3.5-turbo, etc.
# ¿CÓMO FUNCIONA? Cuando creas una instancia de ChatOpenAI, establece una
#                 conexión HTTP con la API de OpenAI. Cuando le envías un
#                 mensaje, OpenAI procesa tu texto y devuelve una respuesta.
from langchain_openai import ChatOpenAI

# 1.2) Importar las clases de mensajes
# ¿QUÉ SON? Son clases que organizan y estructuran los mensajes en tipos:
#
# - HumanMessage: Representa lo que escribe EL USUARIO
#   Ejemplo: HumanMessage(content="¿Cuál es la capital de Francia?")
#
# - AIMessage: Representa lo que responde LA IA/CHATBOT
#   Ejemplo: AIMessage(content="La capital de Francia es París")
#
# - SystemMessage: Instrucciones ESPECIALES para la IA (su "personalidad")
#   Ejemplo: SystemMessage(content="Eres un asistente amigable")
#
# ¿PARA QUÉ SIRVEN? El modelo de OpenAI entiende mejor los mensajes cuando
#                   están estructurados así. Es como darle contexto:
#                   "esto vino de un humano", "esto vino de la IA", etc.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# 1.3) Importar PromptTemplate
# ¿QUÉ HACE? Te permite crear PLANTILLAS de texto dinámicas.
#            Es como un formato con "espacios en blanco" que rellenas después.
#
# EJEMPLO:
#   template = "Hola {nombre}, tienes {edad} años"
#   Luego reemplazas {nombre} = "Juan" y {edad} = 25
#   Resultado: "Hola Juan, tienes 25 años"
#
# ¿POR QUÉ USAR ESTO? Te permite reutilizar el mismo formato para diferentes
#                     mensajes sin escribir el texto completo cada vez.
from langchain_core.prompts import PromptTemplate

# 1.4) Importar Streamlit
# ¿QUÉ HACE? Es una librería para crear INTERFACES WEB sin necesidad de HTML/CSS
#            Crea botones, cajas de texto, mensajes, etc. automáticamente.
#
# ¿CÓMO FUNCIONA? Streamlit ejecuta tu script de arriba a abajo cada vez que
#                 algo cambia (usuario escribe algo, presiona un botón, etc.)
#                 Es diferente a las apps web normales.
import streamlit as st


# ==============================================================================
# PASO 2: CONFIGURAR LA PÁGINA DE STREAMLIT
# ==============================================================================
# Estas son CONFIGURACIONES globales que afectan a toda la página

# 2.1) Configurar los detalles de la página
# ¿QUÉ HACEN?
# - page_title: El texto que aparece en la pestaña del navegador
# - page_icon: El emoji/icono que aparece al lado del título en la pestaña
#
# NOTA: Esto debe ir al inicio del script, antes de cualquier código de Streamlit
st.set_page_config(
    page_title="Asistente del Inge Charlee",  # Nombre en la pestaña del navegador
    page_icon="🤖"                             # Emoji que aparece en la pestaña
)


# ==============================================================================
# PASO 3: AGREGAR LA IMAGEN CENTRADA (ANTES DEL TÍTULO)
# ==============================================================================
# ¿POR QUÉ HACEMOS ESTO? Para que la app sea más visual y amigable

# 3.1) Crear columnas para centrar la imagen
# ¿CÓMO FUNCIONA st.columns()?
#   - Divide la pantalla en partes iguales
#   - El parámetro [1, 2, 1] significa:
#     * Columna 1: 1 parte (vacía, para espaciado)
#     * Columna 2: 2 partes (aquí va la imagen, más ancha)
#     * Columna 3: 1 parte (vacía, para espaciado)
#   - Esto CENTRA la imagen automáticamente
#
# RESULTADO VISUAL:
#   [vacío]  [  IMAGEN  ]  [vacío]
col1, col2, col3 = st.columns([1, 2, 1])

# 3.2) Mostrar la imagen en la columna del medio
# ¿QUÉ HACE st.image()?
#   - Muestra una imagen en la app
#   - Puede ser una URL de internet O un archivo local
#
# NOTA: "with col2:" significa "haz esto DENTRO de la columna 2"
#       Cualquier código dentro de este bloque aparecerá en esa columna
with col2:
    # Opción A: Usar una imagen desde internet (URL)
    # VENTAJA: No necesitas guardar archivos en tu computadora
    # DESVENTAJA: Requiere conexión a internet
    imagen_url = "https://yt3.googleusercontent.com/XxA1oxEztYFUmMn3F2cJOsv-xGpggDxapUHt45uFt73MVBHrbnXwVxnowtHCxO9RykG-c0P7aQ=s160-c-k-c0x00ffffff-no-rj"
    st.image(imagen_url, width=200)  # width=200 significa 200 píxeles de ancho
    
    # Opción B: Usar una imagen local (descomentar si la necesitas)
    # VENTAJA: No depende de internet
    # DESVENTAJA: Debes guardar la imagen en tu carpeta
    # st.image("ruta/a/tu/imagen.png", width=200)
    # Ejemplo: st.image("imagenes/chatbot.png", width=200)


# ==============================================================================
# PASO 4: AGREGAR TÍTULOS Y DESCRIPCIÓN
# ==============================================================================
# Son los textos que ven los usuarios - la parte "decorativa" pero importante

# 4.1) Título principal (el más grande)
# ¿QUÉ HACE st.title()?
#   - Crea un título tipo H1 (como en HTML)
#   - Es el texto más grande de la página
#   - El 🤖 es un emoji que está incluido en el texto
st.title("🤖 Chatbot Básico por El Inge Charlee")

# 4.2) Descripción/instrucciones (texto con formato)
# ¿QUÉ HACE st.markdown()?
#   - Permite escribir texto con FORMATO MARKDOWN
#   - Markdown es un lenguaje simple para dar formato:
#     * ### = Subtítulo
#     * **texto** = negritas
#     * - item = lista con puntos
#     * [texto](url) = enlaces
#   - Es como escribir en Word pero con símbolos simples
st.markdown(
    """
    ### Bienvenido al Chatbot  🤖
    
    Aquí puedes:
    - Escribir preguntas o comentarios
    - Recibir respuestas inteligentes usando IA
    - Ver el historial de la conversación
    
    **Escribe tu mensaje en el cuadro de abajo y presiona Enter** ⬇️
    """
)


# ==============================================================================
# PASO 5: CONFIGURAR EL MODELO DE IA (LangChain + OpenAI)
# ==============================================================================
# Aquí inicializamos el "cerebro" del chatbot
# Este es el corazón del chatbot - aquí conectamos con OpenAI

# IMPORTANTE: Para que esto funcione necesitas tener tu API KEY de OpenAI
#             Streamlit la busca automáticamente en la variable de entorno
#             OPENAI_API_KEY (debes configurarla en tu sistema)

# ==============================================================================
#  BARRA DE NAVEGACIÓN (SIDEBAR)
# ==============================================================================
# ¿QUÉ ES EL SIDEBAR?
#   - Es una columna al LADO IZQUIERDO de la pantalla
#   - Es un lugar perfecto para CONFIGURACIONES y CONTROLES
#   - Cosas que no necesitas ver todo el tiempo pero quieres poder cambiar
#
# ¿CÓMO FUNCIONA "with st.sidebar:"?
#   - Todo lo que está INDENTADO dentro de este bloque
#   - Aparecerá en el sidebar, no en la zona principal

with st.sidebar:
    # Mostrar un título en el sidebar
    st.header("Configuración")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTROL 1: SLIDER DE TEMPERATURA
    # ─────────────────────────────────────────────────────────────────────────
    # ¿QUÉ ES TEMPERATURA?
    #   - Un número entre 0.0 y 1.0 que controla la "creatividad" del modelo
    #   - TEMPERATURA = 0.0: El modelo es PREDECIBLE y CONSISTENTE
    #     * Siempre da respuestas similares
    #     * Perfecto para cosas que necesitan ser exactas
    #   - TEMPERATURA = 1.0: El modelo es MÁS CREATIVO y VARIADO
    #     * Cada respuesta puede ser diferente
    #     * Perfecto para conversaciones naturales
    #   - TEMPERATURA = 0.5: BALANCE entre ambos (lo más común)
    #
    # ¿QUÉ HACE st.slider()?
    #   - Crea un control deslizable (slider) en la pantalla
    #   - Parámetros: (nombre, min, max, valor_inicial, incremento)
    temperature = st.slider(
        "Temperatura",      # Nombre que se muestra
        0.0,               # Valor mínimo
        1.0,               # Valor máximo
        0.5,               # Valor inicial (por defecto)
        0.1                # Incremento cuando el usuario mueve el slider
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTROL 2: SELECTOR DE MODELO
    # ─────────────────────────────────────────────────────────────────────────
    # ¿QUÉ HACE st.selectbox()?
    #   - Crea un DROPDOWN (menú desplegable) para elegir una opción
    #   - El usuario puede seleccionar solo UNA opción de la lista
    #
    # ¿QUÉ SON ESTOS MODELOS?
    #   - gpt-3.5-turbo: Modelo RÁPIDO y BARATO (bueno para empezar)
    #   - gpt-4: Modelo MÁS INTELIGENTE pero MÁS LENTO y CARO
    #   - gpt-4o-mini: Modelo NUEVO, balance entre velocidad y inteligencia
    model_name = st.selectbox(
        "Modelo",                                          # Etiqueta
        ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]        # Opciones disponibles
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # CREAR LA INSTANCIA DE ChatOpenAI CON LOS PARÁMETROS CONFIGURABLES
    # ─────────────────────────────────────────────────────────────────────────
    # ¿QUÉ OCURRE AQUÍ?
    #   1. El usuario mueve el slider de temperatura → cambio de temperatura
    #   2. El usuario selecciona un modelo diferente → cambio de modelo
    #   3. Streamlit RE-EJECUTA TODO EL SCRIPT (flujo importante)
    #   4. Se crea una NUEVA instancia de ChatOpenAI con los nuevos valores
    #   5. Los cambios se aplican inmediatamente
    #
    # ¿CÓMO FUNCIONA ChatOpenAI?
    #   - Es una clase que representa una CONEXIÓN con OpenAI
    #   - Cuando creas un ChatOpenAI(...), NO se conecta aún
    #   - La conexión ocurre cuando USAS ese objeto (cuando le envías un mensaje)
    #   - Parámetros:
    #     * model: Qué modelo usar (gpt-3.5-turbo, gpt-4, etc.)
    #     * temperature: El parámetro que controla creatividad
    #     * Automáticamente busca la API KEY en la variable OPENAI_API_KEY
    
    chat_model = ChatOpenAI(
        model=model_name,        # El modelo seleccionado en el selectbox
        temperature=temperature  # La temperatura del slider
    )


# ==============================================================================
# BOTÓN PARA ELIMINAR LA CONVERSACIÓN (NUEVA SESIÓN)
# ==============================================================================
# ¿QUÉ HACE st.button()?
#   - Crea un BOTÓN clickeable
#   - Devuelve True cuando el usuario lo presiona, False en caso contrario
#
# ¿QUÉ OCURRE CUANDO PRESIONAS EL BOTÓN?
#   1. st.button("⛔ Nueva conversación") devuelve True
#   2. Entra en el bloque if
#   3. st.session_state.mensajes = [] → BORRA todos los mensajes guardados
#   4. st.rerun() → REINICIA el script (como si recargaras la página)
#   5. Como el historial está vacío, empiezas con una conversación limpia

if st.button("⛔ Nueva conversación"):
    # BORRA el historial de mensajes
    st.session_state.mensajes = []
    # REINICIA el script desde el principio
    st.rerun()


# ==============================================================================
# PASO 6: MANEJO DE MEMORIA (Almacenar el historial de mensajes)
# ==============================================================================
# Este es un concepto MUY IMPORTANTE - explicado en detalle:

# ¿CÓMO FUNCIONA STREAMLIT?
#   - Streamlit ejecuta tu script de ARRIBA A ABAJO cada vez que algo cambia
#   - Ejemplo: Usuario escribe mensaje → Script se ejecuta → Muestra respuesta
#   - PROBLEMA: Las variables normales de Python se pierden después
#   - SOLUCIÓN: Usar st.session_state para guardar datos entre ejecuciones
#
# ¿QUÉ ES st.session_state?
#   - Es un diccionario ESPECIAL que Streamlit mantiene vivo
#   - Guarda datos mientras el usuario navega en la app
#   - Se borra SOLO cuando el usuario cierra la navegador/pestaña
#   - Es como un almacén temporal para cada sesión de usuario
#
# ANALOGÍA:
#   - VARIABLE NORMAL: Tu dinero en el bolsillo (se pierde si reinicias el programa)
#   - st.session_state: Tu dinero en el banco (se mantiene aunque reinicies)

# 6.1) Verificar si YA EXISTE un historial de mensajes
# ¿CÓMO FUNCIONA "if 'mensajes' not in st.session_state:"?
#   - Pregunta: ¿Existe una clave llamada "mensajes" en session_state?
#   - Si NO existe (primera vez que visitas la app):
#     * Crea una lista vacía: []
#   - Si YA existe (vuelves a la app):
#     * No hace nada, mantiene los mensajes anteriores

if "mensajes" not in st.session_state:
    # PRIMERA VEZ: Crear lista vacía de mensajes
    st.session_state.mensajes = []
    print("✓ Historial de mensajes inicializado")

# NOTA: El print() es para tu consola (donde ejecutas streamlit run)
#       Los usuarios NO ven esto, es solo para debugging/desarrollo


# ==============================================================================
# PASO 7: CREAR LA PLANTILLA DE PROMPT (COMPORTAMIENTO DEL CHATBOT)
# ==============================================================================
# Aquí definimos CÓMO debe responder el chatbot - su "personalidad" e instrucciones

# ¿QUÉ ES ESTO?
#   - Una PLANTILLA que le dice al modelo cómo debe comportarse
#   - Tiene variables dinámicas {variable} que se rellenan después
#
# ¿CÓMO FUNCIONA?
#   1. Defines la plantilla con variables como {mensaje} y {historial}
#   2. Luego remplazas esas variables con valores reales
#   3. El texto completo se envía al modelo de OpenAI
#
# ¿VARIABLES EN LA PLANTILLA?
#   - input_variables: Lista de variables que NECESITA la plantilla
#     * En este caso: "mensaje" (lo que pregunta el usuario)
#     * En este caso: "historial" (la conversación anterior)
#   - template: El formato con {variables} entre llaves

prompt_template = PromptTemplate(
    input_variables=["mensaje", "historial"],
    template="""
        Eres un asistente útil y amigable llamado Viernes.
        
        Historial de conversación:
        {historial}
        
        Responde inicialmente con mi nombre Inge Carlos. Después en un párrafo de máximo 20 palabras 
        y mínimo 8 palabras, de manera resumida, clara y concisa la siguiente pregunta: {mensaje}
    """
)

# NOTA IMPORTANTE sobre la plantilla:
#   - La línea "Eres un asistente..." = SYSTEM PROMPT
#     * Esto le dice al modelo cómo debe comportarse
#     * Le da una "personalidad"
#   - "{historial}" = Se reemplaza con la conversación anterior
#     * El modelo ve TODO lo que pasó antes
#     * Por eso "entiende" el contexto
#   - "{mensaje}" = La pregunta actual del usuario
#     * Es lo que el usuario acaba de escribir


# ==============================================================================
# PASO 8: CREAR LA CADENA LCEL (Language Chain Expression Language)
# ==============================================================================
# Este es un concepto FUNDAMENTAL de LangChain - muy importante:

# ¿QUÉ ES LCEL?
#   - LCEL = Language Chain Expression Language
#   - Es una forma MODERNA de LangChain para encadenar componentes
#   - Se pronuncia "local" (que es lo que intenta sonar)
#   - Permite conectar componentes con el operador "|" (pipe/tubería)
#
# ¿CÓMO FUNCIONA?
#   prompt_template | chat_model
#   
#   Significa:
#   1. PRIMERO: Procesa con prompt_template
#      * Rellena las variables {mensaje} y {historial}
#      * Produce un texto completo formateado
#   2. LUEGO: Envía el resultado a chat_model
#      * El texto completo llega a OpenAI
#      * OpenAI procesa y devuelve una respuesta
#   3. RESULTADO: Una cadena que puedes usar con .stream() o .invoke()
#
# ANALOGÍA:
#   - Es como una TUBERÍA: entrada → procesa 1 → procesa 2 → salida
#   - Entrada: {"mensaje": "¿Qué es IA?", "historial": "..."}
#   - Proceso 1: prompt_template rellena el template
#   - Proceso 2: chat_model envía a OpenAI
#   - Salida: Respuesta del modelo

cadena = prompt_template | chat_model

# NOTA: En este momento NO se ejecuta nada
#       Solo creas la "receta" de qué hacer
#       Se ejecuta después cuando llamas .stream() o .invoke()


# ==============================================================================
# PASO 9: MOSTRAR EL HISTORIAL DE MENSAJES ANTERIORES EN PANTALLA
# ==============================================================================
# Aquí mostramos TODOS los mensajes guardados en st.session_state.mensajes
# Esto hace que el usuario vea toda la conversación anterior

# ¿CÓMO FUNCIONA?
#   - for msg in st.session_state.mensajes:
#     * Itera sobre CADA mensaje guardado
#     * msg puede ser un HumanMessage, AIMessage o SystemMessage

for msg in st.session_state.mensajes:
    
    # 9.1) Saltarse los mensajes del sistema
    # ¿POR QUÉ?
    #   - Los SystemMessage son instrucciones PARA el modelo
    #   - NO son parte de la conversación visible
    #   - El usuario NO necesita verlos
    #
    # EJEMPLO:
    #   - SystemMessage: "Eres un asistente amigable" ← NO mostrar
    #   - HumanMessage: "¿Cuál es la capital de Francia?" ← MOSTRAR
    #   - AIMessage: "La capital es París" ← MOSTRAR
    
    if isinstance(msg, SystemMessage):
        # isinstance() pregunta: ¿Es este objeto de tipo SystemMessage?
        # Si es True → continue (salta a la siguiente iteración)
        continue  # Saltamos este mensaje, no lo mostramos
    
    # 9.2) Determinar quién escribió el mensaje (usuario o IA)
    # ¿CÓMO FUNCIONA?
    #   - isinstance(msg, AIMessage) pregunta: ¿Es un mensaje de la IA?
    #   - Si sí → role = "assistant" (así se llama la IA en Streamlit)
    #   - Si no → role = "user" (fue el usuario quien escribió)
    
    role = "assistant" if isinstance(msg, AIMessage) else "user"
    
    # 9.3) Mostrar el mensaje con el estilo correcto de chat
    # ¿QUÉ HACE st.chat_message()?
    #   - Crea un "globo" de mensaje de chat (como en WhatsApp)
    #   - Automáticamente formatea diferente según sea "user" o "assistant"
    #   - Los mensajes del usuario aparecen a la derecha
    #   - Los mensajes del asistente aparecen a la izquierda
    #   - Además agrega un avatar automáticamente
    
    with st.chat_message(role):
        # msg.content es el TEXTO del mensaje
        # .markdown() permite mostrar el texto con formato
        st.markdown(msg.content)


# ==============================================================================
# PASO 10: CAMPO DE ENTRADA DEL USUARIO
# ==============================================================================
# Aquí el usuario ESCRIBE sus mensajes

# ¿QUÉ HACE st.chat_input()?
#   - Crea un cuadro de ENTRADA especial para chatbots
#   - El usuario escribe algo y presiona ENTER
#   - IMPORTANTE: Devuelve lo que escribió el usuario
#   - Si el usuario NO ha escrito nada devuelve None
#
# ¿CUÁNDO SE EJECUTA?
#   - Solo se ejecuta cuando el usuario presiona ENTER
#   - Es diferente a otros inputs que ejecutan el código mientras escribes

pregunta = st.chat_input("Escribe tu mensaje aquí: ")

# ¿QUÉ SIGNIFICA "if pregunta:"?
#   - Pregunta: ¿La variable pregunta tiene un valor?
#   - Si pregunta = "Hola" → True (entra en el if)
#   - Si pregunta = None (usuario no escribió nada) → False (no entra)
#   - En Python, una cadena de texto vacía "" también es False

if pregunta:
    # Aquí entra SOLO cuando el usuario escribió algo y presionó ENTER
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 11: MOSTRAR EL MENSAJE DEL USUARIO EN PANTALLA
    # ─────────────────────────────────────────────────────────────────────────
    
    print(f"Usuario escribió: {pregunta}")  # Para debugging en consola
    
    # ¿QUÉ HACE st.chat_message("user")?
    #   - Crea un "globo" de chat para el usuario (como en WhatsApp)
    #   - Muestra el mensaje a la derecha (estilo usuario)
    
    with st.chat_message("user"):
        # st.markdown() muestra el texto
        st.markdown(pregunta)
    
    print("✓ Mensaje del usuario mostrado en pantalla")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 12: OBTENER LA RESPUESTA DEL MODELO (con STREAMING)
    # ─────────────────────────────────────────────────────────────────────────
    
    # MANEJO DE ERRORES: try-except
    # ¿POR QUÉ?
    #   - El código puede fallar por varias razones:
    #     * API KEY incorrecta o ausente
    #     * Problema de conexión a internet
    #     * Cuota de API excedida
    #   - try-except evita que la app "se bloquee" en error
    #   - En su lugar, moestra un mensaje de error amigable
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # CREAR UN "GLOBO" DE CHAT PARA LA RESPUESTA DEL ASISTENTE
        # ─────────────────────────────────────────────────────────────────────
        # st.chat_message("assistant") crea el globo para la respuesta
        
        with st.chat_message("assistant"):
            
            # ─────────────────────────────────────────────────────────────────
            # STREAMING (Mostrar la respuesta en TIEMPO REAL)
            # ─────────────────────────────────────────────────────────────────
            # ¿QUÉ ES STREAMING?
            #   - La respuesta NO se muestra de golpe
            #   - Se muestra palabra por palabra, como si escribiera
            #   - Mucho mejor UX (experiencia de usuario)
            #   - El usuario ve cómo se escribe la respuesta
            #
            # ¿CÓMO FUNCIONA?
            #   1. response_placeholder = st.empty() crea un espacio vacío
            #   2. for chunk in cadena.stream(...) itera por fragmentos
            #   3. Cada fragmento es un pequeño pedazo de respuesta
            #   4. Vamos concatenando fragmentos en full_response
            #   5. Mostramos full_response actualizado cada iteración
            
            # Crear un "contenedor" vacío donde mostraremos la respuesta
            # st.empty() devuelve un objeto que podemos actualizar
            response_placeholder = st.empty()
            
            # Variable para acumular la respuesta completa
            full_response = ""
            
            # ┌─────────────────────────────────────────────────────────────┐
            # │ cadena.stream() → STREAMING DE LA CADENA LCEL               │
            # └─────────────────────────────────────────────────────────────┘
            # ¿QUÉ HACE .stream()?
            #   - Ejecuta la cadena (prompt_template | chat_model)
            #   - Devuelve un ITERADOR que emite fragmentos
            #   - Parámetro: Un diccionario con los valores para el template
            #     * {"mensaje": pregunta, ...} rellena {mensaje} con pregunta
            #
            # ¿POR QUÉ stream() Y NO invoke()?
            #   - invoke() devuelve la respuesta COMPLETA de una vez
            #   - stream() devuelve la respuesta FRAGMENTO POR FRAGMENTO
            #   - stream() es mejor para UX porque el usuario ve el progreso
            
            for chunk in cadena.stream(
                {
                    "mensaje": pregunta,                      # Lo que preguntó el usuario
                    "historial": st.session_state.mensajes    # Conversación anterior
                }
            ):
                # ¿QUÉ ES chunk?
                #   - Un objeto que representa un fragmento de respuesta
                #   - chunk.content es el TEXTO de ese fragmento
                #   - Normalmente son palabras o partes de palabras
                
                # Agregar el fragmento a la respuesta completa
                full_response += chunk.content
                
                # Actualizar la pantalla CON CURSOR PARPADEANTE
                # El "█ " es un bloque visual que simula un cursor
                # Esto da la ilusión de que el modelo está escribiendo
                response_placeholder.markdown(full_response + "█ ")
            
            # Una vez terminado el streaming, mostrar SIN CURSOR
            # Quitamos el "█ " para que la respuesta se vea limpia
            response_placeholder.markdown(full_response)
        
        # ─────────────────────────────────────────────────────────────────────
        # GUARDAR LOS MENSAJES EN st.session_state
        # ─────────────────────────────────────────────────────────────────────
        # ¿POR QUÉ HACER ESTO?
        #   - Para que el historial PERSISTA entre ejecuciones
        #   - Si no lo guardamos, al refrescar se pierde todo
        #   - st.session_state mantiene estos datos vivos
        #
        # ¿QUÉ GUARDAMOS?
        #   1. HumanMessage(content=pregunta)
        #      - El mensaje que escribió el usuario
        #   2. AIMessage(content=full_response)
        #      - La respuesta completa que generó la IA
        
        # Agregar el mensaje del usuario al historial
        st.session_state.mensajes.append(HumanMessage(content=pregunta))
        
        # Agregar la respuesta del asistente al historial
        st.session_state.mensajes.append(AIMessage(content=full_response))
        
        # NOTA IMPORTANTE:
        #   - Estos mensajes aparecerán en el SIGUIENTE ciclo del script
        #   - Cuando Streamlit vuelve a ejecutar todo (rerun automático)
        #   - El loop "for msg in st.session_state.mensajes" los mostrará
    
    except Exception as e:
        # Si hay ERROR, mostramos un mensaje amigable
        # ¿QUÉ HACE st.error()?
        #   - Muestra un cuadro rojo con un mensaje de error
        #   - Muy visible para el usuario
        #
        # str(e) convierte el error a texto
        st.error(f"Error al generar respuesta: {str(e)}")
        
        # Mostrar un consejo útil
        # ¿QUÉ HACE st.info()?
        #   - Muestra un cuadro azul con información
        #   - Menos urgente que error()
        st.info("Verifica que tu API key de OpenAI esté configurada correctamente")


# ==============================================================================
# NOTAS EDUCATIVAS: RESUMEN DEL FLUJO COMPLETO
# ==============================================================================
#
# FLUJO PASO A PASO:
#
# 1. Usuario abre la app → Streamlit ejecuta el script de arriba a abajo
#    - Carga las importaciones
#    - Crea la interfaz (título, imagen, botones, etc.)
#    - El historial está vacío (primer if en paso 6)
#    - Muestra el chat_input
#
# 2. Usuario escribe "Hola" y presiona ENTER
#    - Streamlit REINICIA el script (rerun automático)
#    - pregunta = "Hola" (ya no es None)
#    - Entra en "if pregunta:"
#    - Muestra "Hola" en un globo de usuario
#
# 3. El código llama a cadena.stream(...)
#    - prompt_template rellena variables
#    - chat_model envía a OpenAI
#    - Recibe fragmentos de respuesta (streaming)
#    - Muestra cada fragmento en tiempo real
#
# 4. Guarda ambos mensajes en st.session_state.mensajes
#    - HumanMessage("Hola")
#    - AIMessage("Hola, ¿cómo estás?")
#
# 5. El script TERMINA (ya no hay más código)
#    - Los mensajes están guardados
#    - El usuario ve la conversación completa
#
# 6. Usuario escribe "¿Qué es IA?" y presiona ENTER
#    - Streamlit REINICIA otra vez
#    - El loop en paso 9 AHORA ve los 2 mensajes anteriores
#    - Los muestra primero (historial)
#    - Luego muestra el nuevo mensaje
#    - El modelo VE TODO el contexto → responde mejor
#
# ─────────────────────────────────────────────────────────────────────────────
#
# CONCEPTOS CLAVE APRENDIDOS:
#
# st.session_state    → Memoria entre ejecuciones
# st.chat_message()   → Globos de chat visual
# st.chat_input()     → Entrada de usuario
# .stream()           → Mostrar respuesta fragmento por fragmento
# prompt_template     → Plantilla con variables dinámicas
# LangChain LCEL      → Encadenar componentes con |
# try-except          → Manejo de errores
# Streamlit rerun     → El script se ejecuta cuando algo cambia
#
# ==============================================================================

print("=" * 80)
print("CHATBOT INICIADO CORRECTAMENTE ✓")
print("=" * 80)