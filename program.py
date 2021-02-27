import json
import boto3
import logging
import random
import uuid
import os
import utility

utility.configure_logger()


def lambda_handler(event, _context):
    bucket_name = os.environ.get('bucket_name', None)

    if not environment_configured(bucket_name):
        return {'statusCode': 500}

    body = json.loads(event.get('body', '{}'))
    draw_id = str(uuid.uuid4())
    tickets_to_return = max(body.get('tickets_to_return', 1), 1)

    logging.info(f'starting draw {draw_id} for {tickets_to_return} winners')

    entries = get_all_entries(bucket_name)

    if entries is None or len(entries) == 0:
        logging.error(f'no valid entries were found in {bucket_name}')
        return {'statusCode': 400}

    winners = get_tickets_for_entries(bucket_name, entries, tickets_to_return)

    if winners is None or len(winners) == 0:
        logging.error(f'failed to load any winning tickets from {bucket_name}')
        return {'statusCode': 400}

    if not write_draw_result(bucket_name, winners, draw_id):
        return {'statusCode': 400}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'x-powered-by': 'al.paca'
        },
        'body': {
            'draw_id': draw_id,
            'winners': make_tickets_safe_for_response(winners)
        }
    }


def write_draw_result(bucket_name: str, winners: list, draw_id: str):
    draw_filename = f'draw/{draw_id}.json'
    logging.info(f'writing draw information to s3://{bucket_name}/{draw_filename}')

    try:
        s3 = get_s3_client()
        s3.put_object(Body=(bytes(json.dumps(winners).encode('UTF-8'))), Bucket=bucket_name, Key=draw_filename)
    except Exception as e:
        logging.error(f'failed to write draw result {winners} to s3://{bucket_name}/{draw_filename} due to an exception: {str(e)}')
        return False

    return True


def get_all_entries(bucket_name: str):
    entries = []

    try:
        s3 = get_s3_client()
        all_entries = s3.list_objects_v2(Bucket=bucket_name, Prefix='entry/')
    except Exception as e:
        logging.error(f'an exception was encountered while reading entries: {str(e)}')
        return entries

    for entry in all_entries.get('Contents', []):
        entries.append(entry['Key'])

    random.shuffle(entries)

    logging.info(f'found a total of {len(entries)} entries')

    return entries


def get_tickets_for_entries(bucket_name: str, entries: list, tickets_to_return: int):
    winners = []

    for entry in entries:
        try:
            s3 = get_s3_client()
            file_object = s3.get_object(Bucket=bucket_name, Key=entry)
            file_data = file_object['Body'].read()
            ticket = json.loads(file_data.decode('utf-8'))
        except Exception as e:
            logging.error(f'rejected {entry} because an exception was encountered while loading it: {str(e)}')
            continue

        winner_ticket_id = ticket.get('ticket', None)
        if not winner_ticket_id or winner_ticket_id is None:
            logging.error(f'ticket {entry} rejected because it does not have a valid ticket number: {winner_ticket_id}')
            continue

        winner_name = ticket.get('name', None)
        if not winner_name or winner_name is None:
            logging.error(f'ticket {entry} rejected because it does not have a valid name: {winner_name}')
            continue

        winner_email = ticket.get('email', None)
        if not winner_email or winner_email is None:
            logging.error(f'ticket {entry} rejected because it does not have a valid email address: {winner_email}')
            continue

        winners.append(ticket)

        logging.info(f'ticket {entry} was successfully added to the draw in position {len(winners)}: {ticket}')

        if len(winners) >= tickets_to_return:
            break

    return winners


def make_tickets_safe_for_response(tickets: list):
    response = []

    for ticket in tickets:
        response.append({
            'ticket': ticket['ticket'],
            'name': ticket['name']
        })

    return response


def get_s3_client():
    return boto3.client('s3')


def environment_configured(bucket_name: str):
    if bucket_name is None or not bucket_name:
        logging.error(f'bucket_name is not set')
        return False

    aws_key = os.environ.get('aws_access_key_id', None)

    if aws_key is None or not aws_key:
        logging.error(f'aws_key is not set')
        return False

    aws_secret = os.environ.get('aws_secret_access_key', None)

    if aws_secret is None or not aws_secret:
        logging.error(f'aws_secret is not set')
        return False

    return True
