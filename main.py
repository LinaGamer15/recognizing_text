from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename
from PIL import Image
import glob
import cv2
import pytesseract
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


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
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    img = cv2.imread('static/images/' + path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(img, config=config, lang='rus')
    texts = text.strip().split('\n\n')
    rescale_image = scale_image('static/images/' + path, f'photo.{extension}', 700)
    return render_template('rec_text.html', texts=texts, path=f'photo.{extension}')


if __name__ == '__main__':
    app.run(debug=True)
