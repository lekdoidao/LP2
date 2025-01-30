# Classificador de Briquetes usando Visão Computacional

## Sobre o Projeto
Sistema automatizado para classificação de briquetes utilizando visão computacional, desenvolvido para otimizar o processo de controle de qualidade na planta de briquetagem da Vale. O sistema visa avaliar características como granulometria, tamanho, uniformidade e qualidade dos briquetes através de processamento de imagens.

## Contexto
Os briquetes são produtos aglomerados que precisam atender a requisitos específicos de qualidade, incluindo:
- Granulometria adequada das matérias-primas
- Tamanho uniforme das partículas
- Boa resistência à compressão
- Alta resistência ao transporte e manuseio
- Baixa degradação e inchamento

## Objetivos
### Geral
Desenvolver um sistema de visão computacional capaz de classificar automaticamente a qualidade dos briquetes durante o processo de produção.

### Específicos
- Implementar sistema de captura de imagens na linha de produção
- Desenvolver algoritmo de classificação baseado em visão computacional
- Validar o sistema em ambiente laboratorial
- Implementar o sistema em ambiente industrial

## Cronograma
O projeto está estruturado em 12 meses, divididos nas seguintes fases:

1. **Fase Inicial (Meses 1-2)**
   - Revisão bibliográfica
   - Estudo do funcionamento da Planta de Briquetes
   - Definição da metodologia

2. **Fase de Desenvolvimento (Meses 3-6)**
   - Coleta de imagens
   - Ajustes e calibração da câmera
   - Treinamento do algoritmo

3. **Fase de Implementação (Meses 7-10)**
   - Validação do algoritmo
   - Testes em laboratório
   - Implementação em ambiente industrial

4. **Fase Final (Meses 11-12)**
   - Ajustes finais
   - Documentação
   - Relatórios e publicações

## Tecnologias
- Sistemas de visão computacional
- Algoritmos de machine learning
- Sistemas de captura de imagem industrial
- Processamento de imagens em tempo real

## Impactos e Benefícios
- **Segurança**: Moderado impacto positivo na segurança do trabalho
- **Operacional**: Redução da necessidade de inspeção manual
- **Qualidade**: Maior consistência na avaliação dos briquetes
- **Produtividade**: Otimização do processo de controle de qualidade

## Documentação
- `/docs`: Documentação técnica
- `/reports`: Relatórios de progresso
- `/papers`: Artigos e publicações

## Como Contribuir
1. Clone o repositório
2. Crie uma branch para sua feature
3. Faça commit das alterações
4. Push para a branch
5. Abra um Pull Request

## Status do Projeto
Em desenvolvimento - Versão 1.0

## Parceiros
- Vale
- IFES

## Organização proposta de arquivos
.
├── README.md
├── docs/
│   ├── technical/
│   │   ├── architecture.md
│   │   ├── api_reference.md
│   │   └── setup_guide.md
│   └── user/
│       ├── manual.md
│       └── troubleshooting.md
├── src/
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   ├── models/
│   │   ├── trained/
│   │   └── configs/
│   ├── preprocessing/
│   │   └── image_processing.py
│   └── utils/
│       └── helpers.py
├── tests/
│   ├── unit/
│   └── integration/
├── notebooks/
│   └── exploratory/
├── reports/
│   ├── figures/
│   └── database/
├── papers/
│   ├── published/
│   └── drafts/
├── requirements.txt
└── .gitignore

## Sistema de Aquisição e Salvamento de Imagens

### Módulo de Aquisição (`camera_acquisition.py`)
Sistema responsável pela captura de frames de câmeras individuais e disponibilização em memória compartilhada.

#### Características Principais
- Suporte múltiplos tipos de câmeras (IP, RTSP, WebCam)
- Execução independente por câmera
- Compartilhamento de frames via memória compartilhada
- Sistema robusto de logging e tratamento de erros
- Configurável via argumentos de linha de comando

#### Exemplo de uso do módulo
python camera_acquisition.py \
--camera-url STRING # URL/Path da câmera (rtsp://, http://, /dev/video0)
--shared-memory STRING # Nome do espaço de memória compartilhada
--log-level STRING # Nível de logging (DEBUG, INFO, WARNING, ERROR)
--retry-interval INT # Intervalo de reconexão em caso de falha (segundos)
--frame-rate INT # Taxa de captura desejada (fps)

### Sistema de Salvamento (`save_images.py`)
Aplicação principal que gerencia múltiplas instâncias do módulo de aquisição e disponibiliza interface web para visualização.

#### Características Principais
- Gerenciamento de múltiplas câmeras via subprocessos
- Interface web em tempo real (0.0.0.0:8888)
- Salvamento configurável de frames em disco
- Configuração via arquivo TOML
- Visualização em tempo real com taxa configurável

#### Exemplo de Configuração (config.toml):
```toml
output_directory = "/data/images"
web_refresh_rate = 1  # fps para visualização web

[cameras]
    [cameras.cam1]
    url = "rtsp://camera1.local:554/stream"
    name = "Câmera 1"
    save_interval = 1  # segundos entre saves
    frame_rate = 30
    retry_interval = 5

    [cameras.cam2]
    url = "http://192.168.1.100/video"
    name = "Câmera 2"
    save_interval = 2
    frame_rate = 15
    retry_interval = 5
```

#### Execução
python save_images.py --config config.toml

### Estrutura de Diretórios do Dataset
saved_images/
├── camera1/
│ ├── YYYY-MM-DD/
│ │ ├── HH-MM-SS.jpg
│ │ └── ...
│ └── ...
├── camera2/
│ └── ...
└── logs/
├── camera_acquisition_[camera_id].log
└── save_images.log

### Requisitos do Sistema
- Python 3.8+
- OpenCV
- FastAPI (interface web)
- SharedMemory (Python multiprocessing)
- Logging
- ConfigArgParse

### Tratamento de Erros
- Reconexão automática em caso de falha de câmera
- Buffer circular para memória compartilhada
- Logging detalhado de eventos e erros
- Monitoramento de uso de recursos

### Interface Web
- Visualização em tempo real de todas as câmeras
- Status de conexão e FPS atual
- Últimos frames salvos
- Logs do sistema