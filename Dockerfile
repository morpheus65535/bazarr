FROM debian:buster

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8

EXPOSE  6767

VOLUME /tv

RUN apt-get update && \
	apt-get install -y python-dev python-pip python-setuptools libjpeg-dev zlib1g-dev git libffi-dev && \
	pip install -r /bazarr/requirements.txt

VOLUME /bazarr/data

CMD ["python", "/bazarr/bazarr.py"]