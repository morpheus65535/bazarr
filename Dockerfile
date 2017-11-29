FROM lsiobase/alpine:3.6

VOLUME /tv

RUN apk add --no-cache git python2 python-dev py-pip py-pygit2 jpeg-dev && \
    apk add --no-cache --virtual build-dependencies g++ libffi-dev zlib-dev  && \
    git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /app && \
    pip install -r /app/requirements.txt && \
    apk del --purge build-dependencies

VOLUME /app/data

EXPOSE 6767

CMD ["python", "/app/bazarr.py"]