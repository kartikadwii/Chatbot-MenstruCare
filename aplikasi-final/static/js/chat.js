const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message-input");
const chatBody = document.getElementById("chat-body");
const sendButton = document.getElementById("send-btn");
const clearButton = document.getElementById("clear-chat");

function getCurrentTime() {
    return new Date().toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit"
    });
}

function addMessage(text, sender, time = getCurrentTime()) {
    const message = document.createElement("div");
    message.className = `message ${sender}`;

    const content = document.createElement("div");
    content.className = "message-content";

    const textElement = document.createElement("div");
    textElement.textContent = text;

    const timeElement = document.createElement("div");
    timeElement.className = "message-time";
    timeElement.textContent = time;

    content.appendChild(textElement);
    content.appendChild(timeElement);
    message.appendChild(content);

    chatBody.appendChild(message);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function showTyping() {
    const typing = document.createElement("div");
    typing.className = "message bot";
    typing.id = "typing-indicator";

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = "MenstruCare sedang mengetik...";

    typing.appendChild(content);
    chatBody.appendChild(typing);

    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById("typing-indicator");

    if (typing) {
        typing.remove();
    }
}

async function sendMessage(message) {
    if (!message.trim()) return;

    addMessage(message, "user");
    messageInput.value = "";
    sendButton.disabled = true;

    showTyping();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        removeTyping();

        if (!response.ok || !data.success) {
            addMessage(
                data.error || "Maaf, terjadi kesalahan.",
                "bot"
            );
            return;
        }

        addMessage(data.reply, "bot");

    } catch (error) {
        removeTyping();
        addMessage(
            "Maaf, tidak dapat terhubung ke server.",
            "bot"
        );
    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

async function loadHistory() {
    try {
        const response = await fetch("/api/history");
        const data = await response.json();

        if (data.success && data.history.length > 0) {
            chatBody.innerHTML = "";

            data.history.forEach(item => {
                const time = item.created_at
                    ? new Date(item.created_at).toLocaleTimeString(
                        "id-ID",
                        {
                            hour: "2-digit",
                            minute: "2-digit"
                        }
                    )
                    : getCurrentTime();

                addMessage(item.text, item.sender, time);
            });
        }

    } catch (error) {
        console.error("Gagal memuat riwayat:", error);
    }
}

async function clearHistory() {
    const confirmation = confirm(
        "Apakah kamu yakin ingin menghapus seluruh riwayat percakapan?"
    );

    if (!confirmation) return;

    try {
        const response = await fetch("/api/clear", {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {
            chatBody.innerHTML = "";

            addMessage(
                "Halo! Aku MenstruCare. Ada yang ingin kamu tanyakan tentang menstruasi hari ini?",
                "bot"
            );
        }

    } catch (error) {
        alert("Gagal menghapus riwayat percakapan.");
    }
}

if (chatForm) {
    chatForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const message = messageInput.value.trim();

        if (message) {
            sendMessage(message);
        }
    });
}

if (clearButton) {
    clearButton.addEventListener("click", clearHistory);
}

document.querySelectorAll(".suggestion-btn").forEach(button => {
    button.addEventListener("click", function() {
        const message = this.dataset.message || this.textContent.trim();

        sendMessage(message);
    });
});

if (chatBody) {
    loadHistory();
}