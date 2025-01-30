# Importação das bibliotecas necessárias
import sqlite3
import logging
import time
import random
import argparse
from datetime import datetime
from multiprocessing import Manager, Process, Event, shared_memory
from threading import Thread
import numpy as np
import tomli

# Configuração de logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Última mudança: Adicionado sistema de memória compartilhada para comunicação entre processos
# A memória compartilhada armazena 3 valores float64:
# - data[0]: Quantidade de briquetes detectados
# - data[1]: Tamanho médio dos briquetes
# - data[2]: Porcentagem de briquetes considerados bons
# Isso permite que diferentes processos (detector, banco de dados e console) 
# compartilhem dados em tempo real de forma eficiente e thread-safe

# Configuração do parser de argumentos para definir intervalos de atualização
parser = argparse.ArgumentParser(description='Configurações do sistema de monitoramento de briquetes')
parser.add_argument('--update-interval', 
                   type=int,
                   default=3,
                   help='Intervalo de atualização em segundos')
parser.add_argument('--db-update-interval',
                   type=int, 
                   default=5,
                   help='Intervalo de atualização do banco de dados em segundos')

# Processa os argumentos da linha de comando
args = parser.parse_args()

# Define constantes globais
UPDATE_INTERVAL = args.update_interval
DATABASE_UPDATE_INTERVAL = args.db_update_interval
DATABASE_NAME = "briquetes.db"

# Classe para gerenciar conexões e operações com o banco SQLite
class SQLiteManager:
    def __init__(self, db_name):
        """
        Inicializa o gerenciador SQLite.
        
        Args:
            db_name (str): Nome do arquivo do banco de dados
        """
        self.db_name = db_name
        self.connection = None
        self._open_database()

    # Método para abrir conexão com o banco de dados
    def _open_database(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            logging.info(f"Conexão estabelecida com {self.db_name}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao abrir banco de dados: {e}")
            raise

    # Método para fechar conexão com o banco de dados
    def close(self):
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logging.info("Conexão com banco de dados fechada")
        except sqlite3.Error as e:
            logging.error(f"Erro ao fechar banco de dados: {e}")

    # Método para criar nova tabela no banco de dados
    def create_table(self, table_name):
        """
        Cria uma nova tabela se ela não existir.
        
        Args:
            table_name (str): Nome da tabela a ser criada
        """
        try:
            columns = {
                "Time": "TEXT",
                "Quantidade": "INTEGER",
                "TamanhoMedioDoBriquete": "REAL",
                "PorcentagemDeBriquetesBons": "REAL"
            }
            columns_def = ", ".join([f"{col} {col_type}" for col, col_type in columns.items()])
            query = f"CREATE TABLE IF NOT EXISTS '{table_name}' ({columns_def})"
            with self.connection:
                cursor = self.connection.cursor()
                cursor.execute(query)
                logging.info(f"Tabela {table_name} criada/verificada com sucesso")
        except sqlite3.Error as e:
            logging.error(f"Erro ao criar tabela {table_name}: {e}")
            raise

    # Método para inserir dados na tabela
    def insert_row(self, table_name, data):
        """
        Insere uma nova linha na tabela.
        
        Args:
            table_name (str): Nome da tabela
            data (dict): Dados a serem inseridos
        """
        try:
            with self.connection:
                cursor = self.connection.cursor()
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?"] * len(data))
                query = f"INSERT INTO '{table_name}' ({columns}) VALUES ({placeholders})"
                cursor.execute(query, tuple(data.values()))
                logging.debug(f"Dados inseridos na tabela {table_name}: {data}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao inserir dados na tabela {table_name}: {e}")
            raise

# Função para atualizar dados na memória compartilhada
def update_shared_memory(camera_id, stop_event):
    """Atualiza a memória compartilhada com dados do detector."""
    try:
        # Usa o mesmo nome de memória compartilhada que o detector
        shm = shared_memory.SharedMemory(name=f"det_{camera_id}")
        frame = np.ndarray((1080, 1920, 3), dtype=np.uint8, buffer=shm.buf)
        
        # Cria memória compartilhada para métricas
        metrics_shm = shared_memory.SharedMemory(name="detector_metrics", create=True, size=24)
        metrics_data = np.ndarray((3,), dtype=np.float64, buffer=metrics_shm.buf)
        metrics_data[:] = [0, 0, 0]  # Inicializa com zeros
        
        while not stop_event.is_set():
            try:
                # Processa o frame para extrair métricas
                # Aqui você deve implementar sua lógica de processamento
                # Por exemplo:
                quantidade = calcular_quantidade(frame)
                tamanho_medio = calcular_tamanho_medio(frame)
                porcentagem_bons = calcular_porcentagem_bons(frame)
                
                # Atualiza as métricas
                metrics_data[0] = quantidade
                metrics_data[1] = tamanho_medio
                metrics_data[2] = porcentagem_bons
                
                time.sleep(UPDATE_INTERVAL)
            except Exception as e:
                logging.error(f"Erro ao atualizar métricas: {e}")
                time.sleep(1)
    except Exception as e:
        logging.error(f"Erro ao acessar memória compartilhada: {e}")
    finally:
        shm.close()
        try:
            metrics_shm.close()
            metrics_shm.unlink()
        except:
            pass

# Worker para gerenciar operações do banco de dados
def database_worker(camera_id, stop_event, pause_event):
    db_name = "briquetes.db"
    db_manager = SQLiteManager(db_name)
    current_date = datetime.now().strftime("%Y_%m_%d")
    table_name = f"Briquetes_{current_date}"
    db_manager.create_table(table_name)

    try:
        metrics_shm = shared_memory.SharedMemory(name="detector_metrics")
        metrics_data = np.ndarray((3,), dtype=np.float64, buffer=metrics_shm.buf)
        
        while not stop_event.is_set():
            pause_event.wait()  # Aguarda enquanto está pausado
            new_date = datetime.now().strftime("%Y_%m_%d")
            if new_date != current_date:
                current_date = new_date
                table_name = f"Briquetes_{current_date}"
                db_manager.create_table(table_name)

            row_data = {
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Quantidade": int(metrics_data[0]),
                "TamanhoMedioDoBriquete": float(metrics_data[1]),
                "PorcentagemDeBriquetesBons": float(metrics_data[2])
            }
            db_manager.insert_row(table_name, row_data)
            time.sleep(DATABASE_UPDATE_INTERVAL)
    finally:
        metrics_shm.close()
        db_manager.close()

# Gerenciador da interface de console
def console_manager(shm_name, pause_event, stop_event):
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        # Aumentamos o array para 4 posições, onde a última indica se deve mostrar o console
        data = np.ndarray((4,), dtype=np.float64, buffer=shm.buf)
        
        # Espera até que o main sinalize para mostrar o console
        while not stop_event.is_set() and data[3] != 1:
            time.sleep(0.1)
            
        if not stop_event.is_set():
            print("Sistema iniciado automaticamente.")
            print("Status atual:")
            print(f"Quantidade: {int(data[0])}")
            print(f"Tamanho Médio do Briquete: {data[1]:.2f}")
            print(f"Porcentagem de Briquetes Bons: {data[2]:.2f}%")
            print("\nComandos disponíveis: status, pause, resume, stop, exit")
            
            while not stop_event.is_set():
                command = input("> ").strip().lower()
                if command == "status":
                    print("\nStatus atual:")
                    try:
                        print(f"Quantidade: {int(data[0])}")
                        print(f"Tamanho Médio do Briquete: {data[1]:.2f}")
                        print(f"Porcentagem de Briquetes Bons: {data[2]:.2f}%")
                    except Exception as e:
                        print(f"Erro inesperado ao ler dados: {e}")
                elif command == "pause":
                    pause_event.clear()
                    print("Processo pausado.")
                elif command == "resume":
                    pause_event.set()
                    print("Processo retomado.")
                elif command == "stop":
                    stop_event.set()
                    print("Processo encerrado.")
                elif command == "exit":
                    stop_event.set()
                    print("Saindo do programa.")
                else:
                    print("Comando inválido. Tente novamente.")
    finally:
        shm.close()

# Ponto de entrada principal do programa
if __name__ == "__main__":
    try:
        # Criar eventos de controle
        stop_event = Event()
        pause_event = Event()
        pause_event.set()  # Começa no estado "ativo" automaticamente

        # Carrega configuração para obter IDs das câmeras
        with open('config.toml', 'rb') as f:
            config = tomli.load(f)
        
        camera_ids = config['cameras'].keys()

        processes = []
        for camera_id in camera_ids:
            # Iniciar processo de atualização para cada câmera
            updater_process = Process(
                target=update_shared_memory, 
                args=(camera_id, stop_event)
            )
            updater_process.start()
            processes.append(updater_process)

            # Iniciar thread do banco de dados para cada câmera
            db_thread = Thread(
                target=database_worker, 
                args=(camera_id, stop_event, pause_event)
            )
            db_thread.start()
            processes.append(db_thread)

        # Iniciar gerenciador do console
        console_manager("detector_metrics", pause_event, stop_event)

    except Exception as e:
        logging.error(f"Erro crítico no programa principal: {e}")
    finally:
        # Limpeza e encerramento
        stop_event.set()
        for process in processes:
            if isinstance(process, Process):
                process.terminate()
            process.join()
        logging.info("Programa encerrado")
