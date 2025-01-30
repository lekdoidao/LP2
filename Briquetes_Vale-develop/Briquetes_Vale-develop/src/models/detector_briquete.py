import time
from datetime import datetime
import gc
from ultralytics import YOLO
from collections import deque
import logging
from multiprocessing import shared_memory
import numpy as np
import argparse

def _setup_logger(name):
    """Configura o sistema de logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Handler para arquivo
    fh = logging.FileHandler(f'logs/{name}.log')
    fh.setLevel(logging.INFO)

    # Handler para console 
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formato do log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def modelo_briquete(camera_id, conf_briquete_model, frame_rate):
    gc.enable()

    # Configuração do logger
    logger = _setup_logger('detector_briquete')

    model = YOLO("models/best.pt", task='detect')
    frame_shape = (1080, 1920, 3)

    # Cria memória compartilhada para o frame processado
    shm_name = f"det_{camera_id}"
    frame_size = int(np.prod(frame_shape) * np.dtype(np.uint8).itemsize)  # Convertido para int

    try:
        # Tenta remover memória compartilhada existente
        existing_shm = shared_memory.SharedMemory(name=shm_name)
        existing_shm.close()
        existing_shm.unlink()
    except FileNotFoundError:
        pass

    # Cria nova memória compartilhada
    shm_det = shared_memory.SharedMemory(name=shm_name, create=True, size=frame_size)
    logger.info(f"Memória compartilhada criada: {shm_name}")

    try:
        while True:
            try:
                # Conecta à memória compartilhada original
                try:
                    shm = shared_memory.SharedMemory(name=camera_id)
                    frame = np.ndarray(frame_shape, dtype=np.uint8, buffer=shm.buf)
                    frame = frame.copy()  # Faz uma cópia para evitar problemas de concorrência
                except Exception as e:
                    logger.error(f"Erro ao acessar memória compartilhada original: {str(e)}")
                    time.sleep(10)  # Aguarda 10 segundos antes de tentar novamente
                    continue

                height, width = frame.shape[:2]
                logger.info('Executando modelo neural!')
                results = model(frame, max_det=1000, save=False, show_labels=True, show_conf=False, show_boxes=True, conf = conf_briquete_model, imgsz=736, iou=0.2, agnostic_nms=True)[0]  # results list
                image_det = results.plot(boxes=True, labels=True, probs=False, masks=False)

                if len(results) == 0:
                    #nenhum briquete detectado
                    logger.info('Nenhum briquete detectado')
                else:
                    area = []
                    xyxy = results.boxes.xyxy.cpu().numpy()
                    # Verifica se há máscaras antes de acessar
                    if hasattr(results, 'masks') and results.masks is not None:
                        mascaras = results.masks.data.cpu().numpy()
                    else:
                        mascaras = None
                    classes = results.boxes.cls.cpu().numpy()

                    # Só processa máscaras se elas existirem
                    if mascaras is not None:
                        for i in range(mascaras.shape[0]):
                            #maskResize = cv2.resize(mascaras[i], (width, height), interpolation=cv2.INTER_NEAREST)
                            #area_mask = np.count_nonzero(maskResize)
                            largura = int(round(xyxy[i, 2] - xyxy[i, 0], 0))
                            altura = int(round(xyxy[i, 3] - xyxy[i, 1], 0))

                # Compartilha o frame processado via memória compartilhada
                try:
                    # Copia o frame processado para a memória compartilhada
                    shm_array = np.ndarray(image_det.shape, dtype=image_det.dtype, buffer=shm_det.buf)
                    np.copyto(shm_array, image_det)
                    
                except Exception as e:
                    logger.error(f"Erro ao compartilhar frame processado via memória compartilhada: {str(e)}")

                # Fecha a memória compartilhada original
                shm.close()

            except Exception as e:
                logger.error(f"Erro no processamento do modelo neural: {str(e)}")
                time.sleep(0.05)
            time.sleep(1/frame_rate)

    except KeyboardInterrupt:
        logger.info("Encerrando processamento do modelo briquete...")
        shm_det.close()
        try:
            shm_det.unlink()
        except FileNotFoundError:
            pass

def main():
    parser = argparse.ArgumentParser(description='Detector de Briquetes')
    parser.add_argument('--camera-id', required=True, help='ID da câmera para processamento')
    parser.add_argument('--conf-briquete-model', type=float, default=0.5, help='Confiança mínima para detecção de briquetes')
    parser.add_argument('--frame-rate', type=int, default=10, help='Taxa de captura desejada')
    args = parser.parse_args()

    modelo_briquete(args.camera_id, args.conf_briquete_model, args.frame_rate)

if __name__ == "__main__":
    main()