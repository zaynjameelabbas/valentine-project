const noBtn = document.getElementById('noBtn');
const yesBtn = document.getElementById('yesBtn');
const billie = document.getElementById('billie');
const sky = document.getElementById('sky');
const mainText = document.getElementById('mainText');

let scale = 1;

noBtn.addEventListener('mouseover', () => {
    const x = Math.random() * (window.innerWidth - 100);
    const y = Math.random() * (window.innerHeight - 50);
    noBtn.style.left = x + 'px';
    noBtn.style.top = y + 'px';
});

noBtn.addEventListener('click', () => {
    billie.classList.add('sad');
    sky.classList.add('sad');
    mainText.innerText = "Billie and Sky are devastated... 😿";
    scale += 0.5;
    yesBtn.style.transform = `scale(${scale})`;
});

yesBtn.addEventListener('click', () => {
    billie.classList.remove('sad');
    sky.classList.remove('sad');
    billie.classList.add('happy');
    sky.classList.add('happy');
    mainText.innerText = "YAY! The cats are purring! ❤️";
    noBtn.style.display = 'none';
});