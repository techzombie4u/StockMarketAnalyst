
document.addEventListener("DOMContentLoaded",()=>{
  const up=document.getElementById("updated");
  const set=()=>{ if(up) up.textContent=new Date().toISOString(); };
  set(); setInterval(set,30000);
  const r=document.getElementById("refresh");
  if(r) r.onclick=()=>set();
});
