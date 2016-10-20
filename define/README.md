# Define Command

Most of the instructions are modified from [this](https://medium.com/@pixelcodeuk/create-a-slack-slash-command-with-aws-lambda-83fb172f9a74#.8mq8z7soq).

This lambda uses the [Dictionary API](http://www.dictionaryapi.com/products/api-collegiate-dictionary.htm)
to return definitions for words or phrases formatted with Slack in mind.
To use this yourself, you need to first get a Dictionary API token and store it somewhere in S3.
Create a slash command custom integration in Slack and store the token in S3 as well.
Then edit the code in `lambda.py` to get `slackToken` and `dictionaryAPIToken` from these locations.

(Note: If this code will only live on lambda for you, then you don't need to obfuscate the tokens through
S3 and can just set `slackToken` and `dictionaryAPIToken` directly.)

To deploy the lambda you will also need to bundle requests, so `cd` into this directory and run
`pip install requests -t .`. Zip up this directory with `zip -r9 define-lambda.zip` and then
put the zip file onto S3. You'll point your lambda to this directory.

## Configuring API Gateway

Make a new API in API Gateway and give it an endpoint `/define` with POST defined.
Enable CORS on this endpoint and give it a lambda integration pointing to the define lambda.
Your body mapping template should have `Content-Type` be `application/x-www-form-urlencoded` with the template
```
## convert HTML POST data or HTTP GET query string to JSON

## get the raw post data from the AWS built-in variable and give it a nicer name
#if ($context.httpMethod == "POST")
 #set($rawAPIData = $input.path('$'))
#elseif ($context.httpMethod == "GET")
 #set($rawAPIData = $input.params().querystring)
 #set($rawAPIData = $rawAPIData.toString())
 #set($rawAPIDataLength = $rawAPIData.length() - 1)
 #set($rawAPIData = $rawAPIData.substring(1, $rawAPIDataLength))
 #set($rawAPIData = $rawAPIData.replace(", ", "&"))
#else
 #set($rawAPIData = "")
#end

## first we get the number of "&" in the string, this tells us if there is more than one key value pair
#set($countAmpersands = $rawAPIData.length() - $rawAPIData.replace("&", "").length())

## if there are no "&" at all then we have only one key value pair.
## we append an ampersand to the string so that we can tokenise it the same way as multiple kv pairs.
## the "empty" kv pair to the right of the ampersand will be ignored anyway.
#if ($countAmpersands == 0)
 #set($rawPostData = $rawAPIData + "&")
#end

## now we tokenise using the ampersand(s)
#set($tokenisedAmpersand = $rawAPIData.split("&"))

## we set up a variable to hold the valid key value pairs
#set($tokenisedEquals = [])

## now we set up a loop to find the valid key value pairs, which must contain only one "="
#foreach( $kvPair in $tokenisedAmpersand )
 #set($countEquals = $kvPair.length() - $kvPair.replace("=", "").length())
 #if ($countEquals == 1)
  #set($kvTokenised = $kvPair.split("="))
  #if ($kvTokenised[0].length() > 0)
   ## we found a valid key value pair. add it to the list.
   #set($devNull = $tokenisedEquals.add($kvPair))
  #end
 #end
#end

## next we set up our loop inside the output structure "{" and "}"
{
#foreach( $kvPair in $tokenisedEquals )
  ## finally we output the JSON for this pair and append a comma if this isn't the last pair
  #set($kvTokenised = $kvPair.split("="))
 "$util.urlDecode($kvTokenised[0])" : #if($kvTokenised[1].length() > 0)"$util.urlDecode($kvTokenised[1])"#{else}""#end#if( $foreach.hasNext ),#end
#end
}
```.
This template was taken from [here](https://medium.com/@pixelcodeuk/create-a-slack-slash-command-with-aws-lambda-83fb172f9a74#.8mq8z7soq).

For the integration response, add the following to the mapping template for `application/json`:
```
{
    "attachments": $input.body,
    "response_type": "in_channel"
}
```

## Configuring the Slack command

On the page for the integration in Slack, give the URL returned by API Gateway.
For example, `https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/define`.
Don't forget to append the name of the endpoint. Also, select to use a POST request to the endpoint.
