from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teachers_username = db.Column(db.String(80), nullable=False)
    classes_teacher = db.Column(db.String(80), nullable=False)
    teacher_files_checksum = db.Column(db.String(64), nullable=False)
    teacher_files_name = db.Column(db.String(120), nullable=False)
    teacher_files_path = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '沒有檔案'})

    file = request.files['file']
    teachers_username = request.form.get('teachers_username')
    classes_teacher = request.form.get('classes_teacher')

    if file.filename == '':
        return jsonify({'error': '沒有選擇檔案'})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Calculate checksum
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        # Save file info to database
        new_file = UploadedFile(
            teachers_username=teachers_username,
            classes_teacher=classes_teacher,
            teacher_files_checksum=checksum,
            teacher_files_name=filename,
            teacher_files_path=filepath
        )
        db.session.add(new_file)
        db.session.commit()

        return jsonify({'message': '檔案上傳成功', 'filename': filename})
    return jsonify({'error': '不允許的檔案類型'})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run()
