import asyncio
import json
from fastapi import Request
import aio_pika
import boto3
from logger import *

from projects.model import ProjectRequest
from config import config

from projects.service import update_project_status

ecs_client = boto3.client(
    'ecs',
    region_name='ap-south-1',
    aws_access_key_id=config.S3_ACCESS_KEY,
    aws_secret_access_key=config.S3_SECRET_KEY
)

container_config = {
    'CLUSTER': config.CLUSTER,
    'TASK': config.TASK
}


async def run_build_container(body: dict):
    try:
        ecs_client.run_task(
            cluster=container_config['CLUSTER'],
            taskDefinition=container_config['TASK'],
            launchType='FARGATE',
            count=1,
            networkConfiguration={
                'awsvpcConfiguration': {
                    'assignPublicIp': 'ENABLED',
                    'subnets': ['subnet-0d9261d1bac8665af', 'subnet-03eb8bca8687f02d8', 'subnet-0afe74c57cdd4e235'],
                    'securityGroups': ['sg-0d8483897cb94cd43']
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': 'builder-image',
                        'environment': [
                            {'name': 'GIT_URL', 'value': body['gitURL']},
                            {'name': 'PROJECT_ID', 'value': body['projectSlug']},
                            {'name': 'PROJECT_TYPE', 'value': body['projectType']}
                        ]
                    }
                ]
            }
        )

    
    except Exception as e:
        publish_error(f'Error running ECS task: {e}')
        return None

    return True

async def run_local_build(body: dict):
    try:
        import os
        os.system(f"docker run -d --name {body['projectSlug']} --add-host=host.docker.internal:host-gateway --env-file ../buildServer/.env -e GIT_URL={body['gitURL']} -e PROJECT_ID={body['projectSlug']} -e PROJECT_TYPE={body['projectType']} build:latest")
    except Exception as e:
        publish_error(f"Error occurred while running Docker container: {e}")
        return None

    return True


async def process(message: aio_pika.IncomingMessage):

    async with message.process():

        job = json.loads(message.body)

        try:
            publish_log(f"Received job: {job}")

            deployment_id = job["projectSlug"]

            publish_log(f"Building {deployment_id}")

            # Simulate build process
            if config.LOCAL == 'true':
                await run_local_build(job)
            else:  # Simulate build time
                await run_build_container(job)

            publish_log("Done")
        except Exception as e:
            publish_error(f"Error processing job: {e}")
        publish_log(f"Received job: {job}")

        deployment_id = job["projectSlug"]

        publish_log(f"Building {deployment_id}")


        update_project_status(deployment_id, "live")

        publish_log("Done")


async def main():

    connection = await aio_pika.connect_robust(
        config.rabbitmq_url
    )

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(
        "build.queue",
        durable=True
    )

    await queue.consume(process)

    publish_log("Worker started")

    await asyncio.Future()

async def close_worker():
    publish_log("Closing worker...")
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    asyncio.run(main())