from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, Flask!"

@app.route('/hands')
def hands():
    hands_data = hands_back.grade().to_dict('records')
    return render_template('hands.html', hands_data=hands_data)

from flask import request, redirect

@app.route('/update', methods=['POST'])
def update():
    name = request.form['name']
    value = request.form['value']
    hands_back.update_hands(name, value)
    return redirect('/hands')

if __name__ == '__main__':
    app.run(debug=True)