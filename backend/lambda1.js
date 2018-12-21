'use strict';

let AWS = require('aws-sdk');
let sns = new AWS.SNS({
  region: 'us-east-1'
});
let sqs = new AWS.SQS({
  region: 'us-east-1'
});

const pushToOrdersQueue = function(order) {
  return new Promise((resolve, reject) => {
    var params = {
      MessageBody: JSON.stringify(order),
      QueueUrl: process.env.queueUrl
    };
    sqs.sendMessage(params, (err) => err ? reject(err) : resolve());
  });
};

// Close dialog with the customer, reporting fulfillmentState of Failed or Fulfilled ("Thanks, your pizza will arrive in 20 minutes")
function close(sessionAttributes, fulfillmentState, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
        },
    };
}

// --------------- Events -----------------------

function dispatch(intentRequest, callback) {
    const sessionAttributes = intentRequest.sessionAttributes;

    console.log('checkout process start');

    let request = {
        Location: '',
        Cuisine: '',
        NumberOfPeople: '',
        PhoneNumber: '',
        date: '',
        time: ''
    };

    const slots = intentRequest.currentIntent.slots;
    request.Location = slots.Location;
    request.Cuisine = slots.Cuisine;
    request.NumberOfPeople = slots.NumberOfPeople;
    request.PhoneNumber = slots.PhoneNumber;
    request.date = slots.Date;
    request.time = slots.Time;

    pushToOrdersQueue(request)
      .then(() => {

        console.log('responding with status message');

    callback(close(sessionAttributes,
                    'Fulfilled',
                      {'contentType': 'PlainText',
                       'content': 'Okay, Expect my recommendations shortly! Have a good day.'
                      }));

      });

    callback(close(sessionAttributes, 'Fulfilled',
    {'contentType': 'PlainText',
     'content': 'Okay, Expect my recommendations shortly1! Have a good day.'}));

}

// --------------- Main handler -----------------------

// Route the incoming request based on intent.
// The JSON body of the request is provided in the event slot.
exports.handler = (event, context, callback) => {
    try {
        dispatch(event,
            (response) => {
                callback(null, response);
            });
    } catch (err) {
        callback(err);
    }
};
