# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                    CHATBOT CON LANGCHAIN Y STREAMLIT                        ║
# ║                          (Versión Educativa)                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# ==============================================================================
# PASO 1: IMPORTAR LAS LIBRERÍAS NECESARIAS
# ==============================================================================


# 1.1) Importar ChatOpenAI
# Esto es el MOTOR del chatbot - conecta con el modelo de OpenAI (GPT-4)
from langchain_openai import ChatOpenAI

# 1.2) Importar las clases de mensajes
# Estas clases ayudan a organizar los mensajes en tipos:
# - HumanMessage: Lo que escribe el usuario
# - AIMessage: Lo que responde la IA
# - SystemMessage: Instrucciones para la IA (como su "personalidad")
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# 1.3) Importar Streamlit
# Streamlit es la librería que crea la INTERFAZ (lo visual) del chatbot
# Sirve para crear botones, cajas de texto, mostrar mensajes, etc.
import streamlit as st

# ==============================================================================
# PASO 2: CONFIGURAR LA PÁGINA DE STREAMLIT
# ==============================================================================

# 2.1) Configurar los detalles de la página
# page_title: Lo que sale en la pestaña del navegador
# page_icon: El icono pequeñito que aparece al lado del título
st.set_page_config(
    page_title="Asistente del Inge Charlee",  # Nombre en la pestaña del navegador
    page_icon="🤖"                             # Emoji que aparece en la pestaña
)
# ==============================================================================
# PASO 3: AGREGAR LA IMAGEN CENTRADA (ANTES DEL TÍTULO)
# ==============================================================================
# Aquí mostramos una imagen bonita al inicio de la página

# 3.1) Crear una columna para centrar la imagen
# st.columns() divide la pantalla en partes iguales
# Usamos 3 columnas: vacía, imagen, vacía (esto centra la imagen)
col1, col2, col3 = st.columns([1, 2, 1])

# 3.2) Mostrar la imagen en la columna del medio
with col2:
    # Aquí puedes usar una URL de imagen de internet o una imagen local
    # OPCIÓN A: Usando URL de internet (recomendado para principiantes)
    imagen_url = "https://yt3.googleusercontent.com/XxA1oxEztYFUmMn3F2cJOsv-xGpggDxapUHt45uFt73MVBHrbnXwVxnowtHCxO9RykG-c0P7aQ=s160-c-k-c0x00ffffff-no-rj"  # Imagen de chatbot
    st.image(imagen_url, width=200)  # width=200 es el ancho en píxeles
    
    # OPCIÓN B: Si tienes una imagen local (descomenta si la necesitas)
    # st.image("ruta/a/tu/imagen.png", width=200)
    # Ejemplo: st.image("imagenes/chatbot.png", width=200)


# ==============================================================================
# PASO 4: AGREGAR TÍTULOS Y DESCRIPCIÓN
# ==============================================================================
# Son los textos que ven los usuarios en la pantalla

# 4.1) Título principal (el más grande)
st.title("🤖 Chatbot Básico por El Inge Charlee")

# 4.2) Subtítulo o descripción (texto más pequeño)
# markdown() permite usar formato especial como negritas, enlaces, etc.
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

# 5.1) Crear una instancia de ChatOpenAI
# model="gpt-4o-mini": Usamos el modelo GPT-4 mini (más barato y rápido)
# temperature=0.5: Controla la "creatividad" (0=predecible, 1=creativo)
chat_model = ChatOpenAI(
    model="gpt-4o-mini",     # El modelo a usar
    temperature=0.5          # Temperatura (balance entre certeza y creatividad)
)

print("✓ Modelo de IA configurado correctamente")


# ==============================================================================
# PASO 6: MANEJO DE MEMORIA (Almacenar el historial de mensajes)
# ==============================================================================
# Streamlit borra los datos cada vez que refrescas la página
# Para evitar esto, usamos "session_state" que guarda datos mientras navega

# 6.1) Verificar si ya existe un historial de mensajes
# "st.session_state" es como un diccionario especial de Streamlit
# Preguntamos: ¿Ya existe una lista llamada "mensajes"?
if "mensajes" not in st.session_state:
    # Si NO existe, la creamos (vacía al principio)
    st.session_state.mensajes = []
    print("✓ Historial de mensajes inicializado")

# 6.2) Mostrar los mensajes anteriores en la pantalla
# Este loop recorre TODOS los mensajes guardados
for msg in st.session_state.mensajes:
    
    # 6.2.1) Saltarse los mensajes del sistema
    # Los SystemMessage son instrucciones para la IA, no se muestran
    if isinstance(msg, SystemMessage):
        continue  # Saltamos este mensaje
    
    # 6.2.2) Determinar quién escribió el mensaje
    # Si es un AIMessage → role = "assistant"
    # Si es un HumanMessage → role = "user"
    role = "assistant" if isinstance(msg, AIMessage) else "user"
    
    # 6.2.3) Mostrar el mensaje con el estilo correcto
    # st.chat_message() dibuja el mensaje como un "globo" de chat
    with st.chat_message(role):
        # msg.content es el texto del mensaje
        st.markdown(msg.content)


# ==============================================================================
# PASO 7: CAMPO DE ENTRADA DEL USUARIO
# ==============================================================================
# Aquí el usuario escribe sus mensajes

# 7.1) Crear el cuadro de input
# st.chat_input() es especial para chatbots
# Devuelve el texto si el usuario presiona Enter, sino devuelve None
pregunta = st.chat_input("Escribe tu mensaje aquí: ")

# 7.2) Verificar si el usuario escribió algo
# El código dentro de este "if" solo se ejecuta si hay texto
if pregunta:
    print(f"Usuario escribió: {pregunta}")  # Para debugging
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 8: MOSTRAR EL MENSAJE DEL USUARIO EN PANTALLA
    # ─────────────────────────────────────────────────────────────────────────
    
    # 8.1) Mostrar el mensaje del usuario como un "globo" de chat
    with st.chat_message("user"):
        st.markdown(pregunta)
    
    print("✓ Mensaje del usuario mostrado en pantalla")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 9: GUARDAR EL MENSAJE EN LA MEMORIA
    # ─────────────────────────────────────────────────────────────────────────
    
    # 9.1) Convertir el texto en un objeto HumanMessage
    # Esto lo hace compatible con LangChain
    mensaje_usuario = HumanMessage(content=pregunta)
    
    # 9.2) Agregar el mensaje a la lista de historial
    # Ahora el mensaje se guarda permanentemente en esta sesión
    st.session_state.mensajes.append(mensaje_usuario)
    
    print("✓ Mensaje guardado en el historial")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 10: OBTENER RESPUESTA DEL MODELO DE IA
    # ─────────────────────────────────────────────────────────────────────────
    
    # 10.1) Enviar TODOS los mensajes al modelo
    # LangChain recibe el historial completo para que la IA tenga contexto
    # Así la IA "recuerda" la conversación anterior
    respuesta = chat_model.invoke(st.session_state.mensajes)
    
    print("✓ Respuesta recibida del modelo")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 11: MOSTRAR LA RESPUESTA DE LA IA EN PANTALLA
    # ─────────────────────────────────────────────────────────────────────────
    
    # 11.1) Mostrar la respuesta como un "globo" de chat del asistente
    with st.chat_message("assistant"):
        # respuesta.content extrae el texto de la respuesta
        st.markdown(respuesta.content)
    
    print("✓ Respuesta mostrada en pantalla")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PASO 12: GUARDAR LA RESPUESTA EN LA MEMORIA
    # ─────────────────────────────────────────────────────────────────────────
    
    # 12.1) Agregar la respuesta de la IA al historial
    # "respuesta" ya es un AIMessage, así que la agregamos directamente
    st.session_state.mensajes.append(respuesta)
    
    print("✓ Respuesta guardada en el historial")


# ==============================================================================
# INFORMACIÓN ADICIONAL PARA PRINCIPIANTES
# ==============================================================================
# 
# ¿QUÉ ES CADA COSA?
# 
# 1. LangChain: Una librería que facilita trabajar con modelos de IA
# 2. OpenAI: La compañía que hizo el modelo GPT-4
# 3. Streamlit: Una librería para hacer interfaces web bonitas sin HTML/CSS
# 4. session_state: Una forma de guardar datos entre actualizaciones
# 5. HumanMessage, AIMessage: Clases que organizan quién escribió cada mensaje
# 
# ¿CÓMO FUNCIONA?
# 
# 1. Usuario escribe un mensaje
# 2. Se guarda en st.session_state.mensajes (memoria)
# 3. Se envía al modelo de OpenAI junto con TODO el historial
# 4. La IA ve toda la conversación y responde
# 5. La respuesta se muestra y se guarda también
# 6. Cuando refresca la página, todos los mensajes siguen ahí
#
# ==============================================================================

print("=" * 80)
print("CHATBOT INICIADO CORRECTAMENTE ✓")
print("=" * 80)