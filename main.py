from website import create_app
from replit import web

app = create_app()

# This is not the main page you are looking for. If you want to modify this website, you'll likely find what you're looking for in auth.py :)
if __name__ == '__main__':
    #app.run(debug=True)
    
    web.run(app, debug=False)
    #app.run(host='127.0.0.1', port=5500)