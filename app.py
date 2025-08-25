import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import re

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
    if 'current_user_cpf' not in st.session_state:
        st.session_state.current_user_cpf = None
    if 'current_user_name' not in st.session_state:
        st.session_state.current_user_name = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 'cpf'  # cpf -> name -> quiz -> result
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'quiz'

def reset_quiz():
    """Reseta o quiz para o início"""
    st.session_state.current_user_cpf = None
    st.session_state.current_user_name = None
    st.session_state.current_step = 'cpf'
    st.session_state.current_question_index = 0
    st.session_state.user_answers = []

# Interface para usuários
def user_interface():
    st.title("❓ Quiz Semanal")
    
    if st.session_state.current_step == 'cpf':
        show_cpf_step()
    elif st.session_state.current_step == 'name':
        show_name_step()
    elif st.session_state.current_step == 'quiz':
        show_quiz_step()
    elif st.session_state.current_step == 'result':
        show_result_step()

def show_cpf_step():
    st.subheader("📋 Etapa 1: Identificação")
    st.write("Digite seu CPF para participar do quiz:")
    
    cpf_input = st.text_input(
        "CPF",
        placeholder="000.000.000-00",
        max_chars=14,
        help="Digite seu CPF para identificação",
        key="cpf_input"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("Próximo ➡️", type="primary", use_container_width=True):
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
                    st.error("❌ Você já participou esta semana! Aguarde a próxima semana.")
                else:
                    st.session_state.current_user_cpf = formatted_cpf
                    st.session_state.current_step = 'name'
                    st.rerun()
            else:
                st.error("❌ CPF inválido! Por favor, digite um CPF válido.")

def show_name_step():
    st.subheader("👤 Etapa 2: Nome")
    st.write("Agora digite seu nome completo:")
    
    name_input = st.text_input(
        "Nome Completo",
        placeholder="Digite seu nome completo",
        help="Digite seu nome completo",
        key="name_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.current_step = 'cpf'
            st.rerun()
    
    with col3:
        if st.button("Próximo ➡️", type="primary", use_container_width=True):
            if name_input.strip():
                st.session_state.current_user_name = name_input.strip()
                st.session_state.current_step = 'quiz'
                st.session_state.current_question_index = 0
                st.rerun()
            else:
                st.error("❌ Por favor, digite seu nome completo!")

def show_quiz_step():
    if not st.session_state.questions:
        st.warning("⚠️ Nenhuma pergunta disponível no momento.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Tentar Novamente", use_container_width=True):
                reset_quiz()
                st.rerun()
        return
    
    current_q_index = st.session_state.current_question_index
    total_questions = len(st.session_state.questions)
    
    # Verificar se acabaram as perguntas
    if current_q_index >= total_questions:
        st.session_state.current_step = 'result'
        st.rerun()
        return
    
    current_question = st.session_state.questions[current_q_index]
    
    # Mostrar progresso
    progress = (current_q_index + 1) / total_questions
    st.progress(progress)
    st.write(f"**Pergunta {current_q_index + 1} de {total_questions}**")
    
    st.subheader(f"❓ {current_question['question']}")
    
    # Opções de resposta
    selected_option = st.radio(
        "Escolha sua resposta:",
        current_question['options'],
        key=f"question_{current_q_index}"
    )
    
    # Botões de navegação
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if current_q_index == 0:
            if st.button("⬅️ Voltar", use_container_width=True):
                st.session_state.current_step = 'name'
                st.rerun()
        else:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state.current_question_index -= 1
                st.rerun()
    
    with col3:
        if current_q_index == total_questions - 1:
            button_text = "🏁 Finalizar"
        else:
            button_text = "Próximo ➡️"
        
        if st.button(button_text, type="primary", use_container_width=True):
            # Salvar resposta atual
            selected_index = current_question['options'].index(selected_option)
            is_correct = selected_index == current_question['correct_answer']
            
            answer = {
                'question_index': current_q_index,
                'question': current_question['question'],
                'selected_option': selected_option,
                'selected_index': selected_index,
                'correct_answer': current_question['correct_answer'],
                'correct_option': current_question['options'][current_question['correct_answer']],
                'is_correct': is_correct,
                'feedback': current_question.get('feedback', '')
            }
            
            # Atualizar ou adicionar resposta
            if len(st.session_state.user_answers) > current_q_index:
                st.session_state.user_answers[current_q_index] = answer
            else:
                st.session_state.user_answers.append(answer)
            
            # Próxima pergunta ou finalizar
            if current_q_index == total_questions - 1:
                # Finalizar quiz
                save_final_response()
                st.session_state.current_step = 'result'
            else:
                st.session_state.current_question_index += 1
            
            st.rerun()

def save_final_response():
    """Salva todas as respostas do usuário"""
    final_response = {
        'cpf': st.session_state.current_user_cpf,
        'name': st.session_state.current_user_name,
        'answers': st.session_state.user_answers,
        'total_questions': len(st.session_state.questions),
        'correct_answers': sum(1 for a in st.session_state.user_answers if a['is_correct']),
        'score_percentage': (sum(1 for a in st.session_state.user_answers if a['is_correct']) / len(st.session_state.questions)) * 100,
        'timestamp': datetime.now().isoformat()
    }
    
    st.session_state.responses.append(final_response)

def show_result_step():
    st.subheader("🎯 Resultado do Quiz")
    
    if not st.session_state.user_answers:
        st.error("Erro: Nenhuma resposta encontrada.")
        return
    
    total_questions = len(st.session_state.user_answers)
    correct_answers = sum(1 for a in st.session_state.user_answers if a['is_correct'])
    score_percentage = (correct_answers / total_questions) * 100
    
    # Mostrar pontuação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Perguntas", total_questions)
    with col2:
        st.metric("Respostas Corretas", correct_answers)
    with col3:
        st.metric("Pontuação", f"{score_percentage:.1f}%")
    
    # Feedback geral
    if score_percentage >= 80:
        st.success("🎉 Excelente! Parabéns pelo seu desempenho!")
    elif score_percentage >= 60:
        st.info("👍 Bom trabalho! Continue assim!")
    else:
        st.warning("📚 Continue estudando! Você pode melhorar!")
    
    # Mostrar detalhes de cada pergunta
    st.subheader("📊 Detalhes das Respostas")
    
    for i, answer in enumerate(st.session_state.user_answers):
        with st.expander(f"Pergunta {i + 1}: {answer['question'][:50]}..."):
            st.write(f"**Pergunta:** {answer['question']}")
            st.write(f"**Sua resposta:** {answer['selected_option']}")
            st.write(f"**Resposta correta:** {answer['correct_option']}")
            
            if answer['is_correct']:
                st.success("✅ Resposta correta!")
            else:
                st.error("❌ Resposta incorreta")
            
            if answer['feedback']:
                st.info(f"**Feedback:** {answer['feedback']}")
    
    # Botão para refazer
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Fazer Novo Quiz", type="primary", use_container_width=True):
            reset_quiz()
            st.rerun()

# Interface administrativa
def admin_interface():
    st.title("🔧 Painel Administrativo")
    
    if not st.session_state.admin_authenticated:
        st.subheader("🔐 Login Administrativo")
        password = st.text_input("Senha", type="password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Entrar", type="primary", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
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
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚪 Sair", type="secondary", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

def manage_questions():
    st.subheader("➕ Adicionar Nova Pergunta")
    
    with st.form("new_question_form", clear_on_submit=True):
        question_text = st.text_input("Pergunta")
        
        st.write("**Opções de resposta:**")
        option1 = st.text_input("Opção 1")
        option2 = st.text_input("Opção 2")
        option3 = st.text_input("Opção 3")
        option4 = st.text_input("Opção 4")
        
        correct_answer = st.selectbox(
            "Resposta correta",
            [0, 1, 2, 3],
            format_func=lambda x: f"Opção {x + 1}"
        )
        
        feedback = st.text_area("Feedback da resposta", help="Explicação ou informação adicional sobre a resposta correta")
        
        submitted = st.form_submit_button("➕ Adicionar Pergunta", type="primary", use_container_width=True)
        
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
                st.success(f"✅ Pergunta {len(st.session_state.questions)} adicionada com sucesso!")
                st.rerun()
            else:
                st.error("❌ Por favor, preencha todos os campos!")
    
    # Lista de perguntas existentes
    st.subheader(f"📋 Perguntas Existentes ({len(st.session_state.questions)})")
    
    if st.session_state.questions:
        for i, q in enumerate(st.session_state.questions):
            with st.expander(f"Pergunta {i + 1}: {q['question'][:50]}..."):
                st.write(f"**Pergunta:** {q['question']}")
                st.write("**Opções:**")
                for j, option in enumerate(q['options']):
                    prefix = "✅" if j == q['correct_answer'] else "•"
                    st.write(f"{prefix} {option}")
                st.write(f"**Feedback:** {q['feedback']}")
                st.write(f"**Criada em:** {datetime.fromisoformat(q['created_at']).strftime('%d/%m/%Y %H:%M')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🗑️ Excluir", key=f"delete_{i}", type="secondary"):
                        st.session_state.questions.pop(i)
                        st.success(f"Pergunta {i + 1} excluída!")
                        st.rerun()
                
                with col2:
                    if st.button(f"⬆️ Mover para cima", key=f"up_{i}", disabled=(i == 0)):
                        if i > 0:
                            st.session_state.questions[i], st.session_state.questions[i-1] = st.session_state.questions[i-1], st.session_state.questions[i]
                            st.rerun()
    else:
        st.info("📝 Nenhuma pergunta cadastrada ainda. Adicione a primeira pergunta acima!")

def view_responses():
    st.subheader("📊 Respostas dos Participantes")
    
    if not st.session_state.responses:
        st.info("📋 Nenhuma resposta registrada ainda.")
        return
    
    # Filtrar por semana atual
    week_start = get_week_start()
    weekly_responses = [
        r for r in st.session_state.responses
        if datetime.fromisoformat(r['timestamp']) >= week_start
    ]
    
    st.write(f"**Respostas desta semana:** {len(weekly_responses)}")
    
    if weekly_responses:
        # Criar abas para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["📊 Estatísticas", "📋 Lista Detalhada", "🆔 Lista de CPFs"])
        
        with tab1:
            # Estatísticas gerais
            col1, col2, col3, col4 = st.columns(4)
            
            total_responses = len(weekly_responses)
            avg_score = sum(r['score_percentage'] for r in weekly_responses) / total_responses
            best_score = max(r['score_percentage'] for r in weekly_responses)
            total_questions = weekly_responses[0]['total_questions'] if weekly_responses else 0
            
            col1.metric("Total de Participantes", total_responses)
            col2.metric("Média Geral", f"{avg_score:.1f}%")
            col3.metric("Melhor Pontuação", f"{best_score:.1f}%")
            col4.metric("Total de Perguntas", total_questions)
            
            # Gráfico simples de distribuição de notas
            if len(weekly_responses) > 1:
                scores = [r['score_percentage'] for r in weekly_responses]
                score_ranges = {
                    "0-30%": len([s for s in scores if s < 30]),
                    "30-60%": len([s for s in scores if 30 <= s < 60]),
                    "60-80%": len([s for s in scores if 60 <= s < 80]),
                    "80-100%": len([s for s in scores if s >= 80])
                }
                
                st.subheader("📈 Distribuição de Pontuações")
                for range_name, count in score_ranges.items():
                    if count > 0:
                        percentage = (count / len(scores)) * 100
                        st.write(f"**{range_name}:** {count} participantes ({percentage:.1f}%)")
        
        with tab2:
            # Lista detalhada (código original)
            st.subheader("📋 Respostas Completas")
            
            for i, response in enumerate(weekly_responses):
                with st.expander(f"Participante {i+1}: {response['name']} - {response['score_percentage']:.1f}%"):
                    st.write(f"**CPF:** {response['cpf']}")
                    st.write(f"**Nome:** {response['name']}")
                    st.write(f"**Pontuação:** {response['correct_answers']}/{response['total_questions']} ({response['score_percentage']:.1f}%)")
                    st.write(f"**Data:** {datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y %H:%M')}")
                    
                    # Mostrar respostas individuais
                    st.write("**Respostas:**")
                    for j, answer in enumerate(response['answers']):
                        status = "✅" if answer['is_correct'] else "❌"
                        st.write(f"{j+1}. {status} {answer['selected_option']}")
        
        with tab3:
            # Nova aba: Lista de CPFs
            st.subheader("🆔 Lista de CPFs dos Participantes")
            st.write("CPFs de todos que responderam o quiz esta semana:")
            
            # Criar lista de CPFs únicos (caso alguém responda mais de uma vez)
            cpfs_list = []
            names_list = []
            dates_list = []
            scores_list = []
            
            for response in weekly_responses:
                cpfs_list.append(response['cpf'])
                names_list.append(response['name'])
                dates_list.append(datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y %H:%M'))
                scores_list.append(f"{response['score_percentage']:.1f}%")
            
            # Mostrar em formato de tabela simples
            cpf_df = pd.DataFrame({
                'CPF': cpfs_list,
                'Nome': names_list,
                'Pontuação': scores_list,
                'Data': dates_list
            })
            
            st.dataframe(cpf_df, use_container_width=True, hide_index=True)
            
            # Seção com CPFs para cópia fácil
            st.subheader("📋 CPFs para Cópia")
            st.write("Lista de CPFs separados por vírgula:")
            
            cpfs_text = ', '.join(cpfs_list)
            st.text_area(
                "CPFs:",
                value=cpfs_text,
                height=100,
                help="Você pode selecionar todo o texto e copiar (Ctrl+C)"
            )
            
            # Lista numerada
            st.subheader("📝 Lista Numerada de CPFs")
            for i, cpf in enumerate(cpfs_list, 1):
                st.write(f"{i}. {cpf}")
            
            # Botão para download apenas dos CPFs
            st.subheader("📥 Download Lista de CPFs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download CPFs simples (apenas CPFs)
                cpfs_simple = '\n'.join(cpfs_list)
                st.download_button(
                    label="📄 Download CPFs (TXT)",
                    data=cpfs_simple,
                    file_name=f"cpfs_quiz_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime='text/plain'
                )
            
            with col2:
                # Download CPFs com nomes (CSV)
                cpfs_csv = cpf_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 Download CPFs + Dados (CSV)",
                    data=cpfs_csv,
                    file_name=f"cpfs_completo_quiz_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime='text/csv'
                )
        
        # Download completo (mantido da versão original)
        st.subheader("📥 Exportar Dados Completos")
        if st.button("📥 Baixar Respostas Completas (CSV)", type="primary"):
            # Criar dados para CSV
            csv_data = []
            for response in weekly_responses:
                for j, answer in enumerate(response['answers']):
                    csv_data.append({
                        'CPF': response['cpf'],
                        'Nome': response['name'],
                        'Pergunta_Numero': j + 1,
                        'Pergunta': answer['question'],
                        'Resposta_Selecionada': answer['selected_option'],
                        'Resposta_Correta': answer['correct_option'],
                        'Status': 'Correta' if answer['is_correct'] else 'Incorreta',
                        'Pontuacao_Final': f"{response['score_percentage']:.1f}%",
                        'Data': datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y %H:%M')
                    })
            
            df = pd.DataFrame(csv_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV Completo",
                data=csv,
                file_name=f"respostas_completas_quiz_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime='text/csv'
            )
    
    # Mostrar histórico completo
    if st.checkbox("📚 Mostrar histórico completo"):
        st.subheader("📊 Todas as Respostas (Histórico)")
        
        # CPFs do histórico completo
        all_cpfs = [r['cpf'] for r in st.session_state.responses]
        if all_cpfs:
            with st.expander("🆔 Todos os CPFs do Histórico"):
                all_cpfs_text = ', '.join(set(all_cpfs))  # Remove duplicatas
                st.text_area(
                    "Todos os CPFs que já participaram:",
                    value=all_cpfs_text,
                    height=80
                )
        
        for i, response in enumerate(st.session_state.responses):
            with st.expander(f"Histórico {i+1}: {response['name']} - {datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y')}"):
                st.write(f"**CPF:** {response['cpf']}")
                st.write(f"**Nome:** {response['name']}")
                st.write(f"**Pontuação:** {response['correct_answers']}/{response['total_questions']} ({response['score_percentage']:.1f}%)")
                st.write(f"**Data:** {datetime.fromisoformat(response['timestamp']).strftime('%d/%m/%Y %H:%M')}")

# Aplicação principal
def main():
    init_session_state()
    
    # Sidebar para navegação
    st.sidebar.title("🧭 Navegação")
    st.sidebar.write(f"**Total de Perguntas:** {len(st.session_state.questions)}")
    st.sidebar.write(f"**Total de Respostas:** {len(st.session_state.responses)}")
    
    if st.sidebar.button("🏠 Quiz", use_container_width=True):
        st.session_state.current_page = 'quiz'
    
    if st.sidebar.button("⚙️ Admin", use_container_width=True):
        st.session_state.current_page = 'admin'
    
    # Botão de reset para admins
    if st.session_state.admin_authenticated:
        st.sidebar.write("---")
        if st.sidebar.button("🔄 Reset Quiz (Admin)", type="secondary"):
            reset_quiz()
            st.rerun()
    
    # Mostrar página atual
    if st.session_state.current_page == 'quiz':
        user_interface()
    elif st.session_state.current_page == 'admin':
        admin_interface()

if __name__ == "__main__":
    main()

