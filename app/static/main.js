// app/static/main.js

document.addEventListener("DOMContentLoaded", function() {
    // Elements
    const chatForm = document.getElementById('chat-form');
    const chatBox = document.getElementById('chat-box');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');
    const materialsForm = document.getElementById('materials-form');
    const messageInput = document.querySelector('input[name="message"]');

    let isProcessing = false; // To prevent multiple submissions

    // Handle form submission
    chatForm.addEventListener('submit', function(event) {
        event.preventDefault();
        if (!isProcessing) {
            sendMessage();
        }
    });

    // Disable reset and send buttons during processing
    function disableButtons() {
        sendButton.disabled = true;
        resetButton.disabled = true;
        isProcessing = true;
    }

    function enableButtons() {
        sendButton.disabled = false;
        resetButton.disabled = false;
        isProcessing = false;
    }

    // Send message via AJAX
    function sendMessage() {
        disableButtons();

        const message = messageInput.value.trim();
        if (!message) {
            enableButtons();
            return;
        }

        // Get selected materials
        const selectedMaterials = [];
        const materialCheckboxes = materialsForm.querySelectorAll('input[name="materials"]:checked');
        materialCheckboxes.forEach((checkbox) => {
            selectedMaterials.push(checkbox.value);
        });

        // Prepare data
        const data = new FormData();
        data.append('message', message);
        data.append('csrf_token', csrfToken);
        selectedMaterials.forEach((materialId) => {
            data.append('materials', materialId);
        });

        // Display user's message immediately
        displayMessage(message, 'user');

        // Clear input
        messageInput.value = '';

        fetch(chatUrl, {
            method: 'POST',
            body: data,
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Display AI response
                displayMessage(result.ai_response, 'assistant');

                // Re-enable buttons
                enableButtons();

                // Render MathJax and Markdown
                renderContent();
            } else {
                alert('Error: ' + result.error);
                enableButtons();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            enableButtons();
        });
    }

    // Display message in chat box
    function displayMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'assistant-message');

        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        if (sender === 'assistant') {
            contentDiv.classList.add('ai-response');
            contentDiv.setAttribute('data-markdown', content);
        } else {
            contentDiv.textContent = content;
        }

        messageDiv.appendChild(contentDiv);
        chatBox.appendChild(messageDiv);

        // Scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;

        // Animate message appearance
        gsap.from(messageDiv, { opacity: 0, y: 20, duration: 0.5 });
    }

    // Handle Reset Conversation
    resetButton.addEventListener('click', function() {
        if (!isProcessing && confirm('Are you sure you want to reset the conversation?')) {
            resetConversation();
        }
    });

    function resetConversation() {
        disableButtons();

        fetch(resetUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Clear chat box
                chatBox.innerHTML = '';
                enableButtons();
            } else {
                alert('Error resetting conversation.');
                enableButtons();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            enableButtons();
        });
    }

    // Render MathJax and Markdown content
    function renderContent() {
        const aiResponses = document.querySelectorAll('.ai-response');

        aiResponses.forEach(function(element) {
            const markdownContent = element.getAttribute('data-markdown');
            let htmlContent = marked.parse(markdownContent);
            htmlContent = DOMPurify.sanitize(htmlContent);
            element.innerHTML = htmlContent;
        });

        // Render LaTeX with MathJax
        if (typeof MathJax !== 'undefined') {
            MathJax.typesetPromise();
        }
    }

    // Initial rendering of existing messages
    renderContent();
});
