var ws = new WebSocket('ws://localhost:8000/ws');
var username = 'Abhinav'
var id = ''

window.onload=function()
{
  username = prompt("Username: ")
}
ws.onopen = function (event) {
  console.log(`Authenticating as ${username}`)
  ws.send(JSON.stringify({ username: username }));
  
}
// ws event logic
ws.onmessage = function (event) {
  data = JSON.parse(event.data);
  if (data.hasOwnProperty('id')) {
    id = data.id
    console.log(`ID: ${id}`)
  }
  if (data.hasOwnProperty('message')) {
    addNewMessage(data);
  }
};

addNewMessage = (data) => {
  message = data.message;
  username = data.username;

  var messageTemplate = document.getElementsByClassName("card")[0];
  var newChat = messageTemplate.cloneNode(true);

  newChat.classList.remove("visually-hidden");

  var chatWindow = document.getElementsByClassName("container")[0];

  // set username
  newChat.querySelector("div.card-header > span").innerText = `    ${username}`;
  // set message content
  newChat.querySelector("div.card-body > blockquote > p").innerText = message;
  // set timestamp
  newChat.querySelector("div.card-body > blockquote > footer").innerText =
    getTimestamp();
  // append new message to list
  chatWindow.append(newChat);
};

// timestamp generator
getTimestamp = () => {
  var now = new moment();
  return now.format("HH:mm:ss");
};

function sendMessage() {
  // get message text
  let message = document.getElementsByClassName("message-input")[0].value;
  if (message != "") {
    // send to websocket
    ws.send(JSON.stringify({ message: message, username: username }));
  }
}

