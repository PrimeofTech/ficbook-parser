FROM tiangolo/meinheld-gunicorn-flask:python3.7

COPY . /app
WORKDIR /app

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y git google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

#RUN git clone https://github.com/PrimeofTech/ficbook-parser.git /app
#WORKDIR /app

# set display port to avoid crash
ENV DISPLAY=:99

ENV FLASK_APP=simple-ficbook-parser-python
ENV chromeinpath=True

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

#CMD ["python", "main.py"]
#CMD ["uwsgi", "--ini", "uwsgi.ini"]
