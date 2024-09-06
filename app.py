from flask import Flask, send_file, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
        <h1>C-SPAN5 Supercut</h1>
        <video width="600" controls>
            <source src="/supercut.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    ''')

@app.route('/supercut.mp4')
def supercut():
    return send_file('supercut.mp4')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
