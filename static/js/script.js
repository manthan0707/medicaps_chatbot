
function appendMessage(content, sender) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-msg" : "bot-msg";
    msgDiv.textContent = content;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function sendMessage() {
    const userInput = document.getElementById("user-input");
    const message = userInput.value.trim();
    if (message === "") return;
    appendMessage(message, "user");
    userInput.value = "";

    fetch("/get", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ msg: message })
    })
    .then(res => res.json())
    .then(data => {
        appendMessage(data.reply, "bot");
    });
}

function toggleTheme() {
    document.getElementById("theme").classList.toggle("dark-mode");
}
