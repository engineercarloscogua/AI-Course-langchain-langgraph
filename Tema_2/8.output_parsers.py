# aprender cmo funciona pydantic sin usar LLM
from pydantic import BaseModel # libreria de python que permite almacenar y convertir los tipos de datos

# toma argumento y con Base Model los convierte al tipo establecido en la clase
class Usuario(BaseModel):
    #Asegurarse de tener esos 3 valores
    id: int
    nombre: str
    activo : bool = True


data = {"id" : "123" , "nombre": "Ana"}

# envio de argumentos especiales
usuario =  Usuario(**data)

#convierte los datos a json
print(usuario.model_dump_json())

#print(usuario)
