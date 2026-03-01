from flask import Flask, render_template, redirect, request

app = Flask(__name__)


@app.route('/')
def index():
    source = request.args.get('src', 'direct')
    return render_template('index.html', source=source)


@app.route('/click')
def log_click():
    src = request.args.get('src', 'unknown')
    # Log the click source here if needed
    print(f'Click logged from source: {src}')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
