#!/bin/sh
echo "Starting service: ${SERVICE_NAME}"
exec fastapi run app/services/${SERVICE_NAME}/${SERVICE_NAME}
