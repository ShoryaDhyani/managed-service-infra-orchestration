FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install nvm and pre-cache common Node LTS versions at build time
# so runtime never needs to download anything
ENV NVM_DIR=/root/.nvm

RUN curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install 18 \
    && nvm install 20 \
    && nvm install lts/* \
    && nvm alias default lts/* \
    && nvm use default \
    && node -v && npm -v

WORKDIR /home/app

COPY script.sh main.sh
COPY main.py main.py
COPY requirements.txt requirements.txt

RUN chmod +x main.sh
RUN chmod +x main.py

RUN pip3 install -r requirements.txt --no-cache-dir

ENTRYPOINT ["/home/app/main.sh"]