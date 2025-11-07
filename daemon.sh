cp gunicorn.service /etc/systemd/system/gunicorn.service
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn
systemctl status gunicorn
