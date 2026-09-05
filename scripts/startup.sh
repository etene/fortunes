#!/bin/sh

FORTUNES_DATA_PATH="${HOME}/.config/fortunes"

if [ ! -d "${FORTUNES_DATA_PATH}" ]; then
    mkdir -p "${FORTUNES_DATA_PATH}"
fi

django-admin migrate

cd ${FORTUNES_DATA_PATH}

exec daphne --bind 0.0.0.0 fortunes.asgi:application
