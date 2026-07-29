FROM python:3.12-slim

RUN pip install --no-cache-dir ansible

WORKDIR /ansible
COPY . .

ENTRYPOINT ["ansible-playbook"]