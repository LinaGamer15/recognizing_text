from flask import Flask, render_template, redirect, url_for, send_file, abort
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename
from PIL import Image
import glob
import cv2
import pytesseract
import os
# create file ignore_file.py
from ignored_file import SECRET_KEY, path_to_tesseract

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


class ImageUpload(FlaskForm):
    image = FileField('PNG or JPG file',
                      validators=[FileAllowed(['png', 'jpg'], 'Only png and jpg!'), FileRequired('File is empty!')])
    submit = SubmitField('Upload')


def scale_image(input_image, output_image, width=None, height=None):
    original_image = Image.open(input_image)
    w, h = original_image.size
    if width and height:
        max_size = (width, height)
    elif width:
        max_size = (width, h)
    elif height:
        max_size = (w, height)
    else:
        raise RuntimeError('Width or height required!')
    original_image.thumbnail(max_size, Image.ANTIALIAS)
    original_image.save('static/images/' + output_image)


@app.route('/', methods=['GET', 'POST'])
def home():
    files = glob.glob('static/images/\\*')
    for f in files:
        os.remove(f)
    form = ImageUpload()
    if form.validate_on_submit():
        filename = secure_filename(form.image.data.filename)
        form.image.data.save('static/images/' + filename)
        if os.path.isfile('static/images/' + filename):
            return redirect(url_for('rec_text', path=filename))
    return render_template('index.html', form=form)


@app.route('/<path>')
def rec_text(path):
    extension = path.split('.')[-1]
    pytesseract.pytesseract.tesseract_cmd = path_to_tesseract
    img = cv2.imread('static/images/' + path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(img, config=config, lang='rus')
    i = text.find('\n')
    new_text = text[:i] + '\n\n' + text[i + 1:]
    text_l = new_text.split()
    texts = new_text.strip().split('\n\n')
    text_to_file = new_text.strip().replace('\n\n', ';').replace('\n', '').replace(';', ';\n')
    name_file = ''
    for i1 in range(len(text_l)):
        if text_l[i1] == 'Уровень':
            for i2 in range(0, i1):
                if i2 == i1 - 1:
                    name_file += f'{text_l[i2]}'
                else:
                    name_file += f'{text_l[i2]}_'
            file = open(f'files/{name_file}.txt', 'w+', encoding='utf-8')
            file.write(text_to_file)
            break
    rescale_image = scale_image('static/images/' + path, f'photo.{extension}', 700)
    if os.path.isfile(f'files/{name_file}.txt'):
        return render_template('rec_text.html', texts=texts, path=f'photo.{extension}', filename=name_file)


@app.route('/send-file/<filename>', methods=['GET', 'POST'])
def send(filename):
    try:
        return send_file(f'files\\{filename}.txt', mimetype='txt', attachment_filename=f'{filename}.txt',
                         as_attachment=True)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run(debug=True)
