from fastapi.responses import HTMLResponse
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

def _setup_routes(app: FastAPI, config: dict, get_frames_callback):
    """
    Configura as rotas da API web.
    
    Args:
        app: Instância do FastAPI
        config: Configurações do sistema
        get_frames_callback: Função para gerar frames
    """
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        # Cria HTML com todas as câmeras
        cameras_html = ""
        cameras_links = ""
        
        # Links para câmeras individuais
        for camera_id, camera_config in config['cameras'].items():
            cameras_links += f"""
            <a href="/view/{camera_id}" class="camera-link">
                {camera_config.get('name', camera_id)}
            </a>
            """
        
        # Container das câmeras
        for camera_id, camera_config in config['cameras'].items():
            cameras_html += f"""
            <div class="camera-container">
                <h2>{camera_config.get('name', camera_id)}</h2>
                <img src="/camera/{camera_id}" alt="{camera_id}">
                <div class="camera-links">
                    <a href="/view/{camera_id}" class="button">Ver em Tela Cheia</a>
                    <a href="/camera/{camera_id}" class="button">Stream Direto</a>
                </div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Sistema de Câmeras</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    .header {{
                        background-color: #333;
                        color: white;
                        padding: 1rem;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .nav {{
                        background-color: #444;
                        padding: 10px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .camera-link {{
                        color: white;
                        text-decoration: none;
                        padding: 5px 10px;
                        margin: 0 5px;
                        border-radius: 3px;
                    }}
                    .camera-link:hover {{
                        background-color: #555;
                    }}
                    .camera-container {{
                        background-color: white;
                        margin-bottom: 20px;
                        padding: 15px;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .camera-links {{
                        margin-top: 10px;
                    }}
                    img {{
                        max-width: 640px;
                        width: 100%;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    h1 {{
                        margin: 0;
                    }}
                    h2 {{
                        color: #333;
                        margin-top: 0;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 8px 16px;
                        margin: 5px;
                        background-color: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-size: 14px;
                    }}
                    .button:hover {{
                        background-color: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Monitoramento de Câmeras</h1>
                </div>
                <div class="nav">
                    <a href="/" class="camera-link">Todas as Câmeras</a>
                    {cameras_links}
                </div>
                {cameras_html}
            </body>
        </html>
        """
        return html_content
    
    @app.get("/view/{camera_id}", response_class=HTMLResponse)
    async def view_camera(camera_id: str):
        camera_config = config['cameras'].get(camera_id, {})
        camera_name = camera_config.get('name', camera_id)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>{camera_name} - Sistema de Câmeras</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        background-color: #f5f5f5;
                    }}
                    .header {{
                        background-color: #333;
                        color: white;
                        padding: 1rem;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .nav {{
                        background-color: #444;
                        padding: 10px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .camera-link {{
                        color: white;
                        text-decoration: none;
                        padding: 5px 10px;
                        margin: 0 5px;
                        border-radius: 3px;
                    }}
                    .camera-link:hover {{
                        background-color: #555;
                    }}
                    .camera-container {{
                        background-color: white;
                        padding: 15px;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    img {{
                        max-width: 100%;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 5px;
                    }}
                    h1 {{
                        margin: 0;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 8px 16px;
                        margin: 5px;
                        background-color: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-size: 14px;
                    }}
                    .button:hover {{
                        background-color: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{camera_name}</h1>
                </div>
                <div class="nav">
                    <a href="/" class="camera-link">Todas as Câmeras</a>
                    <a href="/camera/{camera_id}" class="camera-link">Stream Direto</a>
                </div>
                <div class="camera-container">
                    <img src="/camera/{camera_id}" alt="{camera_name}">
                </div>
            </body>
        </html>
        """
        return html_content
    
    @app.get("/camera/{camera_id}")
    async def get_camera_frame(camera_id: str):
        return StreamingResponse(
            get_frames_callback(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )