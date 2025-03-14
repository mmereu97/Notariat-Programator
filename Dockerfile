FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Bucharest

# Instalăm pachetele necesare inclusiv tigervnc-common care conține vncpasswd
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    x11vnc xvfb \
    tigervnc-common \
    openbox \
    libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libglib2.0-0 \
    libgtk-3-0 \
    python3-pyqt5 \
    python3-requests \
    python3-bs4 \
    && rm -rf /var/lib/apt/lists/*

# Creăm directorul de lucru
WORKDIR /app

# Configurăm VNC
RUN mkdir -p ~/.vnc
RUN echo "password" | vncpasswd -f > ~/.vnc/passwd
RUN chmod 600 ~/.vnc/passwd

# Copiem codul aplicației
COPY . .

# Exposăm portul VNC
EXPOSE 5900

# Script de pornire
RUN echo '#!/bin/bash\nXvfb :1 -screen 0 1280x800x16 &\nexport DISPLAY=:1\nopenbox &\nx11vnc -forever -usepw -display :1 -geometry 1280x800 &\npython3 Programator.py\n' > /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]