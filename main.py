from website import create_app

app = create_app()

# This is not the main page you are looking for. If you want to modify this website, you'll likely find what you're looking for in auth.py :)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)