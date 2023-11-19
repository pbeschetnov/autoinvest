#!/bin/bash

set -e

sudo sed -i "s|\${HOME}|${HOME}|g" autoinvest_telegram.service
sudo sed -i "s|\${USER}|$(whoami)|g" autoinvest_telegram.service
sudo cp autoinvest_telegram.service /etc/systemd/system/
sudo sed -i "s|\${HOME}|${HOME}|g" autoinvest_main.service
sudo sed -i "s|\${USER}|$(whoami)|g" autoinvest_main.service
sudo cp autoinvest_main.service /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl enable autoinvest_telegram.service
sudo systemctl restart autoinvest_telegram.service

sudo systemctl enable autoinvest_main.service
sudo systemctl restart autoinvest_main.service
