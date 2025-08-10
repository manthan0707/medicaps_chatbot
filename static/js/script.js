
const chat = document.getElementById('chat');
const input = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const themeBtn = document.getElementById('themeBtn');
let dark=false;

function appendMsg(text, who='bot', html=false){
  const div = document.createElement('div');
  div.className = 'msg ' + (who==='user' ? 'user' : 'bot');
  if(html) div.innerHTML = text; else div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function appendTyping(){
  const d = document.createElement('div');
  d.className='msg bot';
  d.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

async function send(){
  const text = input.value.trim();
  if(!text) return;
  appendMsg(text,'user');
  input.value='';
  const t = appendTyping();
  try{
    const res = await fetch('/chat', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
    const data = await res.json();
    t.remove();
    appendMsg(data.reply,'bot', false);
  }catch(e){
    t.remove();
    appendMsg('Error connecting to server.','bot');
  }
}

sendBtn.addEventListener('click', send);
input.addEventListener('keydown',(e)=>{ if(e.key==='Enter') send(); });

themeBtn.addEventListener('click', ()=>{
  dark = !dark;
  document.body.classList.toggle('dark-mode', dark);
  themeBtn.textContent = dark ? 'Light' : 'Dark';
});

document.querySelectorAll('.quick').forEach(b=>{
  b.addEventListener('click', ()=>{
    const q = b.getAttribute('data-q');
    input.value = q;
    send();
  });
});
