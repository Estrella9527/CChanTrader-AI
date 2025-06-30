let scene, camera, renderer, points, controls, composer;
let currentVibe = 'calm';

const vibes = {
    calm: {
        color1: new THREE.Color(0x4a86e8), // Soothing Blue
        color2: new THREE.Color(0x9fc5e8), // Light Sky Blue
        shape: 'sphere',
        density: 80000
    },
    joy: {
        color1: new THREE.Color(0xffd966), // Sunny Yellow
        color2: new THREE.Color(0xfcc2d9), // Soft Pink
        shape: 'random',
        density: 120000
    },
    focus: {
        color1: new THREE.Color(0xffffff), // White
        color2: new THREE.Color(0xcccccc), // Light Grey
        shape: 'cube',
        density: 60000
    }
};

function init() {
    // Scene and Renderer
    scene = new THREE.Scene();
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    document.body.appendChild(renderer.domElement);

    // Camera
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 15;

    // Controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;

    // Placeholder Point Cloud
    createPlaceholderPointCloud();

    // Post-processing for Bloom Effect
    const renderScene = new THREE.RenderPass(scene, camera);
    const bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.threshold = 0;
    bloomPass.strength = 0.6;
    bloomPass.radius = 0.5;

    composer = new THREE.EffectComposer(renderer);
    composer.addPass(renderScene);
    composer.addPass(bloomPass);

    // Event Listeners
    document.getElementById('calm').addEventListener('click', () => setVibe('calm'));
    document.getElementById('joy').addEventListener('click', () => setVibe('joy'));
    document.getElementById('focus').addEventListener('click', () => setVibe('focus'));
    window.addEventListener('resize', onWindowResize, false);

    animate();
}

function createPlaceholderPointCloud() {
    const vibe = vibes[currentVibe];
    const geometry = new THREE.BufferGeometry();
    const positions = [];
    const colors = [];

    const size = 10;

    for (let i = 0; i < vibe.density; i++) {
        let x, y, z;

        if (vibe.shape === 'sphere') {
            const phi = Math.acos(-1 + (2 * i) / vibe.density);
            const theta = Math.sqrt(vibe.density * Math.PI) * phi;
            x = size * Math.cos(theta) * Math.sin(phi);
            y = size * Math.sin(theta) * Math.sin(phi);
            z = size * Math.cos(phi);
        } else if (vibe.shape === 'cube') {
            x = Math.random() * size - size / 2;
            y = Math.random() * size - size / 2;
            z = Math.random() * size - size / 2;
        } else { // random
            x = (Math.random() - 0.5) * size * 2;
            y = (Math.random() - 0.5) * size * 2;
            z = (Math.random() - 0.5) * size * 2;
        }
        positions.push(x, y, z);

        const color = new THREE.Color();
        color.lerpColors(vibe.color1, vibe.color2, Math.random());
        colors.push(color.r, color.g, color.b);
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({ 
        size: 0.05, 
        vertexColors: true, 
        transparent: true, 
        opacity: 0.8, 
        depthWrite: false 
    });

    if (points) {
        scene.remove(points);
    }

    points = new THREE.Points(geometry, material);
    scene.add(points);
}

function setVibe(vibe) {
    currentVibe = vibe;
    controls.autoRotate = (vibe !== 'focus');
    createPlaceholderPointCloud();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    composer.render();
}

init();