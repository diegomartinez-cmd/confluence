from flask import Flask, request, send_file, render_template_string
import requests
import re
from io import BytesIO
import os

app = Flask(__name__)

BASE_URL = "https://brmtatlconfluence.banregio.com:8443"
API_TOKEN = os.getenv("API_TOKEN")  # Lee desde variable de entorno

HTML_FORM = """
<!doctype html>
<html>
  <head><title>Descargar PDF Confluence</title></head>
  <body>
    <h2>Descargar PDF desde Confluence</h2>
    <form method="POST">
      <input type="text" name="confluence_url" placeholder="Pega aquí la URL de Confluence" style="width: 400px;" required>
      <button type="submit">Descargar PDF</button>
    </form>
  </body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('confluence_url')
        match = re.search(r'pageId=(\d+)', url)
        if not match:
            return "❌ URL inválida: no se encontró el pageId", 400

        page_id = match.group(1)

        headers = {
            "X-Atlassian-Token": "no-check",
            "Authorization": f"Bearer {API_TOKEN}"  # Aquí está la clave
        }
        print(f"API_TOKEN = '{API_TOKEN}'")


        export_url = f"{BASE_URL}/spaces/flyingpdf/pdfpageexport.action?pageId={page_id}"
        response = requests.get(export_url, headers=headers, allow_redirects=False)

        if response.status_code != 302:
            return f"""
            ❌ No se obtuvo redirección 302<br>
            Código: {response.status_code}<br>
            Headers: {dict(response.headers)}<br>
            Body: {response.text}
            """, 500

        pdf_path = response.headers.get("location")
        if not pdf_path:
            return f"❌ No se encontró el header `location`. Headers: {dict(response.headers)}", 500

        pdf_url = f"{BASE_URL}{pdf_path}"
        pdf_response = requests.get(pdf_url, headers=headers)

        if pdf_response.status_code != 200:
            return f"❌ Error al descargar el PDF (código {pdf_response.status_code})", 500

        return send_file(
            BytesIO(pdf_response.content),
            download_name=f"pagina-{page_id}.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )

    return render_template_string(HTML_FORM)

if __name__ == '__main__':
    app.run(debug=True)
