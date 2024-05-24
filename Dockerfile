# ---------------------------------------------
# Frontend
FROM node:20 as build-stage

WORKDIR /app
COPY ./frontend ./

RUN npm install && npm run build

# ---------------------------------------------
# Main
FROM debian:12-slim

RUN apt update && apt install 7zip ffmpeg python3-dev python3-pip python3-distutils unzip -y
# package unrar is missing

# Install
WORKDIR /app
COPY . ./

# Get rid of uncompiled fronted
RUN rm -rf ./frontend
COPY --from=build-stage /app/build /app/frontend/build

RUN python3 -m pip install -r requirements.txt --break-system-packages

EXPOSE 6767

ENTRYPOINT ["python3", "bazarr.py", "--no-update", "true", "--debug", "true", "--dev", "true"]