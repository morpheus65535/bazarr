FROM debian:buster

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8

EXPOSE  6767

VOLUME /tv

RUN apt-get update && \
	apt-get install -y build-essential python-dev python-pip python-setuptools libjpeg-dev zlib1g-dev git libgit2-dev libffi-dev && \
	git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr && \
	git config --global user.name "Bazarr" && git config --global user.email "bazarr@fake.email" && \
	pip install -r /bazarr/requirements.txt

VOLUME /bazarr/data

CMD ["python", "/bazarr/bazarr.py"]