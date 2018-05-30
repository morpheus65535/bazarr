FROM lsiobase/alpine.python:3.7

# set python to use utf-8 rather than ascii.
ENV PYTHONIOENCODING="UTF-8"

VOLUME /tv
VOLUME /movies

RUN apk add --update git py-pip jpeg-dev && \
    apk add --update --virtual build-dependencies build-base python-dev libffi-dev zlib-dev  && \
    git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr && \
    pip install -r /bazarr/requirements.txt && \
    apk del --purge build-dependencies

VOLUME /bazarr/data

EXPOSE 6767

CMD ["python", "/bazarr/bazarr.py"]
