
from slackclient import SlackClient
import sys
import urllib2
import json


def API_slack(request,slack_token):

    sc = SlackClient(slack_token)

    return sc.api_call(
      "chat.postMessage",
        channel="#bot_testing",
      text=request
    )


TIMEOUT = 7
def API(request,auth,url):

    stringified = json.dumps(request)
    headers = {'content-type': 'application/json', 'Authorization': auth}

    try:
        request = urllib2.Request(url=url, data=stringified, headers=headers)
        returnData = urllib2.urlopen(request,timeout=TIMEOUT).read()
    except:
        print url, "Timeout!"
        print '\n    ' + repr(sys.exc_info())
        return

    response = json.loads(returnData)
    return response

