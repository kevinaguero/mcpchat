document.addEventListener("DOMContentLoaded", function () {

    // Cargar mensajes al iniciar
    fetch(`/chat/messages/${conversationId}/`)
        .then(res => res.json())
        .then(data => {
            data.messages.forEach(msg => appendMessage(msg.sender, msg.content));
            scrollToBottom();
        });
});

function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();

    if (!message) return;

    // Mostrar mensaje del usuario inmediatamente
    appendMessage('user', message);
    scrollToBottom();

    // Limpiar input
    input.value = "";

    fetch("/chat/message/", {
        method: "POST",
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({ message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            appendMessage('bot', data.response);
            scrollToBottom();
        }
    })
    .catch(error => {
        console.error("Error al enviar mensaje:", error);
    });
}

function appendMessage(sender, text) {
    const container = document.getElementById("chat-messages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}`;
    messageDiv.innerText = text;
    container.appendChild(messageDiv);
}

function scrollToBottom() {
    const container = document.getElementById("chat-messages");
    container.scrollTop = container.scrollHeight;
}

function getCSRFToken() {
    let cookieValue = null;
    const name = "csrftoken";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
