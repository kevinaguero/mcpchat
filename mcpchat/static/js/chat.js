document.addEventListener("DOMContentLoaded", () => {
    // 👉 Scroll automático al final del contenedor de mensajes
    const chatMessagesContainer = document.getElementById("chat-messages");
    chatMessagesContainer.scrollTo({ top: chatMessagesContainer.scrollHeight, behavior: 'smooth' });
});


// Función para extraer CSRF de las cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

async function fetchConversations() {
    const res = await fetch('/chats/conversations/');
    const data = await res.json();
    renderConversationList(data);
}

function renderConversationList(conversations) {
    const chatHistory = document.getElementById('chat-history');
    chatHistory.innerHTML = '';
    conversations.forEach(conv => {
        const li = document.createElement('li');
        const btn_conv = document.createElement('div');
        btn_conv.className = 'conversation-button';

        if (conv.id == current_conversation) {
            //btn_conv.className = 'active';
            btn_conv.classList.add("active");
        }

        const texto = document.createElement('span');
        texto.textContent = conv.name;
        const actions = document.createElement('div');
        actions.className = 'icon-buttons';
        
        //li.className = 'list-group-item';
        //li.textContent = conv.name;
        li.onclick = () => {
            window.location.href = `/chats/${conv.id}`;
            document.getElementById('chat-title').textContent = conv.name;
            //loadMessages(conv.id);
        };

        const renameBtn = document.createElement('button');
        //renameBtn.className = 'btn btn-sm btn-outline-warning me-1';
        renameBtn.innerHTML = '<i class="bi bi-pencil"></i>';
        renameBtn.onclick = async (e) => {
            e.stopPropagation();
            id_conv = conv.id
            const newName = prompt('Nuevo nombre:');
            if (newName) {
                await fetch(`/chats/edit/${id_conv}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken},
                    body: `newname=${newName}`
                });
                window.location.href = `/chats/${conv.id}`;
            }
        };

        const deleteBtn = document.createElement('button');
        //deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
        deleteBtn.onclick = async (e) => {
            e.stopPropagation();
            id_conv = conv.id
            if (confirm('¿Eliminar esta conversación?')) {
                await fetch(`/chats/delete/${id_conv}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrftoken}
                });
                window.location.href = `/chats`;
            }
        };

        actions.appendChild(renameBtn);
        actions.appendChild(deleteBtn);
        btn_conv.appendChild(texto);
        btn_conv.appendChild(actions);
        li.appendChild(btn_conv);

        chatHistory.appendChild(li);
    });
}

async function createConversation() {
    const res = await fetch('/chats/create/', {
    method: 'POST',
    headers: {'X-CSRFToken': csrftoken}
    });
    const conv = await res.json();
    await fetchConversations();
    current_conversation = conv.id;
    window.location.href = `/chats/${current_conversation}`;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value;

    appendMessage('user', message);
    input.value = '';

    /////////////////
    // CARGAR SPINNER DE ESPERA
    const spinnerContainer = document.createElement('div');
    spinnerContainer.id = 'loading-spinner';
    spinnerContainer.style.display = 'flex';
    const dotFlashing = document.createElement('div');
    dotFlashing.className = 'dot-flashing';
    spinnerContainer.appendChild(dotFlashing);
    
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(spinnerContainer);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    //////////////

    const spinner = document.getElementById('loading-spinner');
    spinner.style.display = 'flex';

    try {
        const res = await fetch('/chats/message/', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
            },
            body: `message=${encodeURIComponent(message)}&conversation_id=${current_conversation}`
        });

        const data = await res.json();
        spinner.remove();
        appendMessage('bot', data.response);
        
        } catch (error) {
        spinner.remove();
        appendMessage('bot', 'Error en el servidor.');
    }   
}

function appendMessage(sender, content) {
    const chatMessages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = content;
    chatMessages.appendChild(div);

    if (sender == 'bot'){
        const html = div.innerHTML.trim();
        div.innerHTML = marked.parse(html);
        hljs.highlightAll();
        chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    }
}

fetchConversations(); // Inicial

function toggleDarkMode() {
    const dark_mode = document.body.classList.toggle('dark-mode');

    // Guardar la preferencia del usuario en el backend
    fetch('/chats/chat_dark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken // Solo si usás CSRF, como en Django
        },
        body: `dark_mode=${dark_mode}`
    });
}


function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('toggleSidebarBtn');
  const tooltipInstance = bootstrap.Tooltip.getInstance(toggleBtn);

  sidebar.classList.toggle('collapsed');

  // Actualizar el título dinámicamente
  if (sidebar.classList.contains('collapsed')) {
    toggleBtn.setAttribute('title', 'Mostrar barra lateral');
  } else {
    toggleBtn.setAttribute('title', 'Ocultar barra lateral');
  }

  // Actualizar el tooltip manualmente
  tooltipInstance.setContent({ '.tooltip-inner': toggleBtn.getAttribute('title') });
}

//CONFIGURACIONES CHATBOT
const systemPrompt = document.getElementById('systemPrompt');
const charCount = document.getElementById('charCount');
charCount.textContent = systemPrompt.value.length;

systemPrompt.addEventListener('input', () => {
    charCount.textContent = systemPrompt.value.length;
});