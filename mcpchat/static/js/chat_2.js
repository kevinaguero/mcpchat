// Para manejar CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            for (let cookie of document.cookie.split(';')) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    let conversations = JSON.parse(localStorage.getItem('conversations')) || {};
    let currentConversation = localStorage.getItem('currentConversation') || null;

    function renderConversationList() {
      const chatHistory = document.getElementById('chat-history');
      chatHistory.innerHTML = '';
      for (const id in conversations) {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.classList.toggle('active', id === currentConversation);
        li.textContent = conversations[id].name;
        li.onclick = () => switchConversation(id);

        const actions = document.createElement('div');

        const renameBtn = document.createElement('button');
        renameBtn.className = 'btn btn-sm btn-outline-warning me-1';
        renameBtn.innerHTML = '<i class="fas fa-edit"></i>';
        renameBtn.onclick = (e) => {
          e.stopPropagation();
          const newName = prompt('Nuevo nombre:');
          if (newName) {
            conversations[id].name = newName;
            saveConversations();
            renderConversationList();
          }
        };

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.onclick = (e) => {
          e.stopPropagation();
          if (confirm('¿Eliminar esta conversación?')) {
            delete conversations[id];
            if (id === currentConversation) currentConversation = null;
            saveConversations();
            renderConversationList();
            loadMessages();
          }
        };

        actions.appendChild(renameBtn);
        actions.appendChild(deleteBtn);
        li.appendChild(actions);
        chatHistory.appendChild(li);
      }
    }

    function createConversation() {
      const id = 'conv_' + Date.now();
      conversations[id] = { name: 'Nueva conversación', messages: [] };
      currentConversation = id;
      saveConversations();
      renderConversationList();
      loadMessages();
    }

    function switchConversation(id) {
      currentConversation = id;
      localStorage.setItem('currentConversation', id);
      renderConversationList();
      loadMessages();
    }

    function saveConversations() {
      localStorage.setItem('conversations', JSON.stringify(conversations));
      localStorage.setItem('currentConversation', currentConversation);
    }

    function loadMessages() {
      const messagesContainer = document.getElementById('chat-messages');
      messagesContainer.innerHTML = '';
      if (!currentConversation || !conversations[currentConversation]) return;
      document.getElementById('chat-title').textContent = conversations[currentConversation].name;
      conversations[currentConversation].messages.forEach(({ sender, text }) => {
        const msg = document.createElement('div');
        msg.className = `message ${sender}`;
        msg.textContent = text;
        messagesContainer.appendChild(msg);
      });
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async function sendMessage() {
      console.log("iniciando2...");
      const input = document.getElementById('user-input');
      const messageText = input.value.trim();
      if (!messageText || !currentConversation) return;

      // Muestra mensaje del usuario
      conversations[currentConversation].messages.push({ sender: 'user', text: messageText });
      saveConversations();
      loadMessages();
      input.value = '';

      try {
        console.log("iniciando...");
        const response = await fetch('/chats/message/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({ message: messageText })
        });
        const data = await response.json();
        
        console.log("hola mundo");
        console.log(data);
        conversations[currentConversation].messages.push({ sender: 'bot', text: data.response || 'Error al obtener respuesta.' });
      } catch (error) {
        conversations[currentConversation].messages.push({ sender: 'bot', text: 'Error en el servidor.' });
      }

      saveConversations();
      loadMessages();
    }

    function toggleDarkMode() {
      document.body.classList.toggle('dark-mode');
    }

    window.onload = () => {
      renderConversationList();
      loadMessages();
    };