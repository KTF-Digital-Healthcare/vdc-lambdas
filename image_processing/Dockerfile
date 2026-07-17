FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt .
COPY test_images test_timages
RUN pip install -r requirements.txt

COPY main.py .

CMD ["main.lambda_handler"]