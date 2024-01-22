Um sistema de Reconhecimento de Placas Veiculares feito por um aprendiz Brasileiro de Python (do qual não teve muito tempo para aprender), o código não está polido ou sequer no seu melhor estado (mas existe uma versão funcional do mesmo).

Como o código funciona:

Inicialmente o código tenta se conectar e autenticar a conexão antes de reunir as informações que são distribuídas do NVD/DVR da Intelbras (utilizando o IP do mesmo, Port, User e Password), que por si mesmo controla as câmeras conectadas nele. Depois que ele pega essas imagens (que são fotos tiradas constantemente por um link que estabelece a conexão) ele
começa a realizar seu real trabalho, que é: Traçar uma área de interesse na imagem (ROI) usando método CascadeClassifier e PlateCascade, a partir disso a ROI vai ser salva (já que é a região exata da placa), depois de ser salva, alguns comandos do OpenCV2 serão utilizados para tratar a imagem e melhorar a detecção de superfície dela.
Quando o tratamento acaba, o PyTesseract tenta reconhecer padrões/similaridades desses caracteres, para então devolver o texto resultante, a partir daí o código segue dois caminhos diferentes dependendo da versão utilizada:

  1° Se estiver utilizando a versão 1.0 (sem o filtro de caracteres no código), o filtro só vai passar caracteres similares, se passarem de 5 dos 7, o código envia um sinal ao MQTT, caso não, volta ao início.

  2° Se estiver utilizando a versão 1.1 (não testada, com filtro de caracteres), o código vai substituir caracteres fora de posição, utilizando de uma condição mal-feita (não aprendi a criar classes ainda e minhas funções feitas pra esse caso deram errado) que vai identificar e comparar posições e substituir caracteres fora delas no padrão da placa
    Mercosul.
      Sendo sincero, quando digo condição mal-feita é por causa do meu pouco tempo para fazer o projeto de TCC (que funcionou), tive somente 3 meses e não consegui estudar Python realmente como eu deveria, mesmo ficando quase 8 horas no dia por dia codando.
      
Por fim, quando o filtro de similaridade de caracteres termina seu serviço, o código vai analisar se a placa tratada está no banco de dados, caso esteja ele vai mandar um sinal para o ESP pelo MQTT Broker, que então fara sua devida ativação.

Quais módulos/bibliotecas de Python são utilizadas nesse trabalho?

  paho.mqtt (pip install paho-mqtt)
  openCV2 (pip install opencv-python-headless)
  pandas (pip install pandas)
  tesseract/PyTessract (instalar primeiro o tesseractOCR e depois abrir ambiente virtual para rodar o pip install pytesseract)
  
Os outros módulos ou são previamente instalados pelo próprio Python ou são módulos dos quais não foram retirados previamente do trabalho.
