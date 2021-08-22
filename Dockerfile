FROM python:3.9-slim-buster as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/bpauser/.local/bin:$PATH
ENV FT_APP_ENV="docker"

# Prepare environment
RUN mkdir /binance-pump-alerts \
  && apt-get update \
  && apt-get -y install sudo \
  && apt-get clean \
  && useradd -u 1000 -G sudo -U -m bpauser \
  && chown bpauser:bpauser /binance-pump-alerts \
  # Allow sudoers
  && echo "bpauser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /binance-pump-alerts

# Install dependencies
FROM base as python-deps
RUN  apt-get update \
  && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc \
  && apt-get clean \
  && pip install --upgrade pip

# Install dependencies
COPY --chown=bpauser:bpauser requirements.txt /binance-pump-alerts/
USER bpauser
RUN  pip install --user --no-cache-dir -r requirements.txt

# Copy dependencies to runtime-image
FROM base as runtime-image

COPY --from=python-deps /usr/local/lib /usr/local/lib
ENV LD_LIBRARY_PATH /usr/local/lib

COPY --from=python-deps --chown=bpauser:bpauser /home/bpauser/.local /home/bpauser/.local

USER bpauser

COPY --chown=bpauser:bpauser . /binance-pump-alerts/

RUN chmod a+x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh", "python", "pumpAlerts.py"]
