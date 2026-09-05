FROM python:3.14-slim-trixie AS builder
RUN pip install --no-warn-script-location --user --no-cache-dir daphne==4.2.3
COPY pyproject.toml .
COPY requirements.txt .
COPY fortunes fortunes
RUN pip install --no-warn-script-location --user --no-cache-dir .

FROM python:3.14-slim-trixie
ARG FORTUNES_UID=1000
RUN adduser --gecos '' --disabled-password --uid ${FORTUNES_UID} fortunes
USER fortunes
ENV PATH="/usr/local/bin:/usr/bin:/bin:/home/fortunes/.local/bin"
ENV DJANGO_SETTINGS_MODULE="fortunes.settings"
COPY --from=builder --chown=fortunes /root/.local /home/fortunes/.local
# RUN mkdir -p /home/fortunes/.config/fortunes/
WORKDIR /home/fortunes/.config/fortunes/
COPY scripts/startup.sh /home/fortunes/.local/bin/startup.sh
ENTRYPOINT ["startup.sh"]
