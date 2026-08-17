from langchain_core.prompts import PromptTemplate # clase para crear plantillas de prompts


# ==|==|==| DEFINCIÓN DE PLANTILLA ==|==|==|==|==|==|
template = "Eres un experto en marketing, Suguiere un slogan creativo para un producto {producto}"

prompt= PromptTemplate(
    template = template,
    input_variables=["producto"]
)
# ==|==|==| # ==|==|==|==| ==|==|==|==|==|==|
# PROBANDO la plantilla PROMPT antes de enviar a un LLM

prompt_completo = prompt.format(producto = "Cafe organico")
print(prompt_completo)
