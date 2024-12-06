#!/bin/sh
echo "Starting ${SERVICE_NAME} service"
exec fastapi run app/services/${SERVICE_NAME}/${SERVICE_NAME}
