import tomli
import argparse
import subprocess
import logging
import os
import sys
from datetime import datetime
import time
from pathlib import Path
from multiprocessing import shared_memory
import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
from threading import Thread, Event
import cv2
from utils.setup_routes import _setup_routes
import signal
import psutil
from BancodeDados import console_manager
class ImageSaver:
    def __init__(self, config_path: str):
        """
        Inicializa o sistema de salvamento de imagens.
        
        Args:
            config_path: Caminho para o arquivo de configuração TOML
        """
        self.config = self._load_config(config_path)
        self.frame_shape = self.config.get('frame_shape', (1080, 1920, 3))
        self.logger = self._setup_logger()
        self.camera_processes = {}
        self.detector_processes = {}
        self.shared_memories = {}
        self.shared_memories_det = {}
        self.app = FastAPI()
        self.stop_event = Event()
        
        # Configura rotas da API
        _setup_routes(self.app, self.config, self._generate_frames)

        # Configura handler para sinais de término
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _load_config(self, config_path: str) -> dict:
        """Carrega configurações do arquivo TOML."""
        with open(config_path, 'rb') as f:
            return tomli.load(f)
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o sistema de logging."""
        logger = logging.getLogger('main')
        logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        os.makedirs('logs', exist_ok=True)
        fh = logging.FileHandler('logs/main.log')
        fh.setLevel(logging.INFO)
        
        # Handler para console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def _kill_child_processes(self, parent_pid):
        """Mata todos os processos filhos recursivamente."""
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            psutil.wait_procs(children, timeout=5)
        except Exception as e:
            self.logger.error(f"Erro ao finalizar processos filhos: {str(e)}")

    def _signal_handler(self, signum, frame):
        """Handler para sinais de término."""
        self.logger.info(f"Sinal {signum} recebido. Iniciando limpeza...")
        self.stop_event.set()
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """Realiza limpeza dos recursos."""
        self.logger.info("Iniciando limpeza dos recursos...")
        
        # Finaliza processos das câmeras e detectores
        for camera_id, process in {**self.camera_processes, **self.detector_processes}.items():
            try:
                # Mata processo e seus filhos
                self._kill_child_processes(process.pid)
                process.terminate()
                process.wait(timeout=5)
                self.logger.info(f"Processo {camera_id} finalizado")
            except Exception as e:
                self.logger.error(f"Erro ao finalizar processo {camera_id}: {str(e)}")
        
        # Limpa memórias compartilhadas
        for shm in {**self.shared_memories, **self.shared_memories_det}.values():
            try:
                shm.close()
                shm.unlink()
            except Exception as e:
                self.logger.error(f"Erro ao limpar memória compartilhada: {str(e)}")
    
    def _generate_frames(self, camera_id: str):
        """Gerador de frames para streaming web."""
        while not self.stop_event.is_set():
            try:
                frame = self._get_frame(camera_id)
                frame_det = self._get_frame(f"det_{camera_id}")
                
                if frame is not None and frame_det is not None:
                    # Concatena frames lado a lado
                    combined_frame = np.hstack((frame, frame_det))
                    _, buffer = cv2.imencode('.jpg', combined_frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(1/self.config.get('web_refresh_rate', 1))
                
            except Exception as e:
                self.logger.error(f"Erro ao gerar frame para {camera_id}: {str(e)}")
                time.sleep(1)
    
    def _get_frame(self, camera_id: str) -> np.ndarray:
        """Obtém o frame mais recente da memória compartilhada."""
        try:
            shm = self.shared_memories.get(camera_id) or self.shared_memories_det.get(camera_id)
            if shm is None:
                return None

            frame = np.ndarray(
                self.frame_shape,
                dtype=np.uint8, 
                buffer=shm.buf
            )
            return frame.copy()
            
        except Exception as e:
            self.logger.error(f"Erro ao obter frame de {camera_id}: {str(e)}")
            return None
    
    def start_camera_processes(self):
        """Inicia os processos de aquisição de imagem e detecção para cada câmera."""
        for camera_id, camera_config in self.config['cameras'].items():
            try:
                # Limpa memórias compartilhadas existentes
                for name in [camera_id, f"det_{camera_id}"]:
                    try:
                        shm = shared_memory.SharedMemory(name=name)
                        shm.close()
                        shm.unlink()
                        self.logger.info(f"Memória compartilhada anterior removida: {name}")
                    except FileNotFoundError:
                        pass

                script_dir = Path(__file__).parent

                # Inicia processo de aquisição
                exe_path = str(script_dir / "camera_acquisition.py")
                if not Path(exe_path).exists():
                    raise FileNotFoundError(f"Executável não encontrado: {exe_path}")

                cmd_camera = [
                    sys.executable,
                    exe_path,
                    "--camera-url", str(camera_config['url']),
                    "--shared-memory", camera_id,
                    "--frame-rate", str(camera_config.get('frame_rate', 30)),
                    "--retry-interval", str(camera_config.get('retry_interval', 5)),
                    "--frame-shape",
                    str(self.frame_shape[0]),
                    str(self.frame_shape[1]),
                    str(self.frame_shape[2])
                ]

                # Inicia processo de detecção
                detector_path = str(script_dir / "models/detector_briquete.py")
                if not Path(detector_path).exists():
                    raise FileNotFoundError(f"Executável não encontrado: {detector_path}")

                cmd_detector = [
                    sys.executable,
                    detector_path,
                    "--camera-id", camera_id,
                    "--conf-briquete-model", str(camera_config.get('conf_briquete_model', 0.5)),
                    "--frame-rate", str(camera_config.get('frame_rate', 10))
                ]

                # Inicia os processos
                self.logger.info(f"Iniciando processos para câmera {camera_id}")
                self.camera_processes[camera_id] = subprocess.Popen(cmd_camera, cwd=str(script_dir))
                self.detector_processes[camera_id] = subprocess.Popen(cmd_detector, cwd=str(script_dir))

                # Aguarda criação das memórias compartilhadas
                max_retries = 10
                for i in range(max_retries):
                    time.sleep(2)
                    try:
                        if camera_id not in self.shared_memories:
                            self.shared_memories[camera_id] = shared_memory.SharedMemory(name=camera_id)
                        if f"det_{camera_id}" not in self.shared_memories_det:
                            self.shared_memories_det[f"det_{camera_id}"] = shared_memory.SharedMemory(name=f"det_{camera_id}")
                        if camera_id in self.shared_memories and f"det_{camera_id}" in self.shared_memories_det:
                            self.logger.info(f"Memórias compartilhadas conectadas para {camera_id}")
                            break
                    except FileNotFoundError:
                        if i == max_retries - 1:
                            self.logger.error(f"Timeout ao conectar às memórias compartilhadas para {camera_id}")

            except Exception as e:
                self.logger.error(f"Erro ao iniciar processos para {camera_id}: {str(e)}")
    
    def run(self):
        """Inicia o sistema completo."""
        try:
            # Inicia processos de câmera e detector
            self.start_camera_processes()
            
            # Inicia servidor web
            config = uvicorn.Config(
                self.app, 
                host="0.0.0.0", 
                port=8888, 
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # Executa o servidor em um thread separado
            server_thread = Thread(target=server.run)
            server_thread.start()
            
            # Aguarda o sinal de interrupção
            while not self.stop_event.is_set():
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            self.logger.info("Encerrando servidor web...")
            self.stop_event.set()
            
        finally:
            # Cleanup
            self.cleanup()
            if server_thread.is_alive():
                server.should_exit = True
                server_thread.join()

def main():
    parser = argparse.ArgumentParser(description='Sistema de Salvamento de Imagens')
    parser.add_argument('--config', default='config.toml', help='Caminho do arquivo de configuração TOML')
    
    args = parser.parse_args()
    
    saver = ImageSaver(args.config)
    saver.run()

if __name__ == "__main__":
    # Inicializa a memória compartilhada com 4 posições
    shm = shared_memory.SharedMemory(create=True, size=np.dtype(np.float64).itemsize * 4)
    data = np.ndarray((4,), dtype=np.float64, buffer=shm.buf)
    data[:] = [0, 0, 0, 0]  # Inicializa todos os valores com 0
    
    pause_event = Event()
    stop_event = Event()
    pause_event.set()  # Começa não pausado
    
    # Inicia o console manager em uma thread separada
    console_thread = Thread(target=console_manager, args=(shm.name, pause_event, stop_event))
    console_thread.start()
    
    # ... seu código de inicialização ...
    
    # Quando estiver pronto para mostrar o console, defina data[3] = 1
    data[3] = 1
    
    # ... resto do código ...

    # Quando terminar, limpe a memória compartilhada
    try:
        shm.close()
        shm.unlink()
    except:
        pass