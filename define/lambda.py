from xml.dom.minidom import parseString
import boto3
import requests

s3_client = boto3.client('s3')

try:
  slackToken = s3_client.get_object(Bucket='dm-slack-secrets', Key='slack_token')['Body'].read().strip()
  dictionaryAPIToken = s3_client.get_object(Bucket='dm-slack-secrets', Key='dictionary_api_token')['Body'].read().strip()

except Exception as e:
  fail('Unable to get secret tokens from s3. Exception: ' + str(e) + '.')

def handler(event, context):
  if slackToken != event['token']:
    fail('Invalid slack token provided.')

  # Slack encodes spaces with a '+', but the dictionary api is not a fan.
  encoded = event['text'].replace('+', '%20')

  r = requests.get('http://www.dictionaryapi.com/api/v1/references/collegiate/xml/' + encoded, params={'key': dictionaryAPIToken})

  dom = parseString(r.text.strip())

  try:
    entry_list = dom.firstChild

    if entry_list.tagName != 'entry_list':
      fail('Expected first child of XML DOM to be entry_list. Got ' + entryList.tagName + '.', dom)

    entry =  entry_list.firstChild
    while entry != None:
      if entry.nodeType == entry.ELEMENT_NODE and entry.tagName == 'entry' and entry.getAttribute('id'):
        return processEntry(entry)

      entry = entry.nextSibling

    fail('Unable to find search phrase in results from Dictionary API.', dom)

  except Exception as e:
    fail('Unexpected exception processing XML. Exception: ' + str(e) + '.', dom)

def fail(err_str, dom = None):
  if dom != None:
    print 'XML: ' + dom.toxml() + '.'

  raise Exception(err_str)

def processEntry(entry):
  dts = entry.getElementsByTagName('dt')
  definitions = [dtToString(dt) for dt in dts]
  return [{'color': '3C0857', 'text': definition} for definition in definitions]

def dtToString(dt):
  dt_str = ''

  for node in dt.childNodes:
    while node.nodeType != node.TEXT_NODE:
      node = node.firstChild

    dt_str += node.nodeValue

  return dt_str
