import streamlit as st
import whisper
from openai import OpenAI
import sqlite3
from datetime import datetime
import os

# Configuração do banco de dados
def inicializar_banco(conexao):
    cursor = conexao.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS registros (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transcricao TEXT,
                        relatorio TEXT,
                        data_hora TEXT,
                        audio BLOB,
                        bairro TEXT
                    )''')
    conexao.commit()

# Função para salvar os dados
def salvar_dados(conexao, transcricao, relatorio, audio_data, localizacao):
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO registros (transcricao, relatorio, data_hora, audio, bairro) VALUES (?, ?, ?, ?, ?)",
                   (transcricao, relatorio, data_hora, audio_data, localizacao))
    conexao.commit()

# Função para transcrever o áudio
def transcrever_audio(arquivo_audio):
    resultado = modelo_whisper.transcribe(arquivo_audio)
    return resultado['text']

# Função para gerar um relatório detalhado
def gerar_relatorio_detalhado(texto):
    prompt = (
            f"Sabendo que se trata de um texto que será encaminhado para uma secretaria municipal."
            f"Primeiro classifique o texto em algumas dessas opções: Meio Ambiente, Educação, Fazenda, Infraestrutura, Limpeza Urbana, Turismo, Saúde, Mobilidade Urbana."
            f"Depois escreva uma subcategoria. Algumas opções de subcategorias: vagas para sepultamento, indicação de descarte irregular, falta de coleta domiciliar, poda de arvore, supressão de arvore, capinação, limpeza em geral, tapar buraco, implantação de asfalto, manutenção de vias não pavimentadas, alagamento, afundamento, limpeza de boca de lobo, marcação de exames consultas e cirurgias, unidade de saúde, atendimento medico. Em seguida defina o tema principal abordado."
            f"Após esses passos, faça um resumo bem objetivo."
            f"sempre me retorne nessa estrutura, exemplo: Categoria: Infraestrutura Subcategoria: Praças Tema: Iluminação Resumo: puxar do texto"
            f"Gere de acordo com esse conteúdo: {texto}"
              )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    relatorio = response.choices[0].message.content
    return relatorio

# Inicialização
modelo_whisper = whisper.load_model("base")
apikey = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=apikey)
conexao = sqlite3.connect("db/dados_audio.db")
inicializar_banco(conexao)

# Interface com Streamlit
st.title("Envie um áudio, a prefeitura de Maceió quer te ouvir!")
st.write("Por favor, selecione o bairro em que você está presente antes de gravar o áudio.")
bairros = ["Centro", "Benedito Bentes", "Jacintinho", "Feitosa"]
localizacao = st.selectbox("Selecione o bairro:", bairros)

# Somente habilita gravação após seleção de bairro
if localizacao:
    audio_recorded = st.experimental_audio_input("Grave um áudio")
    if audio_recorded:
        st.audio(audio_recorded)
        with open("temp_input_audio.wav", "wb") as f:
            audio_data = audio_recorded.getbuffer()
            f.write(audio_data)
        # audio_data = audio_recorded.read()

        # Processamento do áudio
        transcricao = transcrever_audio("temp_input_audio.wav")
        relatorio = gerar_relatorio_detalhado(transcricao)
        
        # Exibição dos resultados e salvar no banco
        st.subheader("Transcrição:")
        st.write(transcricao)
        st.subheader("Relatório Detalhado:")
        st.write(relatorio)
        salvar_dados(conexao, transcricao, relatorio, audio_data, localizacao)
        
        # Apagar arquivo de audio gerado
        # Apagar arquivo de audio gerado
        os.remove("temp_input_audio.wav")

# Fechar conexão com o banco ao final
conexao.close()
