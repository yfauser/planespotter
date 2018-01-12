FROM tiangolo/uwsgi-nginx-flask:flask
RUN pip install Flask-Restless
RUN pip install PyMySQL
RUN pip install Flask-SQLAlchemy
RUN pip install requests
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY ./uwsgi-streaming.conf /etc/nginx/conf.d/
COPY ./app /app
