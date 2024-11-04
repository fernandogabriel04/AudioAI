import ia_audio as st
import whisper
from openai import OpenAI
import subprocess
import sqlite3
from datetime import datetime
import os

# Configuração do banco de dados
def inicializar_banco():
    conexao = sqlite3.connect("dados_audio.db")
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
    conexao.close()

# Função para salvar os dados
def salvar_dados(transcricao, relatorio, audio_data, localizacao):
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexao = sqlite3.connect("dados_audio.db")
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO registros (transcricao, relatorio, data_hora, audio, localizacao) VALUES (?, ?, ?, ?, ?)",
                   (transcricao, relatorio, data_hora, audio_data, localizacao))
    conexao.commit()
    conexao.close()
    
# Função para converter áudio para .wav usando ffmpeg
def converter_para_wav(arquivo_audio):
    arquivo_wav = "temp_audio.wav"
    comando_ffmpeg = ["ffmpeg", "-i", arquivo_audio, "-ar", "16000", "-ac", "1", "-y", arquivo_wav]
    subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return arquivo_wav

# Função para transcrever o áudio
def transcrever_audio(arquivo_audio):
    if not arquivo_audio.endswith(".wav"):
        arquivo_audio = converter_para_wav(arquivo_audio)
    resultado = modelo_whisper.transcribe(arquivo_audio)
    return resultado['text']

# Função para gerar um relatório detalhado
def gerar_relatorio_detalhado(texto):
    prompt = f"Sabendo que se trata de um texto que sera encaminhado para uma secretaria municipal. Primeiro classifique o texto em algumas dessas opções: Meio Ambiente, Educação, Fazenda, Infraestrutura, Abastecimento pesca e agricultura, Turismo, Saúde, Esporte. Depois escreva uma subcategoria. Em seguida defina o tema principal abordado. Após esses dois passos, faça um resumo bem objetivo. Conteúdo: {texto}"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        relatorio = response.choices[0].message.content
    except AttributeError:
        relatorio = "Erro ao gerar o relatório."
    return relatorio



# Carregar o modelo Whisper
modelo_whisper = whisper.load_model("large")

# Inicializar o cliente OpenAI
client = OpenAI()  # Defina sua API_KEY nas variáveis de ambiente

# Interface com Streamlit
st.title("Envie um áudio, a prefeitura de Maceió quer te ouvir!")
st.write("Grave um áudio e nós te ouviremos!")

# Inicializar banco de dados
inicializar_banco()

bairros = ["Centro", "Benedito Bentes", "Jacintinho", "Feitosa"]
localizacao = st.selectbox("Selecione o bairro que voce está presente:", bairros)


audio_recorded = None

if localizacao:  # Verifica se um bairro foi selecionado
    audio_recorded = st.experimental_audio_input("Grave um áudio")
else:
    st.warning("Por favor, selecione o bairro em que você está presente antes de gravar o áudio.")
    
if audio_recorded:
    st.audio(audio_recorded)
    with open("temp_input_audio.wav", "wb") as f:
        audio_data = audio_recorded.getbuffer()
        f.write(audio_data)

    # Processamento do áudio
    transcricao = transcrever_audio("temp_input_audio.wav")
    relatorio = gerar_relatorio_detalhado(transcricao)
    
    # Exibição dos resultados
    st.subheader("Transcrição:")
    st.write(transcricao)
    st.subheader("Relatório Detalhado:")
    st.write(relatorio)

    # Salvar no banco de dados
    salvar_dados(transcricao, relatorio, audio_data, localizacao)
    
    # Apagar arquivo de audio gerado
    os.remove("temp_input_audio.wav")