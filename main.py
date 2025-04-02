import os
import psutil
import subprocess
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Monitor de Sistema Linux",
    page_icon="🖥️",
    layout="wide"
)

# Título da aplicação
st.title("🖥️ Monitor de Sistema Linux")

# Função para obter dados de memória
def get_memory_data():
    memory = psutil.virtual_memory()
    return {
        "total": memory.total / (1024 ** 3),  # GB
        "available": memory.available / (1024 ** 3),  # GB
        "used": memory.used / (1024 ** 3),  # GB
        "percent": memory.percent
    }

# Função para obter dados de CPU
def get_cpu_data():
    return {
        "percent": psutil.cpu_percent(interval=0.1),
        "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
    }

# Função para obter lista de processos
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
        try:
            proc_info = proc.info
            proc_info['memory_mb'] = proc.memory_info().rss / (1024 * 1024)  # MB
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

# Função para matar um processo
def kill_process(pid):
    try:
        process = psutil.Process(pid)
        process.terminate()
        return True, f"Processo {pid} finalizado com sucesso."
    except Exception as e:
        return False, f"Erro ao finalizar processo {pid}: {str(e)}"

# Função para alterar permissões
def change_permissions(path, user_perm, group_perm, others_perm, user=None, group=None):
    try:
        # Construir string de permissão (ex: 755)
        perm_string = f"{user_perm}{group_perm}{others_perm}"
        
        # Executar comando chmod
        subprocess.run(['chmod', perm_string, path], check=True)
        
        # Alterar proprietário/grupo se especificado
        if user or group:
            owner = user if user else ""
            group_name = group if group else ""
            owner_string = f"{owner}:{group_name}" if owner and group_name else owner or group_name
            if owner_string:
                subprocess.run(['chown', owner_string, path], check=True)
        
        return True, f"Permissões alteradas com sucesso para {path}"
    except Exception as e:
        return False, f"Erro ao alterar permissões: {str(e)}"

# Criar abas para diferentes funcionalidades
tab1, tab2, tab3, tab4 = st.tabs(["📊 Memória", "🔄 CPU", "⚙️ Processos", "🔒 Permissões"])

with tab1:
    st.header("Utilização de Memória")
    
    # Criar contêineres para gráficos
    memory_chart_container = st.container()
    memory_history_container = st.container()
    
    # Inicializar histórico de memória se não existir
    if 'memory_history' not in st.session_state:
        st.session_state.memory_history = []
        st.session_state.memory_times = []
    
    # Obter dados atuais de memória
    memory_data = get_memory_data()
    
    # Adicionar ao histórico (limitando a 100 pontos)
    st.session_state.memory_history.append(memory_data["percent"])
    st.session_state.memory_times.append(datetime.now())
    if len(st.session_state.memory_history) > 100:
        st.session_state.memory_history.pop(0)
        st.session_state.memory_times.pop(0)
    
    with memory_chart_container:
        # Criar gráfico de gauge para uso atual
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory_data["percent"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Uso de Memória (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar detalhes de memória
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", f"{memory_data['total']:.2f} GB")
        col2.metric("Usado", f"{memory_data['used']:.2f} GB")
        col3.metric("Disponível", f"{memory_data['available']:.2f} GB")
    
    with memory_history_container:
        # Criar gráfico de histórico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=st.session_state.memory_times,
            y=st.session_state.memory_history,
            mode='lines+markers',
            name='Uso de Memória (%)',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title="Histórico de Uso de Memória",
            xaxis_title="Tempo",
            yaxis_title="Uso (%)",
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Utilização de CPU")
    
    # Criar contêineres para gráficos
    cpu_chart_container = st.container()
    cpu_history_container = st.container()
    
    # Inicializar histórico de CPU se não existir
    if 'cpu_history' not in st.session_state:
        st.session_state.cpu_history = []
        st.session_state.cpu_times = []
    
    # Obter dados atuais de CPU
    cpu_data = get_cpu_data()
    
    # Adicionar ao histórico (limitando a 100 pontos)
    st.session_state.cpu_history.append(cpu_data["percent"])
    st.session_state.cpu_times.append(datetime.now())
    if len(st.session_state.cpu_history) > 100:
        st.session_state.cpu_history.pop(0)
        st.session_state.cpu_times.pop(0)
    
    with cpu_chart_container:
        # Criar gráfico de gauge para uso atual
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_data["percent"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Uso de CPU (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [50, 80], 'color': "orange"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar uso por núcleo
        st.subheader("Uso por Núcleo")
        per_cpu = cpu_data["per_cpu"]
        fig = go.Figure(data=[
            go.Bar(
                x=[f"Core {i}" for i in range(len(per_cpu))],
                y=per_cpu,
                marker_color=['lightgreen' if x < 50 else 'orange' if x < 80 else 'red' for x in per_cpu]
            )
        ])
        fig.update_layout(
            title="Uso por Núcleo de CPU (%)",
            xaxis_title="Núcleo",
            yaxis_title="Uso (%)",
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with cpu_history_container:
        # Criar gráfico de histórico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=st.session_state.cpu_times,
            y=st.session_state.cpu_history,
            mode='lines+markers',
            name='Uso de CPU (%)',
            line=dict(color='green', width=2)
        ))
        fig.update_layout(
            title="Histórico de Uso de CPU",
            xaxis_title="Tempo",
            yaxis_title="Uso (%)",
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Gerenciador de Processos")
    
    # Obter lista de processos
    processes = get_processes()
    
    # Criar DataFrame
    df = pd.DataFrame(processes)
    
    # Ordenar por uso de memória (padrão)
    sort_by = st.selectbox("Ordenar por:", ["memory_percent", "cpu_percent", "pid", "name", "username"])
    df = df.sort_values(by=sort_by, ascending=False)
    
    # Filtrar processos
    filter_text = st.text_input("Filtrar processos (nome ou usuário):")
    if filter_text:
        df = df[df['name'].str.contains(filter_text, case=False) | 
                df['username'].str.contains(filter_text, case=False)]
    
    # Mostrar tabela de processos
    st.dataframe(df)
    
    # Finalizar processo
    st.subheader("Finalizar Processo")
    col1, col2 = st.columns([1, 3])
    with col1:
        pid_to_kill = st.number_input("PID do processo:", min_value=1, step=1)
    with col2:
        if st.button("Finalizar Processo"):
            success, message = kill_process(int(pid_to_kill))
            if success:
                st.success(message)
            else:
                st.error(message)

with tab4:
    st.header("Gerenciador de Permissões")
    
    # Selecionar arquivo/pasta
    file_path = st.text_input("Caminho do arquivo ou pasta:")
    
    if file_path and os.path.exists(file_path):
        # Mostrar informações atuais
        file_stat = os.stat(file_path)
        current_mode = oct(file_stat.st_mode)[-3:]  # Últimos 3 dígitos do modo octal
        
        st.info(f"Permissões atuais: {current_mode}")
        
        # Interface para alterar permissões
        st.subheader("Alterar Permissões")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Proprietário")
            owner_read = st.checkbox("Leitura", value=True)
            owner_write = st.checkbox("Escrita", value=True)
            owner_exec = st.checkbox("Execução", value=False)
        
        with col2:
            st.write("Grupo")
            group_read = st.checkbox("Leitura (Grupo)", value=True)
            group_write = st.checkbox("Escrita (Grupo)", value=False)
            group_exec = st.checkbox("Execução (Grupo)", value=False)
        
        with col3:
            st.write("Outros")
            others_read = st.checkbox("Leitura (Outros)", value=True)
            others_write = st.checkbox("Escrita (Outros)", value=False)
            others_exec = st.checkbox("Execução (Outros)", value=False)
        
        # Calcular valores numéricos
        owner_val = (4 if owner_read else 0) + (2 if owner_write else 0) + (1 if owner_exec else 0)
        group_val = (4 if group_read else 0) + (2 if group_write else 0) + (1 if group_exec else 0)
        others_val = (4 if others_read else 0) + (2 if others_write else 0) + (1 if others_exec else 0)
        
        st.info(f"Novas permissões: {owner_val}{group_val}{others_val}")
        
        # Alterar proprietário/grupo
        st.subheader("Alterar Proprietário/Grupo")
        col1, col2 = st.columns(2)
        with col1:
            new_owner = st.text_input("Novo proprietário (deixe em branco para não alterar):")
        with col2:
            new_group = st.text_input("Novo grupo (deixe em branco para não alterar):")
        
        # Botão para aplicar alterações
        if st.button("Aplicar Alterações"):
            success, message = change_permissions(
                file_path, 
                str(owner_val), 
                str(group_val), 
                str(others_val),
                new_owner if new_owner else None,
                new_group if new_group else None
            )
            if success:
                st.success(message)
            else:
                st.error(message)
    else:
        if file_path:
            st.error(f"O caminho '{file_path}' não existe.")
        else:
            st.warning("Digite o caminho de um arquivo ou pasta para gerenciar suas permissões.")

# Adicionar botão para atualizar dados
if st.button("Atualizar Dados"):
    st.rerun()
