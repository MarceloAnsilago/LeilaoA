import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import sqlite3

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
        lote INTEGER
    );
    """
    conn.execute(create_table_sql)
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

# Função para inserir os dados no banco
def insert_data(conn, df):
    for _, row in df.iterrows():
        conn.execute("""
            INSERT INTO bovinos (numero_gta, lacre, M_0_8, F_0_8, M_9_12, F_9_12, M_13_24, F_13_24, M_25_36, F_25_36, M_36_mais, F_36_mais, lote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['N.º Série'], row['Lacre'], row['M 0 - 8'], row['F 0 - 8'], row['M 9 - 12'], row['F 9 - 12'],
            row['M 13 - 24'], row['F 13 - 24'], row['M 25 - 36'], row['F 25 - 36'], row['M 36 +'], row['F 36 +'], row['Lotes']
        ))
    conn.commit()

# Main Function - Página de Carregar Dados
def carregar_dados():
    st.title("Carregar Planilha de Dados das GTAs e Brincos")
    
    conn = create_connection()
    create_table(conn)

    # Verifica se há dados no banco
    data = check_data(conn)
    
    if data:
        st.warning("Dados salvos no banco de dados.")
        # Convertendo os dados do banco para um DataFrame
        df = pd.DataFrame(data, columns=['id', 'numero_gta', 'lacre', 'M_0_8', 'F_0_8', 'M_9_12', 'F_9_12', 'M_13_24', 'F_13_24', 'M_25_36', 'F_25_36', 'M_36_mais', 'F_36_mais', 'lote'])
        
        # Exibindo os dados em tabela
        st.dataframe(df)

        # Calculando os totais de cada faixa etária
        totais, total_machos, total_femeas, total_animais = calcular_totais(df)
        
        # Exibindo os totais em uma tabela com efeito zebra
        st.subheader("Totais por Faixa Etária e Sexo")
        totais_df = pd.DataFrame.from_dict({
            "Faixa Etária": list(totais.keys()),
            "Total": list(totais.values())
        })

        # Ocultar o índice e aplicar o efeito zebra nas linhas
        st.markdown("""
        <style>
        tbody tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        </style>
        """, unsafe_allow_html=True)

        st.table(totais_df.style.hide(axis="index"))  # Oculta o índice

        # Exibindo os totais de machos, fêmeas e total geral
        st.write(f"**Total de Machos: {total_machos}**")
        st.write(f"**Total de Fêmeas: {total_femeas}**")
        st.write(f"**Total de Animais: {total_animais}**")
        
        # Botão para excluir dados existentes
        if st.button("Excluir todos os dados"):
            delete_data(conn)
            st.success("Todos os dados foram excluídos com sucesso!")
    
    else:
        # Upload do arquivo
        uploaded_file = st.file_uploader("Escolha um arquivo Excel ou ODS", type=["xlsx", "xls", "ods"])
        
        if uploaded_file is not None:
            try:
                # Carregar dados para um DataFrame
                df = pd.read_excel(uploaded_file)
                st.success("Dados carregados com sucesso!")
                st.dataframe(df)  # Exibe os dados carregados

                # Inserir dados da planilha no banco
                if st.button("Salvar dados no banco"):
                    insert_data(conn, df)
                    st.success("Dados salvos no banco de dados com sucesso!")

            except Exception as e:
                st.error(f"Erro ao carregar o arquivo: {e}")

# Estrutura do Menu
def main():
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu Principal",  # título do menu
            options=["Visualizar Lotes", "Gerar Planilha", "Carregar Dados"],  # Carregar Dados agora na última posição
            icons=["eye", "file-earmark-excel", "upload"],  # ícones opcionais
            menu_icon="cast",  # ícone do menu principal
            default_index=0,  # seleciona a primeira opção ao iniciar
        )

    if selected == "Carregar Dados":
        carregar_dados()

    elif selected == "Visualizar Lotes":
        st.title("Visualizar Lotes")
        st.write("Funcionalidade em construção.")

    elif selected == "Gerar Planilha":
        st.title("Gerar Planilha")
        st.write("Funcionalidade em construção.")

if __name__ == "__main__":
    main()
