#!/bin/sh
set -e

echo "🚀 Starting Promo-ML in PROD mode"



# НИКАКИХ chown в prod
# права на volume должны быть заданы при создании
#if [ -d /app/logs ]; then
#  chown -R app:app /app/logs
#fi

# гарантируем, что каталог существует
mkdir -p /app/logs

exec "$@"
