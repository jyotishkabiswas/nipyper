def main():
    from nipyper.app import app, celery, socketio, port
    socketio.run(app, port = port)

if __name__ == '__main__':
    main()
