# ==============================================================================
# CONFIGURACIÓN Y PIPELINE DEL SISTEMA RAG - HELPDESK SYSTEM
# ==============================================================================
# Este archivo gestiona el procesamiento, fragmentación e indexación vectorial:
# Paso 1: Importación de dependencias y librerías clave.
# Paso 2: Definición de la clase DocumentProcessor para gestionar el pipeline RAG.
# Paso 3: Carga y enriquecimiento de documentos desde el almacenamiento local.
# Paso 4: Métodos auxiliares de clasificación por categoría y generación de hash MD5.
# Paso 5: Fragmentación de documentos (text splitting / chunking).
# Paso 6: Creación e indexación de la Base de Datos Vectorial (ChromaDB).
# Paso 7: Carga de un Vectorstore previamente persistido.
# Paso 8: Orquestación completa del flujo de configuración del sistema RAG.
# Paso 9: Prueba de búsquedas por similitud vectorial (Semantic Search).
# Paso 10: Función principal (main) y punto de entrada del script.
# ==============================================================================

# ------------------------------------------------------------------------------
# PASO 1: IMPORTACIÓN DE LIBRERÍAS Y MÓDULOS
# ------------------------------------------------------------------------------
import hashlib
from typing import List
from pathlib import Path
import shutil

# Cargadores de documentos de LangChain
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# Vectorstore Chroma (Intento de paquete dedicado moderno o fallback a community)
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

# Modelos de embeddings de OpenAI
from langchain_openai import OpenAIEmbeddings

# Splitter de texto recursivo desde la librería dedicada moderna
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Variables globales de configuración
from config import DOCS_PATH, CHROMADB_PATH, EMBEDDINGS_MODEL


# ------------------------------------------------------------------------------
# PASO 2: DEFINICIÓN DE LA CLASE DOCUMENTPROCESSOR
# ------------------------------------------------------------------------------
class DocumentProcessor:
    """Procesador de documentos para construir e indexar la BD vectorial RAG."""
    
    def __init__(self, docs_path: str = DOCS_PATH, chroma_path: str = CHROMADB_PATH):
        """Inicializa rutas, embeddings y el divisor de texto (text splitter)."""
        self.docs_path = Path(docs_path)
        self.chroma_path = Path(chroma_path)
        
        # Modelo de embeddings de OpenAI
        self.embeddings = OpenAIEmbeddings(model=EMBEDDINGS_MODEL)
        
        # Divisor de texto recursivo para fragmentar documentos en chunks
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    # --------------------------------------------------------------------------
    # PASO 3: CARGA Y ENRIQUECIMIENTO DE DOCUMENTOS DESDE EL DISCO
    # --------------------------------------------------------------------------
    def load_documents(self) -> List[Document]:
        """Carga documentos markdown (.md) y enriquece sus metadatos."""
        print(f"[INFO] Cargando documentos desde {self.docs_path}")
        
        # Verificar que el directorio existe
        if not self.docs_path.exists():
            print(f"[WARN] El directorio {self.docs_path} no existe.")
            return []

        loader = DirectoryLoader(
            str(self.docs_path),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"}
        )
        
        documents = loader.load()
        
        # Enriquecer cada documento con metadatos útiles
        for doc in documents:
            filename = Path(doc.metadata["source"]).stem
            doc.metadata.update({
                "filename": filename,
                "doc_type": self._get_doc_type(filename),
                "doc_id": self._generate_doc_id(doc.page_content)
            })
        
        print(f"[OK] Cargados {len(documents)} documentos")
        return documents

    # --------------------------------------------------------------------------
    # PASO 4: MÉTODOS AUXILIARES DE CLASIFICACIÓN E IDENTIFICACIÓN ÚNICA
    # --------------------------------------------------------------------------
    def _get_doc_type(self, filename: str) -> str:
        """Determina la categoría del documento según su nombre."""
        fn_lower = filename.lower()
        if "faq" in fn_lower:
            return "faq"
        elif "manual" in fn_lower:
            return "manual"
        elif "troubleshooting" in fn_lower:
            return "troubleshooting"
        else:
            return "general"
    
    def _generate_doc_id(self, content: str) -> str:
        """Genera un hash MD5 de 8 caracteres basado en el contenido del documento."""
        return hashlib.md5(content.encode()).hexdigest()[:8]    

    # --------------------------------------------------------------------------
    # PASO 5: FRAGMENTACIÓN DE DOCUMENTOS (CHUNKING)
    # --------------------------------------------------------------------------
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Divide documentos en fragmentos (chunks) más pequeños."""
        print("[INFO] Dividiendo documentos en chunks...")        
        chunks = self.text_splitter.split_documents(documents)        
        
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": i,
                "chunk_size": len(chunk.page_content)
            })
        
        print(f"[OK] Creados {len(chunks)} chunks")
        return chunks

    # --------------------------------------------------------------------------
    # PASO 6: CREACIÓN DE LA BASE DE DATOS VECTORIAL (CHROMADB)
    # --------------------------------------------------------------------------
    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """Crea y persiste un vectorstore con ChromaDB a partir de los fragmentos."""
        print("[INFO] Creando vectorstore con ChromaDB...")
        
        # Limpiar directorio previo si ya existe
        if self.chroma_path.exists():
            try:
                shutil.rmtree(self.chroma_path, ignore_errors=True)
            except Exception as e:
                print(f"[WARN] No se pudo borrar la carpeta previa de Chroma: {e}")
            
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(self.chroma_path),
            collection_name="helpdesk_knowledge"
        )
        
        print(f"[OK] Vectorstore creado en {self.chroma_path}")
        print(f"[STATS] Total de vectores indexados: {len(documents)}")
        return vectorstore

    # --------------------------------------------------------------------------
    # PASO 7: CARGA DE UN VECTORSTORE EXISTENTE DESDE DISCO
    # --------------------------------------------------------------------------
    def load_existing_vectorstore(self) -> Chroma:
        """Carga la BD vectorial persistida previamente en disco."""
        if not self.chroma_path.exists():
            raise FileNotFoundError(f"Vectorstore no encontrado en {self.chroma_path}")
            
        vectorstore = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.embeddings,
            collection_name="helpdesk_knowledge"
        )
        return vectorstore

    # --------------------------------------------------------------------------
    # PASO 8: ORQUESTACIÓN Y CONFIGURACIÓN COMPLETA DEL SISTEMA RAG
    # --------------------------------------------------------------------------
    def setup_rag_system(self, force_rebuild: bool = False):
        """Orquesta todo el flujo (Cargar -> Fragmentar -> Indexar en ChromaDB)."""
        print("[INFO] Configurando sistema RAG...")
        
        if self.chroma_path.exists() and not force_rebuild:
            print("[INFO] Vectorstore existente encontrado")
            return self.load_existing_vectorstore()
        
        documents = self.load_documents()
        if not documents:
            print("[WARN] No se encontraron documentos para procesar en la carpeta docs")
            return None
        
        chunks = self.split_documents(documents)
        vectorstore = self.create_vectorstore(chunks)
        
        print("[OK] Sistema RAG configurado exitosamente")
        return vectorstore

    # --------------------------------------------------------------------------
    # PASO 9: PRUEBA DE BÚSQUEDA POR SIMILITUD VECTORIAL (SEMANTIC SEARCH)
    # --------------------------------------------------------------------------
    def test_search(self, vectorstore: Chroma, query: str = "resetear contraseña"):
        """Prueba la búsqueda de fragmentos por similitud vectorial."""
        print(f"\n[SEARCH] Probando búsqueda: '{query}'")
        results = vectorstore.similarity_search(query, k=3)
        
        for i, doc in enumerate(results, 1):
            print(f"\n[RESULT {i}]:")
            print(f"Tipo: {doc.metadata.get('doc_type', 'unknown')}")
            print(f"Archivo: {doc.metadata.get('filename', 'unknown')}")
            print(f"Contenido: {doc.page_content[:200]}...")
        
        return results

# ------------------------------------------------------------------------------
# PASO 10: FUNCIÓN PRINCIPAL Y EJECUCIÓN DEL PIPELINE
# ------------------------------------------------------------------------------
def main():
    """Ejecución principal para verificar la indexación y pruebas RAG."""
    print("Helpdesk 2.0 - Configuración RAG")
    print("=" * 40)
    
    processor = DocumentProcessor(docs_path=DOCS_PATH, chroma_path=CHROMADB_PATH)
    vectorstore = processor.setup_rag_system(force_rebuild=True)
    
    if vectorstore:
        test_queries = [
            "resetear contraseña",
            "error 500",
            "cancelar suscripción",
            "aplicación lenta"
        ]
        for query in test_queries: 
            processor.test_search(vectorstore, query)
    
    print("\n[OK] Configuración completada")


if __name__ == "__main__":
    main()