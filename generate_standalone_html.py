"""
Script para generar un HTML standalone con los datos JSON embebidos.
Esto permite que el HTML funcione sin necesidad de servidor web.
"""
import json
from pathlib import Path

def generate_standalone_html():
    """Genera un HTML con los datos JSON embebidos."""
    
    # Rutas
    json_path = Path("data/groq_simulation_results.json")
    template_path = Path("data/htmls/groq_interactive_report.html")
    output_path = Path("data/htmls/groq_report_standalone.html")
    
    # Leer JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Leer template HTML
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Convertir JSON a string escapado para JavaScript
    json_string = json.dumps(json_data, ensure_ascii=False)
    # Escapar comillas simples para que no rompan el string de JavaScript
    json_string = json_string.replace("'", "\\'")
    
    # Reemplazar el placeholder con los datos reales
    html_content = html_content.replace(
        "const embeddedData = JSON.parse('DATA_PLACEHOLDER');",
        f"const embeddedData = {json_string};"
    )
    
    # Guardar HTML standalone
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML standalone generado: {output_path}")
    print(f"   Ahora puedes abrir el archivo directamente en tu navegador sin necesidad de servidor.")
    
    return output_path

if __name__ == "__main__":
    generate_standalone_html()
