FROM python:2.7.14-alpine3.6

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8

VOLUME /tv

RUN apk add --update git py-pip jpeg-dev && \
    apk add --update --virtual build-dependencies build-base python-dev libffi-dev zlib-dev  && \
    git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr && \
    pip install -r /bazarr/requirements.txt && \
    apk del --purge build-dependencies

VOLUME /bazarr/data

EXPOSE 6767

CMD ["python", "/bazarr/bazarr.py"]