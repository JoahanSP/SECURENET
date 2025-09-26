#!/usr/bin/env python3
import sys
import requests
import os
import argparse
from config import Config

def send_image(server_url, image_path, api_key=None):
    """Envía una imagen al servidor"""
    if not os.path.exists(image_path):
        print(f"❌ Archivo no encontrado: {image_path}")
        return False
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            headers = {}
            
            if api_key:
                headers['X-API-Key'] = api_key
            
            response = requests.post(
                f"{server_url}/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            
            print(f"📤 Imagen enviada: {os.path.basename(image_path)}")
            print(f"📊 Status Code: {response.status_code}")
            
            try:
                json_response = response.json()
                print("📨 Respuesta del servidor:")
                print(f"   Status: {json_response.get('status', 'N/A')}")
                print(f"   Mensaje: {json_response.get('message', 'N/A')}")
                if 'name' in json_response:
                    print(f"   Nombre: {json_response.get('name')}")
            except:
                print(f"   Texto: {response.text}")
            
            return response.status_code == 200
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con el servidor: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Enviar imagen al servidor de seguridad')
    parser.add_argument('server_url', help='URL del servidor (ej: http://localhost:5000)')
    parser.add_argument('image_path', help='Ruta de la imagen a enviar')
    parser.add_argument('--api-key', help='API Key para autenticación', default=Config.API_KEYS["esp32_cam_1"])
    
    args = parser.parse_args()
    
    if len(sys.argv) < 3:
        parser.print_help()
        return
    
    success = send_image(args.server_url, args.image_path, args.api_key)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()