import os
import zipfile
import shutil
from flask import Flask, request, send_from_directory, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from converter import convert_multiple_heic_files

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ZIP_PATH = 'converted.zip'
ALLOWED_EXTENSIONS = {'heic'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_converted_folder_and_zip(folder):
    # Svuota la cartella converted
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    # Cancella converted.zip se esiste
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            return 'No file part', 400

        files = request.files.getlist('files[]')
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filepath)

        # Svuota la cartella converted e cancella lo zip PRIMA della nuova conversione
        clear_converted_folder_and_zip(CONVERTED_FOLDER)

        # Convert files
        convert_multiple_heic_files(
            uploaded_files,
            overwrite=True,
            remove=False,
            quality=95,
            target=CONVERTED_FOLDER,
            progress_callback=None,
            generate_unique=True,
            verbose=True
        )

        # Create ZIP file of all converted JPGs
        with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
            for filename in os.listdir(CONVERTED_FOLDER):
                file_path = os.path.join(CONVERTED_FOLDER, filename)
                zipf.write(file_path, arcname=filename)
            

        return redirect(url_for('download_page'))
    return render_template('index.html')

@app.route('/downloads')
def download_page():
    files = os.listdir(CONVERTED_FOLDER)
    return render_template('downloads.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=True)

@app.route('/download_all')
def download_all():
    clear_converted_folder_and_zip(UPLOAD_FOLDER)
    
    return send_file(ZIP_PATH, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
