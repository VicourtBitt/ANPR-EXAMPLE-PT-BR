# IMAGE TREATMENT and CHAR RECOG (tratamento de imagem e reconhecimento de caractéres)
import pytesseract
import cv2
from onvif import ONVIFCamera

# SYSTEM MODULES (módulos do sistema)
import os
import re
import difflib
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth
import time
import string

# DATA ANALISYS (análise de dados)
import pandas as pd
from openpyxl import load_workbook

# MQTT COMM (comunicação MQTT)
import paho.mqtt.publish as publish

# ———————————————————————————————————————————————————————————————————————————————————————————————————

# Turma: 1441B-23/2 Turma de Apredizagem Técnica da GM Turno da Manhã
# Componente do Grupo:Victor Bittencourt (@_vicourt), Marcos Filipi (@marcx_ol) e
# Marcos Winicios (@mw_mendess)
# Trabalho funcionando. Em caso de perda, solicitar para: victor.bittencourt@estudante.senairs.edu.br

# Melhorias: API/HUD e Integração MultiTerminal
# OBSERVAÇÃO: Não mude se não sabe o que está fazendo, aja de maneira profissional, existem registros
# de funcionamento em posse dos professores.

# ———————————————————————————————————————————————————————————————————————————————————————————————————

# MQTT VARIABLES (HOST/PORT/TOPIC)
MQTT_BROKER_HOST = "test.mosquitto.org"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "placasdecar1"
# there's no need to declare user and password

# IMAGE OUTPUT DIRECTORY
global output_directory
output_directory = "C:\\Downloads\\plate_regions"
# I guess it will work in every computer (at least on windows)

# TEXT FROM PLATE
global plate_text
plate_text = ""

# LAST MESSAGE SENT
last_sent_message = ""

# ALFANUMERIC LIST
letters = list(string.ascii_uppercase)
numbers = list(range(0,10))

# ZOOM function probably non-used 
def set_zoom(camera, zoom_value):
    request = camera.ptz.create_type('ContinuousMove')
    request.Velocity.Zoom = zoom_value
    camera.ptz.ContinuousMove(request)

# MAIN function
def main():
    
    while True:
        with open('output.txt', 'w') as txtfile:
            txtfile.truncate(0)

        # DVR or NVD Variables
        dvr_ip = ""
        dvr_port = 80
        dvr_username = "admin"
        dvr_password = "admin123"
        channel = 2
        camera_url = f"http://{dvr_ip}:{dvr_port}/cgi-bin/snapshot.cgi?channel={channel}"
        auth = HTTPDigestAuth(dvr_username, dvr_password)

        # Plates DataBank
        excel_path = "C:\\Downloads\\NewSheet.xlsx"
        sheet_name1 = "Planilha1"
        sheet_name2 = "Planilha2" 
        output_file = "output.txt"
        results_path = "C:\\Downloads\\output.txt"

        # Cascade Detection Variables
        xml_path = "C:\\Downloads\\haarcascade_russian_plate_number.xml"
        images_folder = "C:\\Downloads"

        # PyTesseract Variables
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\tesseract\\tesseract.exe'

        # Trying to establish the conection
        try:
            response = requests.get(camera_url, auth=auth, stream=True)

            # If we're geting the conection
            if response.status_code == 200:
                image_bytes = bytes()
                for chunk in response.iter_content(chunk_size=1024):
                    image_bytes += chunk
                
                # Creating an temp image
                temp_image_path = "temp_camera_image.jpg"
                with open(temp_image_path, "wb") as file:
                    file.write(image_bytes)

                # Creating the recog variable by using cascade path
                plate_cascade = cv2.CascadeClassifier(xml_path)

                # Image treatment variables
                image = cv2.imread(temp_image_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                rotated_image = cv2.rotate(image, cv2.ROTATE_180)

                # Plate Detection
                plates = plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))

                # This will create an folder
                if not os.path.exists(output_directory):
                    os.makedirs(output_directory)
                
                # Initial State for "There's any plate on screen?"
                plates_found = False

                # For each coordinate do "x" thing
                for i, (x, y, w, h) in enumerate(plates):
                    
                    x_adjusted = x + int(w * 0.15)
                    y_adjusted = y + int(h * 0.25)
                    w_adjusted = int(w * 0.75)
                    h_adjusted = int(h * 0.85)

                    # ROI in this image
                    plate_region = image[y_adjusted:y_adjusted + h_adjusted, x_adjusted:x_adjusted + w_adjusted]

                    # Creating or swaping the file in this folder
                    plate_filename = os.path.join(output_directory, 'plate_0.jpg')
                    cv2.imwrite(plate_filename, plate_region)

                    # Then, now, the state is changed
                    plates_found = True

                if not plates_found:

                    if last_sent_message != "Não existe placa reconhecida na imagem.":
                        last_sent_message = "Não existe placa reconhecida na imagem."

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

                        print(last_sent_message)
                    continue
                
                else:
                    with open (output_file, 'w') as f:
                        f.truncate(0)

                        for filename in os.listdir(output_directory):
                            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                                image_path = os.path.join(output_directory, filename)

                                image = cv2.imread(image_path)
                                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                                gray = cv2.GaussianBlur(gray(5,5),0)
                                _, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                                get_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
                                morphology = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, get_kernel, iterations=1)
                                invert = 255 - morphology
                                                    
                                plate_text = pytesseract.image_to_string(invert, config='--psm 6')

                                plate_text = re.sub(r'[^A-Z0-9]', '', plate_text)

                                f.write(f"{plate_text}\n")

            else:
                print(f"Erro ao obter a imagem da câmera. Status de resposta: {response.status_code}")

        except Exception as e:
            print(f"Erro ao capturar imagem da câmera: {str(e)}")

        finally:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

        df = pd.read_excel(excel_path, sheet_name=sheet_name1)
        lenghtDF = (len(df["Plates"].index))

        platepos = 0
        digitpos = 0
        counter = 0
        
        rearranged_plate = ""
        plateC = plate_text

        while digitpos < 7:
           while digitpos < 3:
                
            if plateC[digitpos] not in letters:
                if plateC[digitpos] == "0":
                            rearranged_plate += "O"
                        
                if plateC[digitpos] == "1":
                            rearranged_plate += "I"
                        
                if plateC[digitpos] == "2":
                            rearranged_plate += "Z"

                if plateC[digitpos] == "3":
                            rearranged_plate += "B"
                        
                if plateC[digitpos] == "4":
                            rearranged_plate += "A"

                if plateC[digitpos] == "5":
                            rearranged_plate += "S"

                if plateC[digitpos] == "6":
                            rearranged_plate += "G"

                if plateC[digitpos] == "7":
                            rearranged_plate += "T"
                        
                if plateC[digitpos] == "8":
                            rearranged_plate += "B"

                if plateC[digitpos] == "9":
                            rearranged_plate += "Q"
                    
            if plateC[digitpos] in letters:
                        rearranged_plate += plate_text[digitpos]
                    
            digitpos += 1

        while digitpos < 4:

            if plateC[digitpos] not in numbers:
                if plateC[digitpos] == "O":
                            rearranged_plate += "0"
                        
                if plateC[digitpos] == "I":
                            rearranged_plate += "1"
                        
                if plateC[digitpos] == "Z":
                            rearranged_plate += "2"

                if plateC[digitpos] == "B":
                            rearranged_plate += "3"
                        
                if plateC[digitpos] == "A":
                            rearranged_plate += "4"

                if plateC[digitpos] == "S":
                            rearranged_plate += "5"

                if plateC[digitpos] == "G":
                            rearranged_plate += "6"

                if plateC[digitpos] == "T":
                            rearranged_plate += "7"
                        
                if plateC[digitpos] == "B":
                            rearranged_plate += "8"

                if plateC[digitpos] == "Q":
                            rearranged_plate += "9"
                    
            if plateC[digitpos] in numbers:
                rearranged_plate += plateC[digitpos]
                    
            digitpos += 1
                
            rearranged_plate += plateC[digitpos]
            digitpos += 1

        while digitpos < 7:

            if plateC[digitpos] not in numbers:
                if plateC[digitpos] == "O":
                            rearranged_plate += "0"
                        
                if plateC[digitpos] == "I":
                            rearranged_plate += "1"
                        
                if plateC[digitpos] == "Z":
                            rearranged_plate += "2"

                if plateC[digitpos] == "B":
                            rearranged_plate += "3"
                        
                if plateC[digitpos] == "A":
                            rearranged_plate += "4"

                if plateC[digitpos] == "S":
                            rearranged_plate += "5"

                if plateC[digitpos] == "G":
                            rearranged_plate += "6"

                if plateC[digitpos] == "T":
                            rearranged_plate += "7"
                        
                if plateC[digitpos] == "B":
                            rearranged_plate += "8"

                if plateC[digitpos] == "Q":
                            rearranged_plate += "9"
                    
            if plateC[digitpos] in numbers:
                        rearranged_plate += plateC[digitpos]

            digitpos += 1

            lenghtDF = (len(df["Placas"].index))
        
        digitpos = 0

        while platepos < lenghtDF:
                
            plateR = df.iloc[platepos,0]
                
            if platepos == lenghtDF:
                    main()
                
            if len(plateR) != len(rearranged_plate):
                    main()
                
            if plateR[digitpos] == rearranged_plate[digitpos]:
                    counter += 1
                    digitpos += 1
            else:
                    digitpos += 1

            if counter < 6 and digitpos == 7:
                    platepos += 1
                    counter = 0
                    digitpos = 0
                
            if counter >= 6 and digitpos == 7:
                    print("Okay")
                    break
        
        break

    formula = (counter/(len(plateR))*100)
    value = float(f'{formula:5.2f}')
    f_value = str(value) + "%"

    if (value >= 80.00) and ((plateR in df.iloc[platepos,0])):
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            wb = load_workbook(excel_path)
            ws = wb[sheet_name2]

            new_row = [plateR, current_datetime]
            ws.append(new_row)

            wb.save(excel_path)

            print("———————————————————————"); print('Resultado foi aprovado')
            print('Placa identificada como: ', plateR); print('Data e Horário: ', current_datetime)
            
            if (plateR in df.iloc[platepos, 0]):
                last_sent_message = "" # Limpa a String
                    
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
            last_sent_message = "———————————————————————" # Preenche a String
                    
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
                    
            print(last_sent_message) # Envia a String de linha
            print("Placa Não Reconhecida/Negada. Tentando Novamente.") # Manda a negação
                    
            last_sent_message = "" # Zera a String

if __name__ == "__main__":
    main()