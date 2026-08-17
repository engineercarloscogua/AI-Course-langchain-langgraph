# fichero de configuración con variables globales
from pathlib import Path

#------------------configuraciónd e modelos-------------------------
EMBEDDING_MODEL = "text-embedding-3-large"

#------------------- LLm models---------------------
# modelo no tan avanzado para consultas
QUERY_MODEL = "gpt-4o-mini"
#respuesta mas avanzada - modelos mas avanzados
GENERATION_MODEL = "gpt-4o"


# ----------------configuración del vector store -------------
CHROMA_DB_PATH = str(Path(__file__).resolve().parent.parent / "crhoma_db")

# ------------------confoiguración del retriever --------------------
# search type
SEARCH_TYPE = "mmr"
# diversidad con balance equilibrado
MMR_DIVERSITY_LAMBDA = 0.7
# documentos iniciales a evaluar 
MMR_FETCH_K = 20
# NUMERO DE DOCUMENTOS FINALES DESPUES DE APLICAR MMR
SEARCH_K = 2

# configuración alternativa para recuperación hibrida para similut por coseno
ENABLE_HYBRID_SEARCH = True
SIMILARITY_THRESHOLD = 0.75
