import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import sqlite3
from datetime import datetime


# Função para criar a conexão com o banco de dados
def create_connection():
    conn = sqlite3.connect('bovinos.db')
    return conn

# Função para criar a tabela de bovinos
def create_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS bovinos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_gta TEXT NOT NULL,
        lacre INTEGER,
        M_0_8 INTEGER,
        F_0_8 INTEGER,
        M_9_12 INTEGER,
        F_9_12 INTEGER,
        M_13_24 INTEGER,
        F_13_24 INTEGER,
        M_25_36 INTEGER,
        F_25_36 INTEGER,
        M_36_mais INTEGER,
        F_36_mais INTEGER,
        lote INTEGER,
        proprietario_origem TEXT,
        propriedade_origem TEXT
    );
    """
    conn.execute(create_table_sql)

    # Tabela de histórico de correções
    create_history_table_sql = """
    CREATE TABLE IF NOT EXISTS historico_correcoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_bovino INTEGER,
        gta_original TEXT,
        gta_corrigida TEXT,
        motivo_correcao TEXT,
        data_correcao TEXT,
        FOREIGN KEY (id_bovino) REFERENCES bovinos(id)
    );
    """
    conn.execute(create_history_table_sql)
    conn.commit()

# Função para excluir todos os dados da tabela bovinos
def delete_data(conn):
    conn.execute("DELETE FROM bovinos")
    conn.commit()

# Função para verificar se há dados no banco
def check_data(conn):
    query = "SELECT * FROM bovinos"
    cursor = conn.execute(query)
    data = cursor.fetchall()
    return data

# Função para calcular os totais por faixa etária
def calcular_totais(df):
    totais = {
        "M 0-8": df["M_0_8"].sum(),
        "F 0-8": df["F_0_8"].sum(),
        "M 9-12": df["M_9_12"].sum(),
        "F 9-12": df["F_9_12"].sum(),
        "M 13-24": df["M_13_24"].sum(),
        "F 13-24": df["F_13_24"].sum(),
        "M 25-36": df["M_25_36"].sum(),
        "F 25-36": df["F_25_36"].sum(),
        "M 36+": df["M_36_mais"].sum(),
        "F 36+": df["F_36_mais"].sum(),
    }
    total_machos = totais["M 0-8"] + totais["M 9-12"] + totais["M 13-24"] + totais["M 25-36"] + totais["M 36+"]
    total_femeas = totais["F 0-8"] + totais["F 9-12"] + totais["F 13-24"] + totais["F 25-36"] + totais["F 36+"]
    total_animais = total_machos + total_femeas
    return totais, total_machos, total_femeas, total_animais

# Função para verificar duplicatas
def verificar_duplicatas(df):
    duplicatas_lacre = df[df.duplicated(subset=['Lacre'], keep=False)]
    duplicatas_gta = df[df.duplicated(subset=['N.º Série'], keep=False)]
    return duplicatas_lacre, duplicatas_gta

# Função para registrar uma correção no histórico
def registrar_correcao(conn, id_bovino, gta_original, gta_corrigida, motivo):
    data_correcao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO historico_correcoes (id_bovino, gta_original, gta_corrigida, motivo_correcao, data_correcao)
        VALUES (?, ?, ?, ?, ?)
    """, (id_bovino, gta_original, gta_corrigida, motivo, data_correcao))
    conn.commit()

# Função para realizar a correção da GTA
def corrigir_gta(conn, id_bovino, nova_gta, motivo):
    cursor = conn.execute("SELECT numero_gta FROM bovinos WHERE id = ?", (id_bovino,))
    gta_original = cursor.fetchone()[0]
    
    # Atualiza a GTA no banco de dados
    conn.execute("UPDATE bovinos SET numero_gta = ? WHERE id = ?", (nova_gta, id_bovino))
    conn.commit()
    
    # Registrar a correção no histórico
    registrar_correcao(conn, id_bovino, gta_original, nova_gta, motivo)

# Função para inserir os dados no banco
def insert_data(conn, df):
    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO bovinos (numero_gta, lacre, M_0_8, F_0_8, M_9_12, F_9_12, M_13_24, F_13_24, M_25_36, F_25_36, M_36_mais, F_36_mais, lote, proprietario_origem, propriedade_origem)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['N.º Série'], row['Lacre'], row['M 0 - 8'], row['F 0 - 8'], row['M 9 - 12'], row['F 9 - 12'],
            row['M 13 - 24'], row['F 13 - 24'], row['M 25 - 36'], row['F 25 - 36'], row['M 36 +'], row['F 36 +'], row['Lotes'],
            row['Proprietário Origem'], row['Propriedade de Origem']
        ))
    conn.commit()

# Função para exibir o histórico de correções
def exibir_historico(conn):
    query = "SELECT * FROM historico_correcoes"
    df_historico = pd.read_sql(query, conn)
    st.subheader("Histórico de Correções")
    st.dataframe(df_historico)

# Função para listar os bovinos e permitir correções
def listar_bovinos_para_correcao(conn):
    query = "SELECT * FROM bovinos"
    df_bovinos = pd.read_sql(query, conn)
    
    st.subheader("Lista de Bovinos")
    st.dataframe(df_bovinos)
    
    # Selecionar o bovino para corrigir
    bovino_selecionado = st.selectbox("Selecione o bovino para corrigir", df_bovinos['id'])
    
    # Inserir a nova GTA e o motivo da correção
    nova_gta = st.text_input("Nova GTA")
    motivo_correcao = st.text_area("Motivo da correção")
    
    if st.button("Corrigir GTA"):
        corrigir_gta(conn, bovino_selecionado, nova_gta, motivo_correcao)
        st.success("GTA corrigida e registrada no histórico com sucesso!")









def gerar_lotes(conn):
    st.title("Gerar Lotes")

    # Inicializar as variáveis de estado, se não existirem
    if 'lote_gerado' not in st.session_state:
        st.session_state['lote_gerado'] = None
    
    if 'cards' not in st.session_state:
        st.session_state['cards'] = []

    if 'mostrar_gerar_lote' not in st.session_state:
        st.session_state['mostrar_gerar_lote'] = True

    # Mostrar botão "Novo Lote" sempre
    if st.button("Novo Lote", key="novo_lote_inicial"):
        st.session_state['mostrar_gerar_lote'] = True
        st.session_state['lote_gerado'] = None
        st.session_state['cards'] = []

    # Formulário para "Gerar Lote" aparece ao clicar em "Novo Lote"
    if st.session_state['mostrar_gerar_lote']:
        # Criar as duas colunas para gerar o lote
        col1, col2 = st.columns([2, 1])
        
        with col1:
            novo_lote = st.text_input("Informe o novo lote", key="lote_input")
        
        with col2:
            gerar_lote_button = st.button("Gerar Lote", key="gerar_lote_button")
        
        # Se o botão for clicado e um lote foi informado, guarda o valor do lote e remove o formulário
        if gerar_lote_button and novo_lote:
            st.session_state['lote_gerado'] = novo_lote
            st.session_state['mostrar_gerar_lote'] = False

    # Formulário para buscar brinco sempre aparece abaixo do botão "Novo Lote" ou após gerar o lote
    if st.session_state['lote_gerado']:
        with st.form(key='form_busca_brinco'):
            st.subheader("Buscar Brinco")
            numero_brinco = st.text_input("Informe o número do brinco", key="brinco_input")
            buscar_brinco_button = st.form_submit_button(label="Buscar Brinco")
            
            if buscar_brinco_button:
                # Consultar o banco de dados para buscar o brinco
                query = "SELECT * FROM bovinos WHERE lacre = ?"
                cursor = conn.execute(query, (numero_brinco,))
                bovino = cursor.fetchone()
                
                if bovino:
                    # Identificar as faixas etárias e quantidades diferentes de 0
                    faixas_etarias = {
                        "M 0-8": bovino[3], "F 0-8": bovino[4],
                        "M 9-12": bovino[5], "F 9-12": bovino[6],
                        "M 13-24": bovino[7], "F 13-24": bovino[8],
                        "M 25-36": bovino[9], "F 25-36": bovino[10],
                        "M 36+": bovino[11], "F 36+": bovino[12]
                    }
                    
                    faixas_validas = {faixa: qtd for faixa, qtd in faixas_etarias.items() if qtd > 0}

                    # Exibir os dados do bovino encontrados
                    st.write("**Dados do Bovino Encontrado**")
                    st.write(f"**GTA:** {bovino[1]}")
                    st.write(f"**Lacre (Brinco):** {bovino[2]}")
                    st.write(f"**Faixa Etária:**")

                    # Exibir cada faixa etária com quantidade diferente de zero
                    for faixa, qtd in faixas_validas.items():
                        st.write(f"- **{faixa}:** {qtd}")
                    
                    # Exibir corretamente as colunas proprietario_origem e propriedade_origem
                    st.write(f"**Proprietário de Origem:** {bovino[14]}")
                    st.write(f"**Propriedade de Origem:** {bovino[15]}")

                    # Armazenar os dados encontrados no estado
                    st.session_state['bovino_atual'] = {
                        "GTA": bovino[1],
                        "Lacre": bovino[2],
                        "Proprietário": bovino[14],
                        "Propriedade": bovino[15],
                        "Faixas": faixas_validas
                    }
                else:
                    st.error("Brinco não encontrado no banco de dados.")

    # Mostrar o botão de "Inserir Lote" somente após os dados terem sido encontrados
    if 'bovino_atual' in st.session_state:
        if st.button("Inserir Lote", key="inserir_lote_button"):
            # Adicionar os dados do bovino atual ao quadro de lote
            st.session_state['cards'].append(st.session_state['bovino_atual'])
            st.success("GTA inserido no lote com sucesso!")
            
            # Remover o bovino atual do estado para evitar duplicações
            del st.session_state['bovino_atual']

    # Exibir os bovinos adicionados ao lote
    if st.session_state['lote_gerado'] and st.session_state['cards']:
        # Mover o lote gerado para baixo do botão "Inserir Lote"
        st.markdown(f"""
            <h4 style="color: #4CAF50;">Lote Gerado: {st.session_state['lote_gerado']}</h4>
        """, unsafe_allow_html=True)

        st.markdown(f"<h5>Resumo: {len(st.session_state['cards'])} bovinos adicionados ao lote.</h5>", unsafe_allow_html=True)

        for card in st.session_state['cards']:
            faixas_str = ", ".join([f"{faixa}: {qtd}" for faixa, qtd in card['Faixas'].items()])
            
            st.markdown(f"""
                <div style="border: 1px solid #d9d9d9; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <p><strong>GTA:</strong> {card['GTA']}</p>
                    <p><strong>Lacre (Brinco):</strong> {card['Lacre']}</p>
                    <p><strong>Proprietário de Origem:</strong> {card['Proprietário']}</p>
                    <p><strong>Propriedade de Origem:</strong> {card['Propriedade']}</p>
                    <p><strong>Faixas Etárias:</strong> {faixas_str}</p>
                </div>
            """, unsafe_allow_html=True)









# Main Function - Página de Carregar Dados
def carregar_dados():
    st.title("Carregar Planilha de Dados das GTAs e Brincos")
    
    conn = create_connection()
    create_table(conn)

    # Verifica se há dados no banco
    data = check_data(conn)
    
    if data:
        st.warning("Dados salvos no banco de dados.")
        df = pd.DataFrame(data, columns=['id', 'numero_gta', 'lacre', 'M_0_8', 'F_0_8', 'M_9_12', 'F_9_12', 'M_13_24', 'F_13_24', 'M_25_36', 'F_25_36', 'M_36_mais', 'F_36_mais', 'lote', 'proprietario_origem', 'propriedade_origem'])
        
        # Exibindo os dados em tabela
        st.dataframe(df)

        totais, total_machos, total_femeas, total_animais = calcular_totais(df)
        
        st.subheader("Totais por Faixa Etária e Sexo")
        totais_df = pd.DataFrame.from_dict({
            "Faixa Etária": list(totais.keys()),
            "Total": list(totais.values())
        })

        st.markdown("""
        <style>
        tbody tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        </style>
        """, unsafe_allow_html=True)

        st.table(totais_df.style.hide(axis="index"))

        st.write(f"**Total de Machos: {total_machos}**")
        st.write(f"**Total de Fêmeas: {total_femeas}**")
        st.write(f"**Total de Animais: {total_animais}**")
        
        if st.checkbox("Deseja excluir todos os dados?"):
            if st.button("Excluir todos os dados"):
                delete_data(conn)
                st.success("Todos os dados foram excluídos com sucesso!")
    
    else:
        uploaded_file = st.file_uploader("Escolha um arquivo Excel ou ODS", type=["xlsx", "xls", "ods"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.success("Dados carregados com sucesso!")
                st.dataframe(df)

                duplicatas_lacre, duplicatas_gta = verificar_duplicatas(df)
                if not duplicatas_lacre.empty or not duplicatas_gta.empty:
                    st.warning("Existem lacres ou GTAs duplicados!")
                    
                    if not duplicatas_lacre.empty:
                        st.subheader("Lacres Duplicados")
                        st.dataframe(duplicatas_lacre)

                    if not duplicatas_gta.empty:
                        st.subheader("GTAs Duplicadas")
                        st.dataframe(duplicatas_gta)

                if st.button("Salvar dados no banco"):
                    insert_data(conn, df)
                    st.success("Dados salvos no banco de dados com sucesso!")

            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {e}")

# Estrutura do Menu
def main():
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu Principal",
            options=["Visualizar Lotes", "Gerar Planilha", "Carregar Dados", "Corrigir GTA", "Exibir Histórico", "Gerar Lotes"],
            icons=["eye", "file-earmark-excel", "upload", "edit", "history", "plus-circle"],
            menu_icon="cast",
            default_index=0,
        )

    conn = create_connection()

    if selected == "Carregar Dados":
        carregar_dados()

    elif selected == "Visualizar Lotes":
        st.title("Visualizar Lotes")
        st.write("Funcionalidade em construção.")

    elif selected == "Gerar Planilha":
        st.title("Gerar Planilha")
        st.write("Funcionalidade em construção.")
    
    elif selected == "Corrigir GTA":
        listar_bovinos_para_correcao(conn)
    
    elif selected == "Exibir Histórico":
        exibir_historico(conn)

    elif selected == "Gerar Lotes":
        gerar_lotes(conn)

if __name__ == "__main__":
    main()
