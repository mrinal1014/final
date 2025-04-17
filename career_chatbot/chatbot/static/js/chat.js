
document.addEventListener("DOMContentLoaded", function () {
    let chatContainer = document.getElementById("chat-container");
    let botVideo = document.getElementById("botVideo");
    let sendBtn = document.getElementById("send-btn");
    let userInputField = document.getElementById("user-input");
    let chatBox = document.getElementById("chat-box");

    function restartVideo() {
        if (botVideo) {
            botVideo.currentTime = 0; // Restart video
            botVideo.play(); // Ensure it plays
        }
    }

    // ✅ Toggle chat on video click
    if (botVideo && chatContainer) {
        botVideo.addEventListener("click", function () {
            chatContainer.classList.toggle("hidden"); // Open/close chatbox
        });
    }

    // ✅ Restart video when user sends a message
    function handleMessageEvent() {
        sendMessage();
        restartVideo();
    }

    if (userInputField) {
        userInputField.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                handleMessageEvent();
            }
        });
    }

    if (sendBtn) {
        sendBtn.addEventListener("click", handleMessageEvent);
    }

    // ✅ Function to send user message
    function sendMessage() {
        let userInput = userInputField.value.trim();
        if (userInput === "") return; // Prevent empty messages

        let userMessage = document.createElement("div");
        userMessage.classList.add("message", "user");
        userMessage.innerHTML = `<span class="avatar">🧑</span><div class="text">${userInput}</div>`;
        chatBox.appendChild(userMessage);

        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to latest message
        userInputField.value = ""; // Clear input field

        showTalkingAnimation(); // Start animation

        fetch("/chatbot-response/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRFToken()
            },
            body: new URLSearchParams({ "message": userInput })
        })
        .then(response => response.json())
        .then(data => {
    let botMessage = document.createElement("div");
    botMessage.classList.add("message", "bot");
    botMessage.innerHTML = `<span class="avatar">🤖</span><div class="text">${formatResponse(data.response)}</div>`;
    chatBox.appendChild(botMessage);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll

    // ✅ Play audio if available
    if (data.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play().catch(err => console.error("Audio playback failed:", err));
    }

    hideTalkingAnimation(); // Stop animation
    adjustVideoSize(); // Adjust video size
})

        .catch(error => {
            console.error("Error:", error);
            hideTalkingAnimation();
        });
    }

    // ✅ Function to adjust video size dynamically
    function adjustVideoSize() {
        let chatMessages = chatBox.children.length;
        if (botVideo) {
            if (chatMessages > 5) {
                botVideo.style.width = "30%"; // Reduce size when messages increase
            } else {
                botVideo.style.width = "50%"; // Default size
            }
        }
    }

    function showTalkingAnimation() {
        let animationElement = document.querySelector('.talking-animation');
        if (animationElement) {
            animationElement.style.opacity = '1';
        }
    }

    function hideTalkingAnimation() {
        let animationElement = document.querySelector('.talking-animation');
        if (animationElement) {
            animationElement.style.opacity = '0';
        }
    }

    function formatResponse(response) {
        return response.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                       .replace(/\*(.*?)\*/g, "<em>$1</em>")
                       .replace(/```([\s\S]*?)```/g, "<pre>$1</pre>")
                       .replace(/`(.*?)`/g, "<code>$1</code>")
                       .replace(/\n/g, "<br>")
                       .replace(/\* (.*?)<br>/g, "• $1<br>");
    }

    function getCSRFToken() {
        let cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                return cookie.substring("csrftoken=".length);
            }
        }
        return "";
    }
});
