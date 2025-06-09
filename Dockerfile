FROM python:3.11.11-slim as image-build

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG WORKDIR=/backend
WORKDIR ${WORKDIR}
COPY ./backend/ .
COPY LICENSE.md .
COPY README.md .

RUN pip install --upgrade pip
RUN pip install -q --no-python-version-warning --disable-pip-version-check -r requirements.txt

RUN ./scripts/after-build.sh
RUN rm -rf scripts/after-build.sh

FROM python:3.11.11-slim

RUN apt-get update -qq && apt-get install -yqq curl && apt-get clean

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG USER=iset
ARG UID=1001
ARG GID=1002
ARG FILES_VERSION
ENV FILES_VERSION=${FILES_VERSION}

COPY --from=image-build /backend /iset
COPY --from=image-build /opt/venv /opt/venv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/iset/app/src"

ARG WORKDIR=/iset
WORKDIR ${WORKDIR}

RUN groupadd -g ${GID} ${USER} && \
useradd --no-create-home --no-log-init -u ${UID} -g ${GID} ${USER} && \
chown -R ${UID}:${GID} ${WORKDIR}
USER ${USER}

RUN ls -la
HEALTHCHECK --interval=60s --timeout=30s --start-period=15s --retries=1 CMD curl -f "${FILES_HEALTHCHECK_URL}"

# CMD [ "./scripts/run-main.sh" ]