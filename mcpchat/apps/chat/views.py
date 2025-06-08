from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Conversation, Message
from langchain_anthropic import ChatAnthropic
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from langchain_openai import ChatOpenAI
from django.http import HttpResponseRedirect
from django.urls import reverse
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
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

config_file = "../browser_mcp.json"
client = MCPClient.from_config_file(config_file)
llm = ChatGroq(model="qwen-qwq-32b") #uso para chats simples
#llm = ChatAnthropic(model="claude-opus-4-20250514") # uso para conectar base de datos
#llm = ChatOpenAI(model="gpt-4-turbo") # no se no tengo

agent = MCPAgent(llm=llm, client=client,max_steps=15, memory_enabled=True)
#disallowed_tools=["file_system", "network"]

async def get_response_from_agent(message):
    response = await agent.run(message)
    #return response[0]['text']
    return response


def chat_detalle(request, id):
    if not request.user.is_authenticated:
        return redirect(reverse("index:login"))
    
    conversations = Conversation.objects.filter(user=request.user)
    current_conversation = get_object_or_404(conversations, id=id)
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

'''
def chat_create(request):
    if request.user.is_authenticated and request.method == "POST":
        current_conversation = Conversation.objects.create(
            user=request.user,
            name="Conversación inicial"
        )

        return render(request, 'chat/chat_detalle.html',{'current_conversation': current_conversation})

from django.http import JsonResponse
'''
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

        # Obtener respuesta del bot
        if user_message:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot_response = loop.run_until_complete(get_response_from_agent(user_message))

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
