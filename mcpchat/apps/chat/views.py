from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

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
config_file = "../browser_mcp.json"
client = MCPClient.from_config_file(config_file)
llm = ChatGroq(model="qwen-qwq-32b")
agent = MCPAgent(llm=llm, client=client, max_steps=15, memory_enabled=True)

async def get_response_from_agent(message):
    response = await agent.run(message)
    return response

def chat_view(request):
    return render(request, 'chat/chat.html')

@csrf_exempt
def chat_message(request):
    if request.method == "POST":
        user_message = request.POST.get("message")
        print(request.POST.get("message"))
        if user_message:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot_response = loop.run_until_complete(get_response_from_agent(user_message))
            return JsonResponse({"response": bot_response})
    return JsonResponse({"error": "Invalid request"}, status=400)


