# Image for running Google Drive file explorer app
FROM ubuntu

# Update the image with the latest packages
RUN apt update
RUN apt upgrade

# Set server timezone before tzdata package is installed below
RUN ln -snf /usr/share/zoneinfo/$CONTAINER_TIMEZONE /etc/localtime && echo $CONTAINER_TIMEZONE > /etc/timezone

# Install Python 3.9
RUN apt install -y python3.9 python3-pip libmagic1 python3-magic git vim
RUN ln -s /usr/bin/python3.9 /usr/bin/python

# Install Google API client libraries for Python
RUN pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib tabulate humanize python-magic

# Create the app code inside the container
RUN git clone https://github.com/80columns/gdrive-shell.git /root/gdshell

