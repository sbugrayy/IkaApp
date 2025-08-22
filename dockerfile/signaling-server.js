const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

let dataStore = {
  offer: null,
  answer: null,
  candidates: []
};

app.post('/data', (req, res) => {
  const data = req.body;

  if(data.type === 'offer') {
    console.log("Offer geldi");
    dataStore.offer = data;
    dataStore.answer = null;
    dataStore.candidates = [];
  } else if(data.type === 'answer') {
    console.log("Answer geldi");
    dataStore.answer = data;
  } else if(data.candidate) {
    console.log("Candidate geldi");
    dataStore.candidates.push(data);
  }
  res.sendStatus(200);
});

app.get('/data', (req, res) => {
  res.json(dataStore);
});

app.listen(port, () => {
  console.log(`Signaling server çalışıyor: http://localhost:${port}`);
});