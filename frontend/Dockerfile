FROM tiangolo/uwsgi-nginx-flask:flask
RUN pip install flask-paginate
RUN pip install requests
RUN pip install netifaces
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY ./uwsgi-streaming.conf /etc/nginx/conf.d/
COPY ./app /app
