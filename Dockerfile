FROM lsiobase/alpine.python

EXPOSE  6767

VOLUME /tv

# Update
RUN apk add --update build-base python-dev py2-pip py-setuptools jpeg-dev zlib-dev git

# Get application source from Github
RUN git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr

VOLUME /bazarr/data

# Install app dependencies
RUN pip install -r /bazarr/requirements.txt

CMD ["python", "/bazarr/bazarr.py"]