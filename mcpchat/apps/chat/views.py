from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message
from langchain_anthropic import ChatAnthropic
from django.shortcuts import get_object_or_404
from asgiref.sync import sync_to_async
from django.shortcuts import redirect
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from django.http import HttpResponseRedirect
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

def get_rag_tool():
    retriever = get_rag_retriever()

    def rag_search_tool(query: str):
        docs = retriever.get_relevant_documents(query)
        return "\n".join([doc.page_content for doc in docs])

    return Tool(
        name="RAGSearch",
        func=rag_search_tool,
        description="Utiliza esta herramienta para buscar información en los documentos PDF cargados."
    )

# Función para cargar documentos y crear un retriever RAG
retriever = None
def get_rag_retriever():
    global retriever
    if retriever is None:
        loader = PyPDFLoader("../guion15anios.pdf")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=400)
        chunks = text_splitter.split_documents(docs)
        db = FAISS.from_documents(chunks, OpenAIEmbeddings())
        retriever = db.as_retriever()
    return retriever

async def get_response_from_chain(message, history):
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=get_rag_retriever(),
        return_source_documents=True
    )
    result = chain({"question": message, "chat_history": history})
    return result["answer"]

async def get_response_from_agent(message, history,system_prompt):
    #rag_tool = get_rag_tool()
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

    config_file = "../browser_mcp.json"
    print("Initializing chat...")
    client = MCPClient.from_config_file(config_file)
    llm = ChatGroq(model="qwen-qwq-32b") #uso para chats simples
    
    agent = MCPAgent(
        llm=llm,
        client=client,
        #tools=[rag_tool],
        #memory_enabled=True,
        max_steps=15,
        disallowed_tools=["file_system", "network"],
        system_prompt=system_prompt,  # Se usa el prompt de la DB
        #verbose=True
    )

    #for user, bot in history:
    #    if user:
    #        await agent.memory.add_user_message(user)
    #    if bot:
    #        await agent.memory.add_assistant_message(bot)

    
    try:
        # Run the agent with the user input (memory handling is automatic)
        response = await agent.run(message)
        print(response)

    except Exception as e:
        print(f"\nError: {e}")

    #return response[0]['text']
    return response

def chat_detalle(request, id):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))
    
    # Intentamos obtener la conversación
    try:
        current_conversation = Conversation.objects.get(id=id)
    except Conversation.DoesNotExist:
        return redirect(reverse("index:login"))
    
    conversations = Conversation.objects.filter(user=request.user)
    messages = Message.objects.filter(conversation=current_conversation)

    return render(request, 'chat/chat_detalle.html', {
        'conversations': conversations,
        'current_conversation': current_conversation,
        'messages':messages
    })

def chat_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))

    return render(request, 'chat/chat.html', {
        'conversations': Conversation.objects.all()
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

@csrf_exempt
def chat_message(request):
    if request.method == "POST" and request.user.is_authenticated:
        user_message = request.POST.get("message")
        conversation_id = request.POST.get("conversation_id")
        system_prompt = request.POST.get("system_prompt")

        # Buscar la conversación del usuario
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return JsonResponse({"error": "Conversación no encontrada"}, status=404)

        # Guardar mensaje del usuario
        Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )

        history = list(
            Message.objects.filter(conversation=conversation).order_by('timestamp').values_list('sender', 'content')
        )

        formatted_history = [(msg[1], '') if msg[0] == 'user' else ('', msg[1]) for msg in history[:-1]]

        # Obtener respuesta del bot
        if user_message:
            #loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(loop)
            #bot_response = loop.run_until_complete(get_response_from_chain(user_message, formatted_history))
            #bot_response = loop.run_until_complete(get_response_from_agent(user_message, formatted_history,system_prompt))
            bot_response = asyncio.run(get_response_from_agent(user_message, formatted_history,system_prompt))

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
