from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import pdfplumber
import pandas as pd
import glob
import pytesseract
from PIL import Image

# Solicita a URL ao usuário antes de iniciar o WebDriver
url = input("Digite o site para extração: ")

# Confs iniciais
driver_path = 'drivers/chromedriver.exe'  # Caminho para o seu WebDriver
pdf_dir = 'pdfs/'  # Pasta onde os PDFs serão salvos
output_dir = 'output/'  # Pasta para salvar o arquivo CSV

# Configurações de Download para o Chrome
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": os.path.abspath(pdf_dir),  # Define a pasta de download
    "download.prompt_for_download": False,                    # Desativa a solicitação de download
    "plugins.always_open_pdf_externally": True               # Baixa PDFs em vez de abri-los
}
chrome_options.add_experimental_option("prefs", prefs)

# Configura o WebDriver usando o Service e as Opções
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Acessa a URL fornecida
driver.get(url)

# Espera até que todos os links para arquivos PDF estejam presentes na página
try:
    pdf_links = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
    )
except Exception as e:
    print(f"Erro ao carregar os links PDF: {e}")
    driver.quit()

# Cria a pasta para armazenar PDFs, se ela não existir
os.makedirs(pdf_dir, exist_ok=True)

# baixa cada PDF encontrado
for link in pdf_links:
    try:
        pdf_url = link.get_attribute('href')
        if pdf_url:
            driver.get(pdf_url)
            time.sleep(10)  # Ajuste conforme necessário para aguardar o download do PDF
    except Exception as e:
        print(f"Erro ao acessar o link de PDF: {e}")

# Fecha o navegador após o download
driver.quit()

print("Carregando, aguarde...")
# Espera o download de todos os arquivos por um tempo adicional
time.sleep(30)

# Verifica se há arquivos PDF baixados
pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))

if not pdf_files:
    print("Nenhum PDF foi baixado. Verifique o site e o processo de download.")
else:
    print(f"{len(pdf_files)} PDFs foram baixados com sucesso.")

    # Processa os PDFs baixados
    extracted_data = []

    # Itera sobre cada PDF para extração de texto com OCR, quando necessário
    for pdf_file in pdf_files:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        # Tenta extrair a imagem da página e aplicar OCR
                        image = page.to_image()
                        pil_image = image.original.convert("RGB")
                        text = pytesseract.image_to_string(pil_image)
                       
                    if text:
                        extracted_data.append({
                            "Nome do Arquivo": os.path.basename(pdf_file),
                            "Página": page_number,
                            "Conteúdo": text
                        })
                    else:
                        print(f"Texto não encontrado na página {page_number} do arquivo {pdf_file}.")
        except Exception as e:
            print(f"Erro ao processar o arquivo {pdf_file}: {e}")

    # Cria o diretório de saída para o CSV, se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Exporta os dados extraídos para um arquivo CSV
    if extracted_data:
        # Converte a lista de dados extraídos em DataFrame
        df = pd.DataFrame(extracted_data)

        # Salva o DataFrame em um arquivo CSV
        output_file_path = os.path.join(output_dir, 'relatorio_extraido.csv')
        df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
        print(f"Processo completo! Relatório salvo em {output_file_path}")
    else:
        print("Nenhum texto foi extraído dos PDFs. Verifique o conteúdo dos arquivos. :(")

print("Extração finalizada! :)")

# Função para buscar o nome do arquivo PDF
pdf_name = input("Buscar PDF: ")

# Verifica se o arquivo existe na pasta de PDFs baixados
pdf_path = os.path.join(pdf_dir, pdf_name)
if not os.path.exists(pdf_path):
    print("Arquivo não encontrado. Verifique o nome e tente novamente.")
else:
    # Abre o PDF e exibe o conteúdo de cada página
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                # Extrai o texto usando OCR se não houver texto na página
                image = page.to_image()
                pil_image = image.original.convert("RGB")
                text = pytesseract.image_to_string(pil_image)
            
            # Exibe o número da página e o texto extraído
            print(f"\nPágina {page_number}:\n{text}\n{'-'*40}")