import cv2
import os
import pytesseract
import re
import difflib
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook
import requests
from requests.auth import HTTPDigestAuth
import paho.mqtt.publish as publish
import time
from onvif import ONVIFCamera

# ———————————————————————————————————————————————————————————————————————————————————————————————————

# Turma: 1441B-23/2 Turma de Apredizagem Técnica da GM Turno da Manhã
# Componente do Grupo:Victor Bittencourt (@_vicourt), Marcos Filipi (@marcx_ol) e
# Marcos Winicios (@mw_mendess)
# Trabalho funcionando. Em caso de perda, solicitar para: victor.bittencourt@estudante.senairs.edu.br

# Melhorias: API/HUD e Integração MultiTerminal
# OBSERVAÇÃO: Não mude se não sabe o que está fazendo, aja de maneira profissional, existem registros
# de funcionamento em posse dos professores.

# ———————————————————————————————————————————————————————————————————————————————————————————————————

# Todos os endereços do MQTT e outros valores que precisa para realizar as conexões
MQTT_BROKER_HOST = "test.mosquitto.org"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "placasdecar1"
# Não precisa definir usuário e nem senha

# Determina que a condição de liberação será sempre falsa até 2° ordem
global condicao_lib
condicao_lib = False

# Definir o diretório de saída das imagens
global output_directory
output_directory = 'C:\\Users\\projeto\\prog 2508\\plate_regions'

# Globalizar plate_text
global plate_text
plate_text = ""

# Variável global para identificar última mensagem enviada
ultima_mensagem_enviada = ""

# Useless Maggot
def set_zoom(camera, zoom_value):
    request = camera.ptz.create_type('ContinuousMove')
    request.Velocity.Zoom = zoom_value
    camera.ptz.ContinuousMove(request)

# Definindo função principal e suas variáveis internas
def main():
    global ultima_mensagem_enviada
    contador = 0
    global digitpos

    while True:
        with open('output.txt','w') as arquivo:
            arquivo.truncate(0)
        
        # Variáveis do DVR
        dvr_ip = ""
        dvr_port = 80
        dvr_username = ""
        dvr_password = ""
        channel = 2
        camera_url = f"http://{dvr_ip}:{dvr_port}/cgi-bin/snapshot.cgi?channel={channel}"
        auth = HTTPDigestAuth(dvr_username, dvr_password)

        # Variáveis do Banco de Dados da Placa
        excel_path = 'C:\\Users\\projeto\\prog 2508\\PROJETO.xlsx'
        excel_path2 = "C:\\Users\\projeto\\prog 2508\\HISTÓRICO.xlsx"
        sheet_name = 'a_1'
        sheet_name1 = 'Planilha1'
        output_file = 'output.txt'
        resultado_path = r'C:\\Users\\projeto\\prog 2508\\output.txt'

        # Variável do Cascade Plate_Detection
        xml_path = 'C:\\Users\\projeto\\Downloads\\haarcascade_russian_plate_number.xml'
        images_folder = 'C:\\Users\\projeto\\prog 2508\\plate_regions'

        # Variáveis do PyTesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\tesseract\\tesseract.exe'
    
        # Tentar estabelecer a conexão
        try:
            response = requests.get(camera_url, auth=auth, stream=True)

            # Se a conexão estiver para se estabelecer
            if response.status_code == 200:
                image_bytes = bytes()
                for chunk in response.iter_content(chunk_size=1024):
                    image_bytes += chunk

                # Criando uma imagem temporária
                temp_image_path = "temp_camera_image.jpg"
                with open(temp_image_path, "wb") as file:
                    file.write(image_bytes)

                # Definindo a função de reconhecimento das placas baseado no local do arquivo
                plate_cascade = cv2.CascadeClassifier(xml_path)
                 
                # Funções de tratamento da imagem
                image = cv2.imread(temp_image_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                rotated_image = cv2.rotate(image, cv2.ROTATE_180)

                # Definir a detecção das placas
                plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                # Esse comando cria uma localização para saírem as imagens, no caso de ela não existir
                if not os.path.exists(output_directory):
                    os.makedirs(output_directory)
                
                # Definindo por padrão que o estado inicial é FALSO
                plates_found = False

                # Para "i" e (coordenadas) dentro da numeração do arquivo de placas faça "x" coisa
                for i, (x, y, w, h) in enumerate(plates):
                    
                    # Esse trecho pode ser um pouco confuso de se alterar, mas vou explicar brevemente o que
                    # está acontecendo aqui:
                    
                    # Nós ajustamos cada variavel para diferenciar o "crop" da imagem, assim tornando ela
                    # maior ou menor, altere isso somente caso a placa esteja muito fora de centro, ai você
                    # terá uma área de reconhecimento maior. OBS: sempre que alterar mude de 0.05 em diante
                    
                    x_adjusted = x + int(w * 0.15)
                    y_adjusted = y + int(h * 0.25)
                    w_adjusted = int(w * 0.75)
                    h_adjusted = int(h * 0.85)

                    # Definndo região de interesse da placa, no caso, seu "traçamento"
                    plate_region = image[y_adjusted:y_adjusted + h_adjusted, x_adjusted:x_adjusted + w_adjusted]

                    # Aqui ele faz um "pre-set" para a existencia de um futuro arquivo caso a placa seja detectada
                    plate_filename = os.path.join(output_directory, 'plate_0.jpg')
                    cv2.imwrite(plate_filename, plate_region)

                    # Agora as placas estão em estado verdadeiro
                    plates_found = True
                
                # Caso nenhuma placa seja reconhecida na imagem em primeira instância
                # O que é sempre verdade na primeira leitura
                if not plates_found:

                    # Define a última mensagem sempre como resultado de não identificado
                    if ultima_mensagem_enviada != "Sem placa na imagem ou placa não reconhecida.":
                        ultima_mensagem_enviada = "Sem placa na imagem ou placa não reconhecida."

                        # Envia 5 mensagens seguidas para o MQTT (em caso de a internet não estar boa)
                        # Todas as mensagens são para manter em estado LOW a saída do ESP32
                        publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                                       hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                        time.sleep(0.05)

                        publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                                       hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                        time.sleep(0.05)

                        publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                                       hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                        time.sleep(0.05)

                        publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                                       hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                        time.sleep(0.05)

                        publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                                       hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                        time.sleep(0.05)

                        # Ele manda a mensagem no terminal do Python também
                        print(ultima_mensagem_enviada)
                    continue
                
                    # Non-Usable RightNow i guess
                    for filename in os.listdir(output_directory):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                            os.remove(os.path.join(output_directory, filename))

                # Aqui chega na parte monstruosa do código, no caso de ele RECONHECER uma placa
                else:
                    
                    # Ele vai abrir o arquivo de saída e dar um re-size nele, no caso, mudar seu tamanho
                    # "digital"
                    with open(output_file, 'w') as f:
                        f.truncate(0)

                        # Para cada arquivo na pasta de saída, se o arquivo for de "x" tipo, fazer "X" coisa
                        for filename in os.listdir(output_directory):
                            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                                image_path = os.path.join(output_directory, filename)
                                                    
                                # Rodar os filtros e estabelecer o tratamento de imagem
                                image = cv2.imread(image_path)
                                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                                # Aqui estão as proporções destas alterações diferentes do "BOB1509"
                                # onde foram adicionados borrões, tratamentos de vibração e etc.
                                gray = cv2.GaussianBlur(gray,(5,5),0)
                                _, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                                                    
                                # Pegar a estruturação da imagem baseada na sua morfologia
                                get_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
                                morphology = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, get_kernel, iterations=1)
                                invert = 255 - morphology
                                                    
                                # Aqui enfrentamos a dificuldade de leitura desse maravilhoso programa
                                plate_text = pytesseract.image_to_string(invert, config='--psm 6')
                                                                                    
                                # Aqui tivemos uma alteração creio que crucial para o código, onde nós fazemos
                                # o seguinte, nós mudamos o alcance de leitura, retirando letras minusculas dele
                                # "[^a-zA-Z0-9]" para "[^A-Z0-9]"
                                plate_text = re.sub(r'[^A-Z0-9]', '', plate_text)

                                f.write(f"{plate_text}\n")
                                        
                                # Por questões de teste e debug esse trecho te devolve o valor da placa com um timer
                                # print(plate_text)
                                # time.sleep(2.0)

                                # Criar varíavel de reconhecimento se estiver dentro do banco de dados
                                    
            # Caso tudo isso acima dê errado, ele não vai receber o estado da camêra e ligar
            else:
                print(f"Erro ao obter a imagem da câmera. Status de resposta: {response.status_code}")

        # Depois ele printará erro na captura de imagem caso não consiga utilizar do comando try por problemas
        # de identação e etc
        except Exception as e:
            print(f"Erro ao capturar a imagem da câmera: {str(e)}")

        # Independente de o "try" dar um erro, ele ira rodar isto:
        finally:
            
            # Apagar o diretorio
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

        # Irá ler o banco de dados e converter ele para duas listas mais acessiveis pro Python
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Váriaveis de Reconhecimento do Banco de Dados
        pos = 0 # posição da placa no banco de dados
        digitpos = 0 # posição do digito da placa
        counter = 0 # contador de digitos CERTOS

        plateC = plate_text # copiar o texto da câmera
            
        while digitpos < 7:
                
            plateR = df.iloc[pos, 0] # Ler o Lugar da Placa no Banco de Dados
            lenghtDF = len(df["Placas"].index)

            if pos == lenghtDF: # MUDE PARA 19/20/21 E SUBSEQUENTES QUANDO ADICIONAR MAIS UMA PLACA NO BANCO
                 break # SÁI DO LOOP PARA NÃO TRAVAR NUMA LINHA VAZIA
                
            if len(plateR) == len(plateC): # Se os tamanhos forem iguais
                ... # Ele só continua
                    
            else: # Caso não sejam iguais
                main() # Recomeça o programa
                
            if plateR[digitpos] == plateC[digitpos]: # Se os digitos e posições forem iguais
                digitpos += 1; counter += 1 # Passa de digito e contabiliza +1
                    
            else: # Caso não sejam iguais
                digitpos += 1 # Passa de digito
                
            if (digitpos == 7) and (counter < 5): # Caso esteja na última posição e o contador seja menor que 5
                pos += 1; counter = 0; digitpos = 0 # Passa de Placa e zera os contadores
                
            if (digitpos == 7) and (counter >= 5): # Caso esteja na última posição e o contador seja maior ou igual que 5
                break # Ele SAÍ do LOOP
                    
        # Expressão matemática utilizada
        formula = (counter/(len(plateR))*100)
            
        # Formatação da expressão matemática
        value = f'{formula:5.2f}'
            
        # Transformar valor String (yeah) em float
        f_value = float(value)
            
        if (f_value >= 70.00) and ((plateR in df.iloc[pos, 0])):
            # Pegar momento atual
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Pegar planilha e aba dela
            wb = load_workbook(excel_path2)
            ws = wb[sheet_name1]

            # Criar nova linha onde
            new_row = [plate_text, current_datetime]
            ws.append(new_row)
            
            # Salva o arquivo do excel
            wb.save(excel_path2)
            
            # Envia uma mensagem no terminal, atestando que a placa foi reconhecida
            # tanto quanto seu horário de reconhecimento
            print("———————————————————————"); print('Resultado foi aprovado')
            print('Placa identificada como: ', plateR); print('Data e Horário: ', current_datetime)
            
            if (plateR in df.iloc[pos, 0]):
                ultima_mensagem_enviada = "" # Limpa a String
                    
                # Atesta a aprovação 6x para garantir recebimento da mensagem
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                    
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                    
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                    
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(0.05)
                
                # Manda um sinal "0"/LOW para desligar o botão, garantindo que o portão já
                # deve ter chegado ao fim de curso.
                publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(1.0) # Esse time sleep serviria como um "soltar natural" de botão
                
                # Manda outro sinal "1"/HIGH, para ativar o portão novamente e fazer com
                # que ele se feche. Time sleep é igual ao de abertura para garantir fechamento.
                publish.single(MQTT_TOPIC, payload="1", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(5.0)                
                
                # Manda novamente um sinal "0"/LOW, quando supostamente o portão já tiver alcançado o
                # fim de curso avisando que ele está fechado.
                publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
                time.sleep(1.0) # Esse time sleep serviria como um "soltar natural" de botão
                
        else: 
            ultima_mensagem_enviada = "———————————————————————" # Preenche a String
                    
            # Manda o sinal de 0 5x para travar/negar acesso
            publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
            time.sleep(0.05)
                    
            publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
            time.sleep(0.05)
                    
            publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
            time.sleep(0.05)
                    
            publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
            time.sleep(0.05)
                    
            publish.single(MQTT_TOPIC, payload="0", qos=0, retain=False, 
                            hostname=MQTT_BROKER_HOST, port=MQTT_BROKER_PORT)
            time.sleep(0.05)
                    
            print(ultima_mensagem_enviada) # Envia a String de linha
            print("Placa Não Reconhecida/Negada. Tentando Novamente.") # Manda a negação
                    
            ultima_mensagem_enviada = "" # Zera a String

if __name__ == "__main__":
    main()
    