from flask import Flask, request, g
import requests
import json
import traceback
from watson_developer_cloud import ConversationV1
from models import User
from database import db_session


conversation = ConversationV1(
    username= "42e2304b-9085-4f53-9197-780039387fa2",
    password =  "H02Zt3ypKsRC",
    version='2017-03-23'
)
# replace with your own workspace_id
workspace_id = 'e48766eb-ddbf-4146-99b1-daf3c2fccffc'

#Token for facebook page
token = "EAAShV6MKQB0BAFOu8cgjkFqLfOr0VSlHu9f1asDr7GPhUMOaMqyyldfgDYIIQkIeGeqyVvZBVVLNhUZCC0qbapFhk3AGJkjujqZCgaChbaJiBYW1GNZBLyOTpZB3trDqP9Tbfzt8jFishjDd1N8g095Jamlu0ZA4hbwaaN0tjMet9iCMkv4nkQ"


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
            # print "count was " + str(count)
            count += 1
            global context
            # print "data recieved is : "
            # print (json.dumps(data,indent=2))
            # print "context used to obtain response was : "
            # print (json.dumps(context, indent=2))
            global response

            #do these steps only if request is coming from facebook api
            if data['entry'][0]['messaging'][0]['message'].get('is_echo') is None:
                response = conversation.message(workspace_id=workspace_id, message_input={
                    'text': text}, context=context)  # response by watson api
                # print "response is : "
                # print (json.dumps(response, indent=2))
                context = response['context']
                # print "context is :"
                # print context
                process_response(sender)
                try:
                    reply = ""
                    for text in response['output']['text']:
                        reply = reply + text + "\n"
                    # print "reply is : \n"
                    # print reply
                    payload = {'recipient': {'id': sender}, 'message': {'text': reply}}  # We're going to send this back
                    r = requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token,
                                      json=payload)  # Lets send it
                except Exception as ex:
                    print ("exception is :")
                    print (ex)


        except Exception as e:
            print ("Error begins")
            print(traceback.format_exc())  # something went wrong
            print ("Error ended")
    elif request.method == 'GET':  # For the initial verification
        if request.args.get(
                'hub.verify_token') ==  "federal_bank_chatbot":
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
        # print user
        if user is None:
            text = "meetpiyushhrushi"
        else:
            text = "account_no_is_verified"
        response = conversation.message(workspace_id=workspace_id, message_input={
                'text': text}, context=context)  # response by watson api

    if block_name == 'Getting Pin' or block_name == 'Getting Pin 2':
        pin_no = response['output']['pin_number']
        # print "you entered pin : "
        # print pin_no


    if block_name == "Pin Confirmation by User" or block_name == "Pin Confirmed 2":
        user = User.query.filter(User.ac_no == ac_no).first()
        # print "pin no in database is : "
        # print user.pin_no
        # print "pin user entered : "
        # print pin_no
        # print type(user.pin_no)
        # print type(pin_no)
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


