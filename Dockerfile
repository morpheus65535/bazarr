FROM alpine:latest

EXPOSE  6767
VOLUME /bazarr

WORKDIR /bazarr

# Update
RUN apk add --update python py-pip

# Install app dependencies
RUN pip install -r requirements.txt

CMD ["python", "/bazarr/bazarr.py"]