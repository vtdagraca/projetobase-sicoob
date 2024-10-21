import os
import time
import pdfplumber
import pandas as pd
import glob
import pytesseract
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from groq import Groq

# Configuração da API da Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Função para perguntas e respostas usando a API da Groq
def question_answer_groq(question, context):
    messages = [
        {"role": "system", "content": "Você é um assistente de IA didático e objetivo."},
        {"role": "user", "content": question},
        {"role": "assistant", "content": context}
    ]
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=500
    )
    return chat_completion.choices[0].message.content

# Configurações iniciais
driver_path = 'drivers/chromedriver.exe'  # Caminho para o WebDriver
pdf_dir = 'pdfs/'  # Pasta para salvar os PDFs baixados
output_dir = 'output/'  # Pasta para salvar o arquivo CSV de extração

# Função para baixar os PDFs do site
def baixar_pdfs(url):
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.abspath(pdf_dir),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)

    try:
        pdf_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
        )
        for link in pdf_links:
            pdf_url = link.get_attribute('href')
            if pdf_url:
                driver.get(pdf_url)
                time.sleep(5)
    except Exception as e:
        print(f"Erro ao carregar os links PDF: {e}")
    finally:
        driver.quit()

# Função para extrair texto dos PDFs baixados e salvar em um CSV
def extrair_texto_dos_pdfs_para_csv():
    pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))
    extracted_data = []

    if not pdf_files:
        print("Nenhum PDF foi baixado. Verifique o site e o processo de download.")
        return None

    for pdf_file in pdf_files:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                pdf_name = os.path.basename(pdf_file)
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        image = page.to_image()
                        pil_image = image.original.convert("RGB")
                        text = pytesseract.image_to_string(pil_image)
                    if text:
                        extracted_data.append({
                            "Nome do Arquivo": pdf_name,
                            "Página": page_number,
                            "Conteúdo": text
                        })
        except Exception as e:
            print(f"Erro ao processar o arquivo {pdf_file}: {e}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file_path = os.path.join(output_dir, 'relatorio_extraido.csv')
    df = pd.DataFrame(extracted_data)
    df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
    print(f"Processo completo! Relatório salvo em {output_file_path}")
    return output_file_path

# Função para carregar o conteúdo do CSV e permitir perguntas
def carregar_e_perguntar_sobre_csv(csv_path):
    df = pd.read_csv(csv_path)
    
    # Concatena todo o conteúdo para criar um contexto completo
    contexto = " ".join(df["Conteúdo"].tolist())

    # Função interativa para realizar perguntas
    while True:
        pergunta = input("Digite a pergunta que você deseja fazer sobre o conteúdo ou 'sair' para terminar: ")
        if pergunta.lower() == 'sair':
            print("Encerrando o programa.")
            break

        # Envia a pergunta à API Groq com o contexto do CSV
        resposta = question_answer_groq(pergunta, contexto)
        print("Resposta:", resposta)

# Execução do processo
url = input("Digite o site para extração: ")
baixar_pdfs(url)  # Baixa os PDFs do site
csv_path = extrair_texto_dos_pdfs_para_csv()  # Extrai texto e salva em CSV
if csv_path:
    carregar_e_perguntar_sobre_csv(csv_path)  # Carrega o CSV e inicia o sistema de perguntas e respostas
else:
    print("Nenhum conteúdo foi extraído para realizar perguntas.")