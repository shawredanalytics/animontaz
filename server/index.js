const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');
const generateRoute = require('./routes/generate');

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Routes
app.use('/api/generate', generateRoute);

app.get('/', (req, res) => {
  res.send('Animontaz API is running');
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
