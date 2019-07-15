FROM python:3.6

RUN pip3 install news-please --upgrade

COPY docker.sh /
RUN chmod +x /docker.sh

CMD ["/docker.sh"]
