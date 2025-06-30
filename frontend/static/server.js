require('dotenv').config();
const express = require('express');
const fetch = require('node-fetch');

const app = express();
const port = 3000;

app.use(express.static('.'));
app.use(express.json());

app.use((req, res, next) => {
    res.setHeader('Permissions-Policy', 'geolocation=*');
    next();
});

app.get('/weather', async (req, res) => {
    const { lat, lon } = req.query;
    const apiKey = process.env.WEATHER_API_KEY;
    const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Weather API error:', error);
        res.status(500).json({ error: 'Failed to fetch weather data' });
    }
});

app.post('/generate-scenery', async (req, res) => {
    const { weatherCondition, city } = req.body;

    if (!weatherCondition || !city) {
        return res.status(400).json({ error: 'Weather condition and city are required.' });
    }

    const prompt = `A photorealistic, serene view from an airplane window of ${city} under ${weatherCondition.toLowerCase()} weather. High detail, 4k.`;
    const aihubmixApiKey = process.env.AIHUBMIX_API_KEY;
    const aihubmixUrl = 'https://aihubmix.com/v1/images/generations';

    try {
        const response = await fetch(aihubmixUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${aihubmixApiKey}`
            },
            body: JSON.stringify({
                model: "dall-e-3",
                prompt: prompt,
                n: 1,
                size: "1024x1024",
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('AIHubMix API Error:', errorData);
            return res.status(response.status).json({ error: 'Failed to generate scenery from AIHubMix', details: errorData });
        }

        const data = await response.json();
        const imageUrl = data.data[0].url;
        res.json({ imageUrl });

    } catch (error) {
        console.error('Error calling AIHubMix:', error.message);
        res.status(500).json({ error: 'Failed to generate scenery image.', details: error.message });
    }
});

app.listen(port, () => {
    console.log(`Dynamic Weather Window server listening at http://localhost:${port}`);
});
