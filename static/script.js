const msgInput = document.getElementById('msg');
const sendBtn = document.getElementById('send');
const chatBox = document.getElementById('chat-box');

function appendMessage(text, sender='bot'){
  const div = document.createElement('div');
  div.className = 'msg ' + (sender==='user' ? 'user' : 'bot');
  div.innerHTML = sender==='user' ? '<b>You:</b> ' + text : '<b>Bot:</b> ' + text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage(){
  const text = msgInput.value.trim();
  if(!text) return;
  appendMessage(text,'user');
  msgInput.value = '';
  try{
    const res = await fetch('/get', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    appendMessage(data.response,'bot');
  }catch(e){
    appendMessage('Error connecting to server.','bot');
  }
}

sendBtn.addEventListener('click', sendMessage);
msgInput.addEventListener('keydown', (e)=>{ if(e.key==='Enter') sendMessage(); });
