FROM python:3.10-slim

RUN apt-get update
RUN apt-get install curl -y
RUN apt-get install git -y
RUN curl -sL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get upgrade -y
RUN apt-get install -y nodejs


WORKDIR /home/app

COPY script.sh main.sh
COPY main.py main.py
COPY requirements.txt  requirements.txt

RUN chmod +x main.sh
RUN chmod +x main.py

RUN pip3 install -r requirements.txt --no-cache-dir

ENTRYPOINT ["/home/app/main.sh"]
