from flask import Flask, request, g
import requests
import json
import traceback
from watson_developer_cloud import ConversationV1
from models import User
from database import db_session


# conversation = ConversationV1(
#     username="285fe1c1-322d-410a-b32c-45dc96906fcc",
#     password="EpmE7OGT8G7y",
#     version='2017-03-09')
# workspace_id = 'e3225f0f-6c7e-4c29-a126-96b48c5d47a5'


conversation = ConversationV1(
    username= "42e2304b-9085-4f53-9197-780039387fa2",
    password =  "H02Zt3ypKsRC",
    version='2017-03-23'
)
# replace with your own workspace_id
workspace_id = 'e48766eb-ddbf-4146-99b1-daf3c2fccffc'

#Token for facebook page
token = "EAAaeb9Hq0F4BAIA1PERtKvixMlDDfZC6djtZBZC91wer5eS8eWF56yrnGJjLhVRJhbdHLbFIhm9BI7465lugnV0mBeqFfbm2ZAO5GmxIeDuReCFRoC7SXViZCjPZAzjFtcCFmj0wBjNmBWBrRkezWhRj9oZAvsIHigNKiwUyY64zQZDZD"


app = Flask(__name__)

#flask will automatically remove database sessions at the end of the request or when the application shuts down
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

#initializing the context dictionary before the starting of the conversation
@app.before_request
def initialize():
    global context
    global response
    if not response:
        context = {}
    else :
        context = response['context']

#Initializing global variables
context = {}
response = {}
ac_no = ''
mob_no = ''
pin_no = ''
recharge_amount = ''
count = 1

@app.route('/6e230bc1aa85447764019102a51914a23acdad8fea916cdc8f', methods=['GET', 'POST'])
def webhook():

    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            text = data['entry'][0]['messaging'][0]['message']['text']  # Incoming Message Text
            sender = data['entry'][0]['messaging'][0]['sender']['id']  # Sender ID
            global count
            print "count was " + str(count)
            count += 1
            global context
            print "data recieved is : "
            print (json.dumps(data,indent=2))
            print "context used to obtain response was : "
            print (json.dumps(context, indent=2))
            global response

            #do these steps only if request is coming from facebook api
            if data['entry'][0]['messaging'][0]['message'].get('is_echo') is None:
                response = conversation.message(workspace_id=workspace_id, message_input={
                    'text': text}, context=context)  # response by watson api
                print "response is : "
                print (json.dumps(response, indent=2))
                context = response['context']
                print "context is :"
                print context
                process_response(sender)
                try:
                    reply = ""
                    for text in response['output']['text']:
                        reply = reply + text + "\n"
                    print "reply is : \n"
                    print reply
                    payload = {'recipient': {'id': sender}, 'message': {'text': reply}}  # We're going to send this back
                    r = requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token,
                                      json=payload)  # Lets send it
                except Exception as ex:
                    print "exception is :"
                    print ex

        except Exception as e:
            print "Error begins"
            print(traceback.format_exc())  # something went wrong
            print "Error ended"
    elif request.method == 'GET':  # For the initial verification
        if request.args.get(
                'hub.verify_token') == 'EAAaeb9Hq0F4BAIA1PERtKvixMlDDfZC6djtZBZC91wer5eS8eWF56yrnGJjLhVRJhbdHLbFIhm9BI7465lugnV0mBeqFfbm2ZAO5GmxIeDuReCFRoC7SXViZCjPZAzjFtcCFmj0wBjNmBWBrRkezWhRj9oZAvsIHigNKiwUyY64zQZDZD':
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"
    return "Hello World"  # Not Really Necessary


def process_response(sender):
    global ac_no
    global mob_no
    global pin_no
    global context
    global recharge_amount
    global response

    block_name = response['context']['system']['dialog_stack'][0]['dialog_node']
    if block_name == 'Getting account number':
        ac_no = response['output']['account_number']

    if block_name == 'Account Confirmed by User':
        user = User.query.filter(User.ac_no == ac_no).first()
        print user
        if user is None:
            text = "meetpiyushhrushi"
        else:
            text = "account_no_is_verified"
        response = conversation.message(workspace_id=workspace_id, message_input={
                'text': text}, context=context)  # response by watson api

    if block_name == 'Getting Pin' or block_name == 'Getting Pin 2':
        pin_no = response['output']['pin_number']
        print "you entered pin : "
        print pin_no


    if block_name == "Pin Confirmation by User" or block_name == "Pin Confirmed 2":
        user = User.query.filter(User.ac_no == ac_no).first()
        print "pin no in database is : "
        print user.pin_no
        print "pin user entered : "
        print pin_no
        print type(user.pin_no)
        print type(pin_no)
        if str(user.pin_no) == str(pin_no):

            text = "cantor_set_is_amazing "+user.bal
        else:
            text = "every_pda_has_a_cfg"
        response = conversation.message(workspace_id=workspace_id, message_input={
            'text': text}, context=context)  # response by watson api

    if block_name == "Balance Enquiry with account number":
        ac_no = response['output']['accoutn_number']

    if block_name == 'Getting mobile number':
        mob_no = response['output']['mobile_number']

    if block_name == 'Account number for recharge':
        ac_no = response['output']['account_number']

    if block_name == 'Getting Recharge':
        recharge_amount = response['output']['recharge_amount']

    if block_name == 'Recharge Getting Pin':
        pin_no = response['output']['pin_number']

    if block_name == 'Recharge Pin Confirmed':
        user = User.query.filter(User.ac_no == ac_no).first()
        if user is None:
            text = "every_pda_has_a_cfg"
        elif str(user.pin_no) != str(pin_no):
            text = "every_pda_has_a_cfg"
        elif float(user.bal) >= float(recharge_amount):
            #sufficient balance
            x = float(user.bal) - float(recharge_amount)
            user.bal = str(x)
            db_session.commit()
            text = "bellman_ford_is_amazing " + user.bal
        else :
            #insufficien balance
            text = "lebesgue_measure"

        response = conversation.message(workspace_id=workspace_id, message_input={
            'text': text}, context=context)  # response by watson api

    if block_name == "Mobile Recharge with mobile number":
        mob_no = response['output']['mobile_number']





@app.route('/')
def hello_world():
    return "Hello World!"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)

'''
{
    "intents": [],
    "entities": [],
    "context": {
        "conversation_id": "35228ff3-70f6-47c3-8b29-d87a32c84746",
        "system": {
            "dialog_stack": [
                {
                    "dialog_node": "root"
                }
            ],
            "dialog_request_counter": 1,
            "dialog_turn_counter": 1,
            "branch_exited": true,
            "_node_output_map": {
                "Conversation Started": [
                    0,
                    0,
                    1
                ]
            },
            "branch_exited_reason": "completed"
        }
    },
    "input": {
        "text": "Hello World"
    },
    "output": {
        "log_messages": [],
        "nodes_visited": [
            "Conversation Started"
        ],
        "text": [
            "Hi, I am your bank assistant. I am here to help you know your account balance or recharge your mobile phone"
        ]
    # },
    "alternate_intents": false
}
'''
'''
{u'entry': [{u'messaging': [{u'timestamp': 1489977945399L,
                             u'message': {u'text': u'Hi, I am your bank buddy. Happy to help you.', u'is_echo': True,
                                          u'app_id': 1863052960649310L, u'seq': 85984,
                                          u'mid': u'mid.1489977945399:d89e2a2754'},
                             u'recipient': {u'id': u'1091425650969369'}, u'sender': {u'id': u'414026028948269'}}],
             u'id': u'414026028948269', u'time': 1489977945829L}], u'object': u'page'}
'''
'''
# @app.after_request
# def update():
#     global response
#     context = response['context']

#
#
# with app.app_context():
#     print('in app context, before first request context')
#     print('setting g.count to 1')
#     g.count = 1
#     print('g.count should be 1, is: {0}'.format(g.count))
#
# with app.test_request_context():
#     print('in first request context')
#     print('g.count should be None, is: {0}'.format(g.get('count')))
#     print('setting g.count to 2')
#     # g.count = g.count+1
#     print('g.count should be 2, is: {0}'.format(g.count))

# with app.test_request_context():
#     print('in second request context')
#     print('g.count should be None, is: {0}'.format(g.get('count')))
#     print('setting g.count to 5')
#     g.count = 5
#     print('g.count should be 5, is: {0}'.format(g.count))
'''
'''
            # u = User('5575', '46565','7895')
            # db_session.add(u)
            # db_session.commit()
            # u.bal = "6564"
            # db.session.commit()
            print User.query.all()
            p = User.query.filter(User.ac_no == '333').first()
            # p.bal = "65462665"
            print p.bal
            p = User.query.filter(User.ac_no == '5555').first()
            print p.pin_no
'''
