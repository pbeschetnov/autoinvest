#!/bin/bash

set -e

sudo apt update

# Python

sudo apt install git htop unzip build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev -y

rm -rf $HOME/.pyenv
curl https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install 3.11.4
pyenv local 3.11.4
pyenv global 3.11.4
pip install --upgrade pip
pip install -r ../requirements.txt

# Postgres

sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql.service

sudo -u postgres psql -c "CREATE USER autoinvest WITH ENCRYPTED PASSWORD '$(cat ../.secrets/pg_password | xargs)';"
sudo -u postgres psql -c "CREATE DATABASE autoinvest;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE autoinvest to autoinvest;"
sudo -u postgres psql -f ../schema/001_create_tables.sql
sudo -u postgres psql -d autoinvest -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO autoinvest;"

# Selenium

# https://googlechromelabs.github.io/chrome-for-testing/#stable

wget "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
sudo apt install ./google-chrome-stable_current_amd64.deb -y
rm google-chrome-stable_current_amd64.deb

wget "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$(google-chrome --version | grep -Eo '[0-9\.]+')/linux64/chromedriver-linux64.zip"
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64*

sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo sysctl vm.swappiness=10
sudo swapon --show
sudo cp /etc/fstab /etc/fstab.bak
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
