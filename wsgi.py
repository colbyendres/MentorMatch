# Put this in top-level directory so Procfile can find it

from mentormatch.app import start_app

if __name__ == '__main__':
	flask_app = start_app()
