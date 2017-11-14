FROM python:2

EXPOSE  6767

VOLUME /tv

# Update
RUN apt-get install build-base python-dev py2-pip py-setuptools jpeg-dev zlib-dev git libgit2-dev

# Get application source from Github
RUN git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr

VOLUME /bazarr/data

# Install app dependencies
RUN pip install -r /bazarr/requirements.txt

CMD ["python", "/bazarr/bazarr.py"]