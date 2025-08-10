
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');

function appendMsg(text, who='bot'){
  const d = document.createElement('div');
  d.className = 'msg ' + (who==='user'?'user':'bot');
  d.textContent = text;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
}

async function send(){
  const text = input.value.trim();
  if(!text) return;
  appendMsg(text,'user');
  input.value='';
  const loading = document.createElement('div');
  loading.className='msg bot';
  loading.textContent = 'Fetching live data...';
  chat.appendChild(loading);
  chat.scrollTop = chat.scrollHeight;
  try{
    const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:text})});
    const data = await res.json();
    loading.remove();
    appendMsg(data.reply,'bot');
  }catch(e){
    loading.remove();
    appendMsg('Error connecting to server: '+e,'bot');
  }
}

sendBtn.addEventListener('click', send);
input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') send(); });
