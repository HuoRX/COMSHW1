'use strict';

// import the NLU library
const nlu = require('./nlu.js');

//newly added
var AWS = require('aws-sdk');


exports.handler = (event, context, callback) => {

  AWS.config.update({region: 'us-east-1'});
  var lexruntime = new AWS.LexRuntime();
  let messages = null;

  try {
    if ('messages' in event && event.messages.length > 0) {
      messages = event.messages;
    } else {
      throw new Error('bad request: missing messages key');
    }

    let responses = [];

    for (const message of messages) {
      // TODO: implement the capability to respond
      // to structured messages (ex. button presses)
      if (message.type === 'structured') {
        console.log('unhandled');
      } else if (message.type === 'unstructured') {
        let retVal = message.unstructured.text;
        responses = responses.concat(retVal);
      }
    }

    messages = responses[0];
    console.log(messages);

    var lexUserId = 'chatbot-demo';
    var sessionAttributes = {"id":"test"};

    var params = {
					botAlias: '$LATEST',
					botName: 'SearchRestaurants',
					inputText: messages,
					userId: lexUserId,
					sessionAttributes: sessionAttributes
				};

    //let responseMessages = '';
		lexruntime.postText(params, function(err, data) {
					if (err) {
						console.log(err, err.stack);
					}
					if (data) {
						// capture the sessionAttributes for the next cycle
						var responseMessages = data.message;
						sessionAttributes = data.sessionAttributes;
						console.log("inside loop: "+responseMessages);
						responseMessages = {
              type: 'unstructured',
              unstructured: {
              text: responseMessages,
              timestamp: new Date().toISOString()
              }
            }
						callback(null, {
              messages: [responseMessages]
              });
					}
				});
    //responseMessages = responseMessages.message;
    // console.log('responding with messages', responseMessages);

    // callback(null, {
    //   messages: responseMessages
    // });
  } catch (error) {
    console.log(error);
    callback(error);
  }
};
