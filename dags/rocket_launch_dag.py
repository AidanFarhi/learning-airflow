import json
import pathlib
import datetime
import requests
import requests.exceptions as requests_exceptions
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

dag = DAG(
    dag_id='download_rocket_launches',
    start_date=datetime.datetime(2022, 12, 1),
    schedule_interval=None,
    catchup=False
)

download_launches = BashOperator(
    task_id='download_launches',
    bash_command="curl -o /tmp/launches.json -L 'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",
    dag=dag
)

def get_pictures_callable():
    pathlib.Path('/tmp/images').mkdir(parents=True, exist_ok=True)
    with open('/tmp/launches.json') as f:
       launches = json.load(f)
       image_urls = [launch['image'] for launch in launches['results']]
       for image_url in image_urls:
           try:
               response = requests.get(image_url)
               image_filename = image_url.split('/')[-1]
               target_file = f'/tmp/images/{image_filename}'
               with open(target_file, 'wb') as f:
                   f.write(response.content)
               print(f'Downloaded {image_url} to {target_file}')
           except requests_exceptions.MissingSchema:
               print(f'{image_url} appears to be an invalid URL.')
           except requests_exceptions.ConnectionError:
               print(f'Could not connect to {image_url}.')

get_pictures = PythonOperator(
    task_id='get_pictures',
    python_callable=get_pictures_callable,
    dag=dag
)

notify = BashOperator(
    task_id='notify',
    bash_command='echo "There are now $(ls /tmp/images/ | wc -l) images."',
    dag=dag
)

download_launches >> get_pictures >> notify
