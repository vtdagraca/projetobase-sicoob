import os
import pandas as pd
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def question_answer(question, context):
    # Define a mensagem para o modelo
    messages = [
        {"role": "system", "content": "Você é um assistente de IA didático e objetivo."},
        {"role": "user", "content": question},
        {"role": "assistant", "content": context}
    ]
    
    # Faz a requisição de conclusão
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=0.9,
        max_tokens=500
    )
    
    # Retorna a resposta do modelo
    return chat_completion.choices[0].message.content

# Função para carregar o CSV e obter contexto relevante
def obter_contexto_relevante(df, question):
    # Divide a pergunta em palavras-chave e busca no conteúdo do CSV
    palavras = question.split()
    linhas_relevantes = df[df['Conteúdo'].str.contains('|'.join(palavras), case=False, na=False)]
    return " ".join(linhas_relevantes['Conteúdo'].tolist())[:3000]  # Limita o contexto a 3000 caracteres

# Função interativa para realizar perguntas sobre o conteúdo do CSV
def carregar_e_perguntar_com_filtragem(csv_path):
    df = pd.read_csv(csv_path)
    while True:
        pergunta = input("Digite a pergunta que você deseja fazer sobre o conteúdo ou 'sair' para terminar: ")
        if pergunta.lower() == 'sair':
            print("Encerrando o programa.")
            break

        # Obter o contexto relevante com base na pergunta
        contexto_relevante = obter_contexto_relevante(df, pergunta)
        resposta = question_answer(pergunta, contexto_relevante)
        print("Resposta:", resposta)

# Executa a função de perguntas e respostas com o caminho do CSV
csv_path = 'output/relatorio_extraido.csv'
carregar_e_perguntar_com_filtragem(csv_path)