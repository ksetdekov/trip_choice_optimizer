FROM python:3.8
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python" ]
CMD ["view.py" ]
