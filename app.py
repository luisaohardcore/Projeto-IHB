import streamlit as st
import json
import random
import datetime
import os
from groq import Groq

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="IA Abençoada", 
    page_icon="📖", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS
st.markdown("""
    <style>
    .main { background-color: transparent; }
    div.stButton > button:first-child {
        width: 100%;
        border-radius: 12px;
        font-weight: bold;
        padding: 10px;
        border: 2px solid #1E88E5 !important;
        background-color: white;
        color: #1E88E5;
        transition: 0.2s;
    }
    div.stButton > button:first-child:hover {
        background-color: #1E88E5;
        color: white !important;
    }
    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95);
        color: #888;
        text-align: center;
        font-size: 11px;
        padding: 5px 0;
        border-top: 1px solid #eee;
        z-index: 999;
    }
    .stChatInput { margin-bottom: 35px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURAÇÃO DA IA (Groq Cloud) ---
# Substitua o valor abaixo pela sua API Key real
GROQ_API_KEY = "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"

with st.sidebar:
    st.title("⚙️ Configurações")
    
    # Dicionário de modelos para facilitar a troca
    modelos_disponiveis = {
        "Llama 3.3 70B (Equilibrado)": "llama-3.3-70b-versatile",
        "DeepSeek R1 (Raciocínio)": "deepseek-r1-distill-llama-70b",
        "Llama 3.1 8B (Instantâneo)": "llama-3.1-8b-instant",
        "Mixtral 8x7B (Versátil)": "mixtral-8x7b-32768"
    }
    
    modelo_selecionado = st.selectbox(
        "Escolha o modelo de IA:",
        options=list(modelos_disponiveis.keys()),
        index=0
    )
    
    id_modelo = modelos_disponiveis[modelo_selecionado]
    st.markdown("---")

def chamar_mentor_groq(pergunta_usuario, contexto_biblico="", modo_motivacao=False):
    if not GROQ_API_KEY or GROQ_API_KEY == "SUA_CHAVE_AQUI":
        return "Erro: A API Key do Groq não foi configurada corretamente no código."

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt_sistema = f"""
    Você é um Mentor Bíblico sábio, empático e direto.
    Responda sempre em Português Brasileiro.
    Use o CONTEXTO BÍBLICO abaixo para enriquecer sua resposta, mas não se limite a ele.
    Seja pastoral, evite repetições desnecessárias e procure variar as citações bíblicas.
    
    CONTEXTO BÍBLICO:
    {contexto_biblico if contexto_biblico else "Use sua base teológica geral de diversos livros bíblicos."}
    """

    if modo_motivacao:
        prompt_sistema = "Gere uma frase curta e impactante de motivação cristã. Seja criativo."

    try:
        completion = client.chat.completions.create(
            model=id_modelo, 
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta_usuario}
            ],
            temperature=0.7,
            max_tokens=500,
            top_p=1,
            stream=False,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na conexão com a nuvem ({modelo_selecionado}): {str(e)}"

# --- 3. DADOS LOCAIS (Bíblia) ---
@st.cache_data(show_spinner=False)
def carregar_biblia():
    try:
        if os.path.exists('pt_almeida.json'):
            with open('pt_almeida.json', 'r', encoding='utf-8-sig') as f:
                return json.load(f)
        return []
    except Exception:
        return []

biblia = carregar_biblia()

def buscar_versiculos(pergunta):
    if not biblia or len(pergunta) < 3: return ""
    palavras = [p.lower() for p in pergunta.split() if len(p) > 3]
    if not palavras: return ""

    ranking = []
    for livro in biblia:
        for n_cap, capitulo in enumerate(livro['chapters']):
            for n_ver, texto in enumerate(capitulo):
                score = sum(1 for p in palavras if p in texto.lower())
                if score > 0:
                    ranking.append({
                        "texto": f"[{livro['name']} {n_cap+1}:{n_ver+1}] {texto}",
                        "pontos": score
                    })

    ranking = sorted(ranking, key=lambda x: x['pontos'], reverse=True)
    return "\n".join([item["texto"] for item in ranking[:3]])

# --- 4. INTERFACE ---
with st.sidebar:
    st.title("📖 Mentor UNASP")
    opcao = st.radio("Menu Principal:", ("Conversar", "Versículo do Dia", "Motivação"))
    st.markdown("---")
    st.caption(f"Status: Ativo com {modelo_selecionado}")

if opcao == "Conversar":
    st.header("🔍 Consultoria Pastoral")
    if prompt := st.chat_input("Como posso ajudar hoje?"):
        st.chat_message("user").write(prompt)
        contexto = buscar_versiculos(prompt)
        with st.spinner(f"O Mentor ({modelo_selecionado}) está processando..."):
            resposta = chamar_mentor_groq(prompt, contexto)
            st.chat_message("assistant").write(resposta)

elif opcao == "Versículo do Dia":
    st.header("📖 Palavra de Hoje")
    CACHE_FILE = "cache_v.json"
    hoje = str(datetime.date.today())

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            c = json.load(f)
            if c["data"] == hoje:
                st.info(f"**{c['ref']}**\n\n*{c['txt']}*")
    else:
        if biblia:
            l = random.choice(biblia)
            nc = random.randrange(len(l['chapters']))
            nv = random.randrange(len(l['chapters'][nc]))
            txt = l['chapters'][nc][nv]
            ref = f"{l['name']} {nc+1}:{nv+1}"
            with open(CACHE_FILE, "w") as f:
                json.dump({"data": hoje, "ref": ref, "txt": txt}, f)
            st.rerun()

elif opcao == "Motivação":
    st.header("💪 Ânimo e Fé")
    if st.button("Receber Mensagem"):
        with st.spinner("Buscando inspiração..."):
            st.success(chamar_mentor_groq("Dê-me uma motivação", modo_motivacao=True))

st.markdown('<div class="footer-container">IA Abençoada - Versão Cloud | UNASP</div>', unsafe_allow_html=True)