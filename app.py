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
# A chave foi removida para segurança. 
# No Streamlit Cloud, adicione GROQ_API_KEY em "Secrets".
GROQ_API_KEY = ""

try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    else:
        # Fallback para variável de ambiente local
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Modelo fixo para maior estabilidade
ID_MODELO_PADRAO = "llama-3.3-70b-versatile"

def chamar_mentor_groq(pergunta_usuario, contexto_biblico="", modo_motivacao=False):
    if not GROQ_API_KEY:
        return "Erro: API Key não configurada. Configure a GROQ_API_KEY nos Secrets do Streamlit ou variáveis de ambiente."

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt_sistema = f"""
    [INSTRUÇÃO CRÍTICA]
    Você é um Mentor Bíblico focado em fatos. Sua base é o CONTEXTO BÍBLICO abaixo.

    REGRAS:
    1. Se não houver contexto, responda de forma normal, como faria em uma conversa casual.
    2. Se a resposta NÃO estiver no contexto, diga: "Não encontrei uma passagem específica sobre isso agora."
    3. Use tom de conversa casual.
    4. Não se estenda muito. Utilize de 3 a 4 parágrafos no máximo para concluir seu raciocínio.
    5. Caso a conversa não esteja atrelada a assuntos bíblicos, aja como agiria naturalmente.

    CONTEXTO BÍBLICO:
    {contexto_biblico if contexto_biblico else "Use sua base teológica geral."}
    """

    if modo_motivacao:
        prompt_sistema = "Gere uma frase curta e impactante de motivação cristã baseada em princípios bíblicos."

    try:
        completion = client.chat.completions.create(
            model=ID_MODELO_PADRAO, 
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pergunta_usuario}
            ],
            temperature=0.6,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na conexão com o serviço de IA: {str(e)}"

# --- 3. DADOS LOCAIS (Bíblia) ---
@st.cache_data(show_spinner=False)
def carregar_biblia():
    try:
        caminhos = ['pt_almeida.json', './pt_almeida.json']
        for p in caminhos:
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8-sig') as f:
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
    st.caption("Motor: Llama 3.3 70B")
    st.caption("Status: Online")

if opcao == "Conversar":
    st.header("🔍 Consultoria Pastoral")
    if prompt := st.chat_input("Como posso ajudar hoje?"):
        st.chat_message("user").write(prompt)
        contexto = buscar_versiculos(prompt)
        with st.spinner(f"O Mentor está processando..."):
            resposta = chamar_mentor_groq(prompt, contexto)
            st.chat_message("assistant").write(resposta)

elif opcao == "Versículo do Dia":
    st.header("📖 Palavra de Hoje")
    CACHE_FILE = "cache_v.json"
    hoje = str(datetime.date.today())
    
    versiculo_exibir = None

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                c = json.load(f)
                if c.get("data") == hoje:
                    versiculo_exibir = c
        except:
            pass

    if not versiculo_exibir:
        if biblia:
            try:
                l = random.choice(biblia)
                nc = random.randrange(len(l['chapters']))
                nv = random.randrange(len(l['chapters'][nc]))
                txt = l['chapters'][nc][nv]
                ref = f"{l['name']} {nc+1}:{nv+1}"
                versiculo_exibir = {"data": hoje, "ref": ref, "txt": txt}
                
                with open(CACHE_FILE, "w") as f:
                    json.dump(versiculo_exibir, f)
            except Exception as e:
                st.error(f"Erro ao selecionar versículo: {e}")
        else:
            st.warning("A base de dados da Bíblia não foi encontrada.")

    if versiculo_exibir:
        st.info(f"**{versiculo_exibir['ref']}**\n\n*{versiculo_exibir['txt']}*")

elif opcao == "Motivação":
    st.header("💪 Ânimo e Fé")
    if st.button("Receber Mensagem"):
        with st.spinner("Buscando inspiração..."):
            st.success(chamar_mentor_groq("Dê-me uma motivação", modo_motivacao=True))

st.markdown('<div class="footer-container">IA Abençoada - Versão Cloud | UNASP</div>', unsafe_allow_html=True)