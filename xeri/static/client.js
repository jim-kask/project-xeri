const socket = io();

socket.on('connect', () => {
  document.getElementById('status').innerText = "Connected!";
});

socket.on('message', (data) => {
  console.log("Server says:", data);
});
