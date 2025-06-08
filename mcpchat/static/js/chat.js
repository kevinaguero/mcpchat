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
            await fetchConversations();
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
        await fetchConversations();
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

    try {
    const res = await fetch('/chats/message/', {
        method: 'POST',
        headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        //'X-CSRFToken': csrftoken
        },
        body: `message=${encodeURIComponent(message)}&conversation_id=${current_conversation}`
    });

    const data = await res.json();
    appendMessage('bot', data.response);
    } catch (error) {
    appendMessage('bot', 'Error en el servidor.');
    }   
}

function appendMessage(sender, content) {
    const chatMessages = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    div.textContent = content;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

fetchConversations(); // Inicial

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
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
