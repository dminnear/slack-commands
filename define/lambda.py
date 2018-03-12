from xml.dom.minidom import parseString
import requests
import os
import json

# Set tokens from env vars
try:
  slackToken = os.environ['SLACK_TOKEN']
  dictionaryAPIToken = os.environ['DICTIONARY_API_TOKEN']

except Exception as e:
  fail('Environment not properly configured. Expected SLACK_TOKEN and DICTIONARY_API_TOKEN environment variables.')

def handler(event, context):
  if slackToken != event['token']:
    fail('Invalid slack token provided.')

  responseUrl = event['response_url']

  # Slack encodes spaces with a '+', but the dictionary api is not a fan.
  encoded = event['text'].replace('+', '%20')

  r = requests.get('http://www.dictionaryapi.com/api/v1/references/collegiate/xml/' + encoded, params={'key': dictionaryAPIToken})

  if r.status_code != 200:
    fail("Request to dictionary api failed.")

  dom = parseString(r.text.strip())

  try:
    entry_list = dom.firstChild

    if entry_list.tagName != 'entry_list':
      fail('Expected first child of XML DOM to be entry_list. Got ' + entryList.tagName + '.', dom)

    entry =  entry_list.firstChild
    while entry != None:
      if entry.nodeType == entry.ELEMENT_NODE and entry.tagName == 'entry' and entry.getAttribute('id'):
        responseBody = processEntry(entry)
        r = requests.post(responseUrl, data=responseBody)
        if r.status_code != 200:
          fail("Request to slack webhook failed. Response: ", r.text)
        return ''

      entry = entry.nextSibling

    fail('Unable to find search phrase in results from Dictionary API.', dom)

  except Exception as e:
    fail('Unexpected exception processing XML. Exception: ' + str(e) + '.', dom)

# Log to cloudwatch and except out of lambda
def fail(err_str, dom = None):
  if dom != None:
    print 'XML: ' + dom.toxml() + '.'

  raise Exception(err_str)

# Process dictionary api entry into json object to be sent to slack
def processEntry(entry):
  dts = entry.getElementsByTagName('dt')
  definitions = [dtToString(dt) for dt in dts]
  attachments = [{'color': '3C0857', 'text': definition} for definition in definitions]
  return json.dumps({'attachments': attachments, 'response_type': 'ephemeral'})

# Sometimes definitions are nested inside other xml objects
def dtToString(dt):
  dt_str = ''

  for node in dt.childNodes:
    while node.nodeType != node.TEXT_NODE:
      node = node.firstChild

    dt_str += node.nodeValue

  return dt_str
