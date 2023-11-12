from tkinter import *
from tkinter import filedialog
from PIL import ImageTk, Image
import cv2
import numpy as np

# Função para abrir o arquivo selecionado
def abrir_arquivo():
    # Abre a janela de seleção de arquivo
    global imagem_destino_cv
    arquivo = filedialog.askopenfilename(initialdir = "/", title = "Selecione o arquivo", filetypes = (("Arquivos JPG", "*.jpg"),
                                                                                                        ("Todos os arquivos", "*.*")))
    # Verifica se um arquivo foi selecionado
    if arquivo != "":
        # Carrega a imagem
        imagem = Image.open(arquivo)
        imagem_destino_cv = cv2.imread(arquivo)
        # Verifica se a resolução da imagem é maior que 1080x720
        if imagem.width > 1080 and imagem.height > 720:
            proporcao = min(1080/imagem.width, 720/imagem.height)
            nova_largura = int(imagem.width * proporcao)
            nova_altura = int(imagem.height * proporcao)
            imagem = imagem.resize((nova_largura, nova_altura))
            imagem_destino_cv = cv2.resize(imagem_destino_cv, (nova_largura, nova_altura))
        
        # Converte a imagem para o formato suportado pelo Tkinter
        imagem_tk = ImageTk.PhotoImage(imagem)
        # Exibe a imagem na janela principal
        label_imagem2.config(image = imagem_tk)
        label_imagem2.image = imagem_tk
        botao_arquivo2.destroy()

def abrir_recorte():
    label_imagem1.config(image = imagem_tk_roi)
    label_imagem1.image = imagem_tk_roi
    # Para não existir borda branca quando colocarmos uma imagem sobre a outra
    label_imagem1.config(bg = 'black', bd = 0)
    botao_arquivo1.destroy()

# callback function para o mouse
def desenha_retangulo(event, x, y, flags, params):
    global x_start, y_start, x_end, y_end, cropping, roi

    # Se apertarmos o botão do mouse
    if event == cv2.EVENT_LBUTTONDOWN:
        x_start, y_start, x_end, y_end = x, y, x, y
        cropping = True

    # Se o mouse estiver se movendo
    elif event == cv2.EVENT_MOUSEMOVE:
        if cropping == True:
            x_end, y_end = x, y

    # Se o botão esquerdo do mouse for solto
    elif event == cv2.EVENT_LBUTTONUP:
        x_end, y_end = x, y
        cropping = False 
        refPoint = [(x_start, y_start), (x_end, y_end)]
        if len(refPoint) == 2: 
            roi = imagem_cv[refPoint[0][1]:refPoint[1][1], refPoint[0][0]:refPoint[1][0]]

def drag_inicio(event):
    widget = event.widget
    # Linha que permite com que o recorte possa ficar em cima da imagem destino
    widget.lift()
    widget.startX = event.x
    widget.startY = event.y

def drag_movimento(event):
    global pos_final_x
    global pos_final_y
    widget = event.widget
    x = widget.winfo_x() - widget.startX + event.x
    y = widget.winfo_y() - widget.startY + event.y
    widget.place(x=x,y=y)
    pos_final_x  = x
    pos_final_y = y

def calcula_media(img, T, string, i):
    contador = 0
    sum_m = 0
    media = 0

    # Se estamos calculando m1, devemos pegar a média da intensidade dos pixels maiores que m1
    if(string == 'm1'):
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                if(img[y,x][i] > T[i]):
                    sum_m += img[y,x][i]
                    contador += 1
        
    # Se estamos calculando m2, devemos pegar a média da intensidade dos pixels menores ou iguais a m2
    else:
        for y in range(img.shape[0]):
            for x in range(img.shape[1]):
                if(img[y,x][i] <= T[i]):
                    sum_m += img[y,x][i]
                    contador += 1

    media = sum_m / contador
    
    return media

def determinacao_threshold(img):
    canto_superior_esquerdo = img[0, 0]
    canto_superior_direito = img[0, img.shape[1]-1]
    canto_inferior_esquerdo = img[img.shape[0]-1, 0]
    canto_inferior_direito = img[img.shape[0]-1, img.shape[1]-1]
    m1 = [0,0,0]
    m2 = [0,0,0]
    m2_sum = [0,0,0]
    threshold_atual = [0,0,0]
    threshold_prev = [0,0,0]
    contador = 0

    m1[0] = int(canto_superior_esquerdo[0]) + int(canto_superior_direito[0]) + int(canto_inferior_esquerdo[0]) + int(canto_inferior_direito[0])
    m1[1] = int(canto_superior_esquerdo[1]) + int(canto_superior_direito[1]) + int(canto_inferior_esquerdo[1]) + int(canto_inferior_direito[1])
    m1[2] = int(canto_superior_esquerdo[2]) + int(canto_superior_direito[2]) + int(canto_inferior_esquerdo[2]) + int(canto_inferior_direito[2])
    
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            m2_sum[0] += img[y,x][0]
            m2_sum[1] += img[y,x][1]
            m2_sum[2] += img[y,x][2]
            contador += 1
    
    m2[0] = (m2_sum[0] - m1[0]) / (contador - 4)
    m2[1] = (m2_sum[1] - m1[1]) / (contador - 4)
    m2[2] = (m2_sum[2] - m1[2]) / (contador - 4)

    m1[0] = m1[0] / 4
    m1[1] = m1[1] / 4
    m1[2] = m1[2] / 4

    threshold_prev[0] = 0
    threshold_prev[1] = 0
    threshold_prev[2] = 0

    threshold_atual[0] = (m1[0] + m2[0]) / 2
    threshold_atual[1] = (m1[1] + m2[1]) / 2
    threshold_atual[2] = (m1[2] + m2[2]) / 2

    while(threshold_atual[0] - threshold_prev[0] >= 0.01 and threshold_atual[1] - threshold_prev[1] >= 0.01 
          and threshold_atual[2] - threshold_prev[2] >= 0.01):
        
        for i in range(3):
            # m1 = média dos pixels maiores que threshold atual
            m1[i] = calcula_media(img, threshold_atual, 'm1', i)
            # m2 = média dos pixels menores ou iguais ao threshold atual
            m2[i] = calcula_media(img, threshold_atual, 'm2', i)

            threshold_prev[i] = threshold_atual[i]
            threshold_atual[i] = (m1[i] + m2[i]) / 2

    return [round(threshold_atual[0]), round(threshold_atual[1]), round(threshold_atual[2])]

def recortar_objeto(img):
    threshold = [0,0,0]
    threshold = determinacao_threshold(img)


    img_thresholded = np.zeros_like(img)
    
    for i in range(3):
        img_thresholded[:,:,i] = np.where(img[:,:,0] > threshold[0], 255, 0)
    

    mascara = cv2.cvtColor(img_thresholded, cv2.COLOR_RGB2GRAY)

    contours, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big_contour = max(contours, key=cv2.contourArea)
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [big_contour], 0, 255, -1)
    roi = cv2.bitwise_and(img, img, mask=mask)
    background = np.zeros_like(img)
    background[mask == 255] = roi[mask == 255]

    return background

def equalizar_tons(objeto, img_destino):
    contador = 0
    global diferenca
    sum_pixels_regiao_dest = [0, 0, 0]
    sum_pixels_regiao_obj = [0, 0, 0]
    media_pixels_dest = [0,0,0]
    media_pixels_objeto = [0,0,0]
    diferenca = [0,0,0]

    # Calcula a média dos pixels na região em que o objeto será colocado
    for y in range(objeto.shape[0]):
        for x in range(objeto.shape[1]):
            sum_pixels_regiao_dest += img_destino[y+pos_final_y,x+pos_final_x]
            contador += 1
    
    media_pixels_dest[0] = sum_pixels_regiao_dest[0] / contador
    media_pixels_dest[1] = sum_pixels_regiao_dest[1] / contador
    media_pixels_dest[2] = sum_pixels_regiao_dest[2] / contador 

    contador = 0
    
    # Calcula a média dos pixels na região do objeto (sem levar em conta os pixels pretos)
    for y in range(objeto.shape[0]):
        for x in range(objeto.shape[1]):
            pixel = objeto[y,x]
            if(pixel[0] != 0 and pixel[1] != 0 and pixel[2] != 2):
                sum_pixels_regiao_obj += objeto[y,x]
                contador += 1

    media_pixels_objeto[0] = sum_pixels_regiao_obj[0] / contador
    media_pixels_objeto[1] = sum_pixels_regiao_obj[1] / contador
    media_pixels_objeto[2] = sum_pixels_regiao_obj[2] / contador
    
    diferenca[0] = round(media_pixels_dest[0] - media_pixels_objeto[0])
    diferenca[1] = round(media_pixels_dest[1] - media_pixels_objeto[1])
    diferenca[2] = round(media_pixels_dest[2] - media_pixels_objeto[2])

    img_objeto = np.clip(objeto + diferenca, 0, 255).astype(np.uint8)
    cv2.imshow('Corte Equalizado Meu', img_objeto)

    return img_objeto

def ajustar_fronteira(img_orig, img_dest):
    altura_orig, largura_orig, _ = img_orig.shape
    for y in range(altura_orig):
         for x in range(largura_orig):
             pixel = img_orig[y,x]
             # Se o pixel é pixel de fundo, trocamos o valor do pixel da img_orig pelo valor do pixel de img_dest
             if((pixel[0]+diferenca[0] != diferenca[0] or pixel[0] != 0) or (pixel[1]+diferenca[1] != diferenca[1] or pixel[1] != 0) 
                or (pixel[2]+diferenca[2] != diferenca[2] or pixel[2] != 0)):
                 img_dest[y+pos_final_y,x+pos_final_x] = img_orig[y,x]

    cv2.imshow('Imagem Final', img_dest)

# Função main
arquivo = filedialog.askopenfilename(initialdir = "/", title = "Selecione o arquivo", filetypes = (("Arquivos JPG", "*.jpg"),
                                                                                                    ("Todos os arquivos", "*.*")))
imagem_cv = cv2.imread(arquivo)
cv2.namedWindow('Recorte a imagem de origem')
cv2.setMouseCallback('Recorte a imagem de origem', desenha_retangulo)

# variáveis para controle do mouse
cropping = False
drawing = False
ix, iy = -1, -1
fx, fy = -1, -1
imagem_tk_roi = None
acabou = False
pos_final_x = 0
pos_final_y = 0

while True:
    k = cv2.waitKey(1) & 0xFF
    i = imagem_cv.copy()

    if(cropping):
        cv2.rectangle(i, (x_start, y_start), (x_end, y_end), (255, 0, 0), 2)
        cv2.imshow('Recorte a imagem de origem', i)
        
    else:
        cv2.imshow('Recorte a imagem de origem', imagem_cv)

    # Se pressionar tecla 'q', sai do programa
    if k == ord('q'):  
        break

    # Se pressionar tecla 's', salva recorte
    elif k == ord('s'):  
        break

cv2.destroyAllWindows()

# Cria a janela principal
root = Tk()

# Define o título da janela
root.title("Trabalho Final FPI")

img_sem_fundo = recortar_objeto(roi)


imagem_pil = Image.fromarray(cv2.cvtColor(img_sem_fundo, cv2.COLOR_BGR2RGB))
# Cria uma imagem em branco com canal alfa
alpha = Image.new('L', imagem_pil.size, 255)  
# Define o canal alfa da imagem
imagem_pil.putalpha(alpha) 
imagem_tk_roi = ImageTk.PhotoImage(imagem_pil)

# Cria um label para exibir o recorte da primeira imagem
label_imagem1 = Label(root)
label_imagem1.pack(side=LEFT)

# Cria um label para exibir a segunda imagem
label_imagem2 = Label(root)
label_imagem2.pack(side=LEFT)

label_imagem1.bind("<Button-1>", drag_inicio)
label_imagem1.bind("<B1-Motion>", drag_movimento)

# Cria um botão para abrir recorte
botao_arquivo1 = Button(root, text = "Abrir recorte selecionado", command = lambda: abrir_recorte())
botao_arquivo1.pack(side=LEFT)

# Cria um botão para selecionar a segunda imagem
botao_arquivo2 = Button(root, text = "Selecionar imagem destino", command = lambda: abrir_arquivo())
botao_arquivo2.pack(side=LEFT)

botao_inicio_edicao = Button(root, text = "Iniciar melhoria de imagem", command = lambda: ajustar_fronteira(equalizar_tons(img_sem_fundo, imagem_destino_cv), imagem_destino_cv))
botao_inicio_edicao.pack(side=LEFT)

# Inicia o loop principal da interface gráfica
root.mainloop() 