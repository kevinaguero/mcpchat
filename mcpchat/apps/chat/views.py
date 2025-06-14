from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message
from langchain.schema import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import json
import csv
from io import StringIO
from django.shortcuts import redirect
import pandas as pd
from datetime import datetime
import os
from langchain.tools import Tool
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from django.urls import reverse
from apps.configuraciones.models import Configuraciones
from django.views.decorators.http import require_GET

# Create your views here.
# views.py

from django.http import JsonResponse
import asyncio
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from mcp_use import MCPAgent, MCPClient
import os

chat_history = []

def get_config():
    return Configuraciones.load()

config = get_config()

# Solo una vez se carga el agente (evitar recrear en cada request)
#load_dotenv()
#os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
#os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

#config_file = "../browser_mcp.json"
#client = MCPClient.from_config_file(config_file)
#llm = ChatGroq(model="qwen-qwq-32b", temperature=0) #uso para chats simples
#llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0) #uso para chats simples
#llm = ChatAnthropic(model="claude-opus-4-20250514") # uso para conectar base de datos
#llm = ChatOpenAI(model="gpt-4-turbo") # no se no tengo

# Función para cargar documentos y crear un retriever RAG
def get_rag_retriever():
    loader = PyPDFLoader("../menu.pdf")
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=400)
    chunks = text_splitter.split_documents(docs)
    db = FAISS.from_documents(chunks, OpenAIEmbeddings())
    retriever = db.as_retriever()
    return retriever

load_dotenv()
#os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

with open("../browser_mcp.json") as f:
        config_file = json.load(f)

# Reemplazar el string de conexión dentro del JSON
config_file["mcpServers"]["postgres"]["args"][2] = config.conn_str
print(config.conn_str)
client = MCPClient.from_dict(config_file)
llm = ChatGroq(model="qwen-qwq-32b") #uso para chats simples

system_prompt = """
Eres un asistente de pedidos para un restaurante.
Cuando te pregunten algo relacionado con productos o precios, usa la herramienta RAGRetriever para buscar en los documentos del menú.
Cuando te pregunten por alguna consulta en la base de datos, usa el mcp de postgres para realizar consultas.
Si te piden que exportes un .csv, vas a identificar la información y la vas a devolver en un formato JSON estructurado SIN AGREGAR MENSAJES ADICIONALES, SÓLO EL JSON y pásalo a la herramienta 'GenerarCSV'.
"""

additional_instructions = """Debes tener en cuenta el historial del chat y la última pregunta del usuario que podría hacer referencia al contexto en el historial de chat.
Debes hablar siempre en español utilizando palabras Argentinas con un tono amistoso y facil de entender."""

async def get_response_from_agent(message, history):

    agent = MCPAgent(
        llm=llm,
        client=client,
        #memory_enabled=True,
        max_steps=15,
        disallowed_tools=["file_system", "network"],
        system_prompt=system_prompt,
        additional_instructions=additional_instructions
        #system_prompt=config.system_prompt,  # Se usa el prompt de la DB
    )

    retriever = get_rag_retriever()

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,  # mismo LLM que usás en MCPAgent
        retriever=retriever,
        chain_type="stuff",  # o "refine", "map_reduce", etc.
    )

    retrieval_tool = Tool.from_function(
        name="RAGRetriever",
        description="Busca información relevante en los documentos pdf cargados.",
        func=qa_chain.run,
    )

    tool_csv = Tool.from_function(
        name="GenerarCSV",
        description=(
            "Usa esta herramienta para crear un archivo CSV personalizado. "
        ),
        func=generar_csv_dinamico,
    )

    await agent.initialize()

    # Agregar herramienta manualmente (evitá sobrescribir las anteriores)
    agent._tools.append(retrieval_tool)
    agent._tools.append(tool_csv)

    # Recrear el agente con la nueva herramienta
    agent._agent_executor = agent._create_agent()
    
    #Agregar historico de chat al contexto
    for user, bot in history:
       if user:
           agent.add_to_history(HumanMessage(content=user))
       if bot:
           agent.add_to_history(AIMessage(content=bot))

    #print("********PRE TRY********")
    try:
        # Run the agent with the user input (memory handling is automatic)
        #response = await agent.run(message)
        #print("********RESPONSE********")
        response = await agent._agent_executor.ainvoke({"input": message, "chat_history": agent.get_conversation_history()})
        agent.add_to_history(HumanMessage(content=message))
        agent.add_to_history(AIMessage(content=response["output"]))
        #print("********CONTESTA CHAT********")
        #print(response)
        #print("----------------------------------------------------------")
        #print(agent.get_conversation_history())
    except Exception as e:
        print(f"\nError: {e}")

    #return response[0]['text']
    return response["output"]

def chat_detalle(request, id):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))
    
    # Intentamos obtener la conversación
    try:
        current_conversation = Conversation.objects.get(id=id)
    except Conversation.DoesNotExist:
        return redirect(reverse("index:login"))
    
    conversations = Conversation.objects.filter(user=request.user)
    messages = Message.objects.filter(conversation=current_conversation).order_by("id")

    return render(request, 'chat/chat_detalle.html', {
        'conversations': conversations,
        'current_conversation': current_conversation,
        'messages':messages,
        'config': config
    })

def chat_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))

    return render(request, 'chat/chat.html', {
        'conversations': Conversation.objects.all(),
        'config': config
    })

def chat_create(request):
    if request.user.is_authenticated and request.method == "POST":
        conversation = Conversation.objects.create(
            user=request.user,
            name="Nueva conversación"
        )
        return JsonResponse({
            'id': conversation.id,
            'name': conversation.name
        })
    return JsonResponse({'error': 'No autenticado'}, status=403)

def chat_edit(request,id):
    
    if request.user.is_authenticated and request.method == "POST":
        newname = request.POST.get("newname")

        conversation = Conversation.objects.get(id=id)
        conversation.name = newname
        conversation.save()

        return JsonResponse({'message': 'Edición aplicada con éxito'}, status=200)
    return JsonResponse({'error': 'No autenticado'}, status=403)

def chat_delete(request,id):
    if request.method == "POST":
        conversation = Conversation.objects.get(id=id)
        conversation.delete()

        return JsonResponse({'message': 'Se eliminó el chat con éxito'}, status=200)
    return JsonResponse({'error': 'No autenticado'}, status=403)

def chat_message(request):
    if request.method == "POST" and request.user.is_authenticated:
        user_message = request.POST.get("message")
        conversation_id = request.POST.get("conversation_id")

        # Buscar la conversación del usuario
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return JsonResponse({"error": "Conversación no encontrada"}, status=404)

        history = list(
            Message.objects.filter(conversation=conversation).order_by('timestamp').values_list('sender', 'content')
        )

        formatted_history = [(msg[1], '') if msg[0] == 'user' else ('', msg[1]) for msg in history[:-1]]

        # Guardar mensaje del usuario
        Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )

        # Obtener respuesta del bot
        if user_message:
            #loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(loop)
            #bot_response = loop.run_until_complete(get_response_from_chain(user_message, formatted_history))
            #bot_response = loop.run_until_complete(get_response_from_agent(user_message, formatted_history,system_prompt))
            bot_response = asyncio.run(get_response_from_agent(user_message, formatted_history))

            # Guardar mensaje del bot
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                content=bot_response
            )

            return JsonResponse({"response": bot_response})
    return JsonResponse({"error": "Solicitud inválida o no autenticada"}, status=400)

@require_GET
def chat_conversations(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=403)

    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    return JsonResponse([
        {
            'id': conv.id,
            'name': conv.name
        } for conv in conversations
    ], safe=False)

def chat_dark(request):
    if request.user.is_authenticated and request.method == "POST":
        user = request.user
        user.dark_mode = request.POST.get("dark_mode") == "true"
        user.save()

        return JsonResponse({'message': 'modo oscuro'}, status=200)
    
def generar_csv_dinamico(input_json: str) -> str:
    print("ENTRANDO POR GENERADOR CSV")
    try:
        data = json.loads(input_json)
        print(data)

        fieldnames = list(data[0].keys())
        print(fieldnames)

        # Guardar CSV en memoria (no en disco)
        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer,fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        filename = f"reporte_dinamico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join("media/reportes", filename)
        print(filename)

        csv_buffer.getvalue().to_csv(path, index=False)
        print("++++++++++++++GENERADO++++++++++++")
        print("/media/reportes/{filename}")

        return f"/media/reportes/{filename}"
    
    except Exception as e:
        return f"Error generando CSV: {str(e)}"