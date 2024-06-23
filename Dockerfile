FROM python:3.13.0b2-slim-bookworm

LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name="Obsidian Daylio Parser"
LABEL org.label-schema.description="Convert .csv Daylio backup into markdown notes."
LABEL org.label-schema.url="https://github.com/DeutscheGabanna/Obsidian-Daylio-Parser/"

COPY src /app/src/
COPY _tests /app/_tests/

WORKDIR /app

RUN mkdir output

ENTRYPOINT [ "python", "src/main.py" ]
CMD [ "_tests/sheet-1-valid-data.csv", "output"]