import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import re
import hashlib

# Configuração da página
st.set_page_config(
    page_title="Quiz Semanal",
    page_icon="❓",
    layout="wide"
)

# Senha do administrador
ADMIN_PASSWORD = "admin123"

# Funções auxiliares
def validate_cpf(cpf):
    """Valida CPF brasileiro"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    
    # Primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    # Segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    return int(cpf[9]) == digito1 and int(cpf[10]) == digito2

def format_cpf(cpf):
    """Formata CPF com pontos e hífen"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

def get_week_start():
    """Retorna o início da semana (domingo)"""
    today = datetime.now()
    days_since_sunday = today.weekday() + 1  # Monday is 0
    if days_since_sunday == 7:
        days_since_sunday = 0
    week_start = today - timedelta(days=days_since_sunday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

def init_session_state():
    """Inicializa variáveis de sessão"""
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'quiz'

# Interface para usuários
def user_interface():
    st.title("❓ Quiz Semanal")
    
    if not st.session_state.user_authenticated:
        st.subheader("Digite seu CPF para participar")
        
        cpf_input = st.text_input(
            "CPF",
            placeholder="000.000.000-00",
            max_chars=14,
            help="Digite seu CPF para identificação"
        )
        
        if st.button("Continuar"):
            if validate_cpf(cpf_input):
                formatted_cpf = format_cpf(cpf_input)
                
                # Verificar se já respondeu esta semana
                week_start = get_week_start()
                already_answered = any(
                    r['cpf'] == formatted_cpf and 
                    datetime.fromisoformat(r['timestamp']) >= week_start
                    for r in st.session_state.responses
                )
                
                if already_answered:
                    st.error("Você já participou esta semana! Aguarde a próxima semana.")
                else:
                    st.session_state.current_user = formatted_cpf
                    st.session_state.user_authenticated = True
                    st.rerun()
            else:
                st.error("CPF inválido! Por favor, digite um CPF válido.")
    else:
        show_quiz()

def show_quiz():
    if not st.session_state.questions:
        st.warning("Nenhuma pergunta disponível no momento.")
        if st.button("Tentar Novamente"):
            st.session_state.user_authenticated = False
            st.session_state.current_user = None
            st.rerun()
        return
    
    # Pegar a pergunta mais recente
    current_question = st.session_state.questions[-1]
    
    st.subheader(f"Pergunta da Semana")
    st.write(current_question['question'])
    
    # Opções de resposta
    selected_option = st.radio(
        "Escolha sua resposta:",
        current_question['options'],
        key="selected_answer"
    )
    
    if st.button("Responder", type="primary"):
        selected_index = current_question['options'].index(selected_option)
        is_correct = selected_index == current_question['correct_answer']
        
        # Salvar resposta
        response = {
            'cpf': st.session_state.current_user,
            'question': current_question['question'],
            'selected_option': selected_option,
            'selected_index': selected_index,
            'correct_answer': current_question['correct_answer'],
            'correct_option': current_question['options'][current_question['correct_answer']],
            'is_correct': is_correct,
            'timestamp': datetime.now().isoformat(),
            'feedback': current_question.get('feedback', '')
        }
        
        st.session_state.responses.append(response)
        
        # Mostrar resultado
        if is_correct:
            st.success("🎉 Parabéns! Resposta correta!")
        else:
            st.error(f"❌ Resposta incorreta. A resposta correta era: **{response['correct_option']}**")
        
        # Mostrar feedback
        if response['feedback']:
            st.info(f"📝 **Feedback:** {response['feedback']}")
        
        # Botão para reiniciar
        if st.button("Fazer Novo Quiz"):
            st.session_state.user_authenticated = False
            st.session_state.current_user = None
            st.rerun()

# Interface administrativa
def admin_interface():
    st.title("🔧 Painel Administrativo")
    
    if not st.session_state.admin_authenticated:
        st.subheader("Login Administrativo")
        password = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        admin_panel()

def admin_panel():
    # Abas do painel admin
    tab1, tab2 = st.tabs(["📝 Gerenciar Perguntas", "📊 Ver Respostas"])
    
    with tab1:
        manage_questions()
    
    with tab2:
        view_responses()
    
    # Botão de logout
    if st.button("🚪 Sair", type="secondary"):
        st.session_state.admin_authenticated = False
        st.rerun()

def manage_questions():
    st.subheader("Adicionar Nova Pergunta")
    
    with st.form("new_question_form"):
        question_text = st.text_input("Pergunta")
        
        st.write("Opções de resposta:")
        option1 = st.text_input("Opção 1")
        option2 = st.text_input("Opção 2")
        option3 = st.text_input("Opção 3")
        option4 = st.text_input("Opção 4")
        
        correct_answer = st.selectbox(
            "Resposta correta",
            [0, 1, 2, 3],
            format_func=lambda x: f"Opção {x + 1}"
        )
        
        feedback = st.text_area("Feedback da resposta")
        
        submitted = st.form_submit_button("Adicionar Pergunta", type="primary")
        
        if submitted:
            if question_text and all([option1, option2, option3, option4]) and feedback:
                new_question = {
                    'id': len(st.session_state.questions) + 1,
                    'question': question_text,
                    'options': [option1, option2, option3, option4],
                    'correct_answer': correct_answer,
                    'feedback': feedback,
                    'created_at': datetime.now().isoformat()
                }
                
                st.session_state.questions.append(new_question)
                st.success("Pergunta adicionada com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha todos os campos!")
    
    # Lista de perguntas existentes
    st.subheader("Perguntas Existentes")
    
    if st.session_state.questions:
        for i, q in enumerate(st.session_state.questions):
            with st.expander(f"Pergunta {i + 1}: {q['question'][:50]}..."):
                st.write(f"**Pergunta:** {q['question']}")
                st.write("**Opções:**")
                for j, option in enumerate(q['options']):
                    prefix = "✅" if j == q['correct_answer'] else "•"
                    st.write(f"{prefix} {option}")
                st.write(f"**Feedback:** {q['feedback']}")
                
                if st.button(f"Excluir Pergunta {i + 1}", key=f"delete_{i}"):
                    st.session_state.questions.pop(i)
                    st.rerun()
    else:
        st.info("Nenhuma pergunta cadastrada ainda.")

def view_responses():
    st.subheader("Respostas dos Participantes")
    
    if not st.session_state.responses:
        st.info("Nenhuma resposta registrada ainda.")
        return
    
    # Filtrar por semana atual
    week_start = get_week_start()
    weekly_responses = [
        r for r in st.session_state.responses
        if datetime.fromisoformat(r['timestamp']) >= week_start
    ]
    
    st.write(f"**Respostas desta semana:** {len(weekly_responses)}")
    
    if weekly_responses:
        # Criar DataFrame
        df_data = []
        for r in weekly_responses:
            df_data.append({
                'CPF': r['cpf'],
                'Pergunta': r['question'][:50] + "..." if len(r['question']) > 50 else r['question'],
                'Resposta': r['selected_option'],
                'Status': '✅ Correta' if r['is_correct'] else '❌ Incorreta',
                'Data': datetime.fromisoformat(r['timestamp']).strftime('%d/%m/%Y %H:%M')
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        
        correct_count = sum(1 for r in weekly_responses if r['is_correct'])
        total_count = len(weekly_responses)
        accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
        
        col1.metric("Total de Respostas", total_count)
        col2.metric("Respostas Corretas", correct_count)
        col3.metric("Taxa de Acerto", f"{accuracy:.1f}%")
        
        # Download CSV
        if st.button("📥 Baixar CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"respostas_quiz_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    
    # Mostrar todas as respostas (histórico)
    if st.checkbox("Mostrar histórico completo"):
        st.subheader("Todas as Respostas")
        
        all_df_data = []
        for r in st.session_state.responses:
            all_df_data.append({
                'CPF': r['cpf'],
                'Pergunta': r['question'][:50] + "..." if len(r['question']) > 50 else r['question'],
                'Resposta': r['selected_option'],
                'Status': '✅ Correta' if r['is_correct'] else '❌ Incorreta',
                'Data': datetime.fromisoformat(r['timestamp']).strftime('%d/%m/%Y %H:%M')
            })
        
        all_df = pd.DataFrame(all_df_data)
        st.dataframe(all_df, use_container_width=True)

# Aplicação principal
def main():
    init_session_state()
    
    # Sidebar para navegação
    st.sidebar.title("Navegação")
    
    if st.sidebar.button("🏠 Quiz"):
        st.session_state.current_page = 'quiz'
    
    if st.sidebar.button("⚙️ Admin"):
        st.session_state.current_page = 'admin'
    
    # Mostrar página atual
    if st.session_state.current_page == 'quiz':
        user_interface()
    elif st.session_state.current_page == 'admin':
        admin_interface()

if __name__ == "__main__":
    main()

