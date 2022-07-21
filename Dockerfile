FROM python:3.7
COPY src/ /app
COPY entrypoint.sh /app
COPY requirements.txt /app
WORKDIR /app
RUN apt-get update
# RUN apt-get install pkg-config libsecp256k1-dev libzmq3-dev docker-compose -y
RUN pip3 install --upgrade setuptools pip pipenv
RUN pip3 install --upgrade -r requirements.txt
RUN chmod +x /app/entrypoint.sh
EXPOSE 8089
CMD ["./entrypoint.sh"]
